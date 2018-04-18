import sys

from twisted.internet.protocol import Factory, Protocol
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor

sys.path.append('./include')
from cam_manager2 import CamManager

DEBUG_PRINT = True

class Server(object):
    def __init__(self):
        self.factory = VideoServerFactory()


    def connect(self):
        # Connect to the IP Address
        endpoint = TCP4ServerEndpoint(reactor, 5000)
        endpoint.listen(self.factory)

        # run the server
        reactor.run()

class Receiver(Protocol):
    def __init__(self):
        super().__init__()

        # initialize parameters
        self.frame_num = -1

    def dataReceived(self, data):
        if b'get_frame' in data:
            # build the packet components
            code            = b'img'
            jpg             = self.factory.video.get_frame('primary')
            self.frame_num += 1
            frame_num       = bytes(str(self.frame_num), 'utf-8')
            count           = bytes(str(len(jpg)), 'utf-8')
            
            # write out u
            packet = self.packData(code, count, frame_num, jpg)
            self.transport.write(packet)

            if DEBUG_PRINT:
                # print out other data
                print("server.py: sent a %s byte img" % count.decode('utf-8'))

    def connectionMade(self):
        print("server.py: connected to ip")

    def packData(self, *args):
        '''
        Takes a set of arguments, and concatenates them in a string that '''
        # join the arg strings
        output_str = b';'.join(args)
        return output_str

class VideoServerFactory(Factory):
    protocol = Receiver
    def __init__(self):
        # connect to video capture library
        self.video = CamManager()

        # settings for the server factory
        self.settings = {}
        self.settings['auto-refresh'] = True
        self.settings['refresh-rate'] = 1.0 #seconds

        # kick off the refresh engine
        self.refresh()

    def refresh(self):
        # send command to video module for refreshing feeds
        self.video.refresh_feeds()

        if self.settings['auto-refresh']:
            rt = 1.0/self.settings['refresh-rate']
            reactor.callLater(rt, self.refresh)
        

def main():
    server = Server()
    server.connect()

if __name__ == '__main__':
    main()