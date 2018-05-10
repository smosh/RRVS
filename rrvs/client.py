from builtins import super, bytes

import os
import struct
import numpy as np
import time
import sys

ROOT_DIR = os.path.join(os.path.dirname(__file__), './')

from twisted.internet.protocol import Protocol, ReconnectingClientFactory
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor

import cv2

#IP_ADDRESS = '10.0.0.56'
IP_ADDRESS = 'localhost'

def convertBytesToHexStr(data):
    import pdb; pdb.set_trace()
    return ''.join([hex(ord(i)) for i in data])

def bytes2cv(buf):
    img = struct.unpack('B'*len(buf), buf)
    img = np.array(img, np.uint8)
    img = cv2.imdecode(img, cv2.IMREAD_UNCHANGED)

    return img

MASTER_FPS = 15.0
FRAME_CLK = time.time()

def check_frame_rate():
    global FRAME_CLK
    delta_time = time.time() - FRAME_CLK 
    fps = 1 / delta_time
    print("client.py: fps = %04.1fHz (%05.1f%% efficiency)" % (fps, fps / MASTER_FPS * 100))
    FRAME_CLK = time.time()
    return 

class Message(Protocol):

    def __init__(self):
        #super().__init__()
        self.config = {}
        self.config['feed_running'] = False
        self.config['frame_rate'] = MASTER_FPS # hz

        self.state = {}
        self.state['expecting_frame'] = False
        self.state['frame_start'] = False

        self.data = {}
        self.data['img'] = None
        self.data['img_size'] = None
        self.data['status'] = None

        self.msg = {}
        self.msg['buffer'] = ''
        self.msg['count'] = 0
        self.msg['type'] = None
        self.msg['header_offset'] = 0
        self.msg['read_busy'] = False
        self.msg['bus_idle'] = True
        self.msg['complete'] = False


    def connectionMade(self):
        self.start_stream()

    def start_stream(self):
        self.config['feed_running'] = True
        self.get_frame()

    def get_frame(self):
        stream_name = self.factory.stream_name.encode('utf-8')
        self.transport.write(b'get_frame;%s' % (stream_name))
        self.state['expecting_frame'] = True

        if self.config['feed_running']:
            rate = self.factory.frame_rate
            reactor.callLater(1.0/rate, self.get_frame)

    def async_msg_parser(self):
        # process image frames
        print('----')
        if self.msg['type'] == b'img':
            nargs = 4
            # self.process_frame
            msg_args = self.msg['buffer'].split(b';',nargs - 1)
            if len(msg_args) < (nargs):
                self.data['status'] = 'not-done'
                return 'not-done'
                
            self.data['img_size']     = eval(msg_args[1])
            self.msg['header_offset'] = len(msg_args[0] + b';' + msg_args[1] + b';' +  msg_args[2] + b';') #TODO: write arg parser
            goal_count                = self.data['img_size'] + self.msg['header_offset']

            if self.data['img_size'] == 0:
                self.data['status'] = 'no-image'

                # read the image anyway
                jpg = b''
                fp = os.path.join(ROOT_DIR, 'static/no-img.jpg')
                with open(fp, 'rb') as f:
                    for line in f:
                        jpg += line

                self.data['img'] = jpg
                return 'no-image'

            if len(self.msg['buffer']) >= goal_count:
                self.data['img'] = msg_args[3]
                self.data['status'] = 'done'
                return 'done'

        else:
            print("unrec datatype")
            self.data['status'] = 'fail'
            return 'fail'



    def async_read_packet(self, data):
        new_packet = self.msg['bus_idle'] == True

        # --- Initialize packet if new
        if new_packet:
            self.msg['buffer'] = data
            self.msg['count'] = len(data)
            self.msg['bus_idle'] = False # self.set_bus_active()
            self.msg['read_busy'] = True # self.set_bus_active()

            # self.init_msg
            self.msg['type'] = None

        else:
            self.msg['buffer'] += data
            self.msg['count'] += len(data)

        # -----
        
        # --- parse args if possible
        if self.msg['type'] is None:
            msg_args = self.msg['buffer'].split(b';')
            if len(msg_args) > 1:
                self.msg['type'] = msg_args[0]
        else:
            pass


        # at this point, there is enough information to run the message parser  
        msg_status = self.async_msg_parser()
     
        if msg_status == 'done':
            self.msg['bus_idle'] = True #self.releasebus()
            return True # sucess!
            
        elif msg_status == 'not-done':
            return False # not done yet

        elif msg_status == 'no-image':
            self.msg['bus_idle'] = True #self.releasebus()
            return True # not done yet

        elif msg_status == 'fail':
            print('client.py: failure')
            self.msg['bus_idle'] = True #self.releasebus()
            return True
            

    def showFrame(self, img):
        stream_name = self.factory.stream_name
        cv2.imshow(stream_name, img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            self.transport.loseConnection()
            reactor.stop()

    def dataReceived(self, data):
        if self.state['expecting_frame']:
            success = self.async_read_packet(data)

            if success:
                # vvvvv
                #TODO: self.writeToImgFile()
                if (self.data['status'] == 'done') or (self.data['status'] == 'no-image'):
                    jpg = self.data['img']

                    # ^^^^^^^

                    img = bytes2cv(jpg)
                    self.showFrame(img)
                    check_frame_rate()
                else:
                    pass

        else:
            print("received inappropiate packet")

class MessageFactory(ReconnectingClientFactory):

    def __init__(self, stream_name=None):
        #super().__init__() 
        self.stream_name = stream_name
        self.frame_rate = 15.0 #frames per second

        self.enable = {}
        self.enable['gui'] = False

    def attach_stream(self, stream_name):
        self.stream_name = stream_name

    def enable_gui(self, value):
        self.enable['gui'] = value

    def startedConnecting(self, connector):
        print('Started to connect')
        ReconnectingClientFactory.resetDelay(self)
        #protocol.connectionMade()

    def buildProtocol(self, addr):
        p = Message()
        p.factory = self
        return p

    def clientConnectionLost(self, connector, reason):
        print('Lost connection. Reason:', reason)
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        pass

class Client(object):
    def __init__(self):
        self.enable = {}
        self.enable['gui'] = False

        self.ip = None
        self.stream_name = None
        self.port = 5000

        self.factory = MessageFactory()

    def attach_IP(self, ip_address):
        self.ip = ip_address

    def attach_stream(self, stream_name):
        self.stream_name = stream_name
        self.factory.attach_stream(stream_name)

    def enable_gui(self, value):
        self.enable['gui'] = value
        self.factory.enable_gui(value)

    def run(self):
        reactor.connectTCP(self.ip, self.port, self.factory)
        reactor.run()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('usage:\n\tclient.py <ip> <stream_name>')
        exit()
    ip = sys.argv[1]
    stream_name = sys.argv[2]



    client = Client()
    client.attach_IP(ip)
    client.attach_stream(stream_name)
    client.enable_gui(True)
    client.run()
