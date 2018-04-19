import os
import struct
import numpy as np
import time

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

MASTER_FPS = 3.0
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
        self.transport.write(b'get_frame')
        self.state['expecting_frame'] = True

        if self.config['feed_running']:
            rate = self.config['frame_rate']
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
                with open('./static/no-img.jpg', 'rb') as f:
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
        cv2.imshow('frame', img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            exit(0)

    def dataReceived(self, data):
        if self.state['expecting_frame']:
            success = self.async_read_packet(data)

            if success:
                # vvvvv
                #TODO: self.writeToImgFile()
                if (self.data['status'] == 'done') or (self.data['status'] == 'no-image'):
                    jpg = self.data['img']
                    with open('.img.jpg', 'wb') as fp:
                        fp.write(jpg)

                    print("wrote %.2fkB file" % (len(jpg)/1000.0))
                    os.system('mv .img.jpg img.jpg')

                    # ^^^^^^^

                    img = bytes2cv(jpg)
                    #self.showFrame(img)
                    check_frame_rate()
                else:
                    pass

        else:
            print("received inappropiate packet")

class MessageFactory(ReconnectingClientFactory):

    def startedConnecting(self, connector):
        print('Started to connect')
        ReconnectingClientFactory.resetDelay(self)
        #protocol.connectionMade()

    def buildProtocol(self, addr):
        return Message()

    def clientConnectionLost(self, connector, reason):
        print('Lost connection. Reason:', reason)
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        pass

reactor.connectTCP(IP_ADDRESS, 5000, MessageFactory())
reactor.run()