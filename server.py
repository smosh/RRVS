import sys


from twisted.internet.protocol import Factory, Protocol
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor

sys.path.append('./include')
from camera_bbb import BBBCam

cam = BBBCam()

DEBUG_PRINT = False

def packData(*args):
    '''
    Takes a set of arguments, and concatenates them in a string that '''
    # join the arg strings
    output_str = b';'.join(args)
    return output_str

class Receiver(Protocol):
    frame_num = -1
    def dataReceived(self, data):
        if 'get_frame' in data:
            # build the packet components
            code            = b'img'
            jpg             = cam.get_frame()
            self.frame_num += 1
            count           = bytes(str(len(jpg)))
            
            # write out u
            packet = packData(code, count, str(self.frame_num), jpg)
            self.transport.write(packet)

            if DEBUG_PRINT:
                # print out other data
                print("sent a %s byte img" % count)


class VideoServerFactory(Factory):
    protocol = Receiver

    def __init__(self):
        pass

# Connect to the IP Address
endpoint = TCP4ServerEndpoint(reactor, 5000)
endpoint.listen(VideoServerFactory())

# run the server
reactor.run()