import sys


from twisted.internet.protocol import Factory, Protocol
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor

sys.path.append('./include')
from camera_bbb import BBBCam

cam = BBBCam()

class Receiver(Protocol):
    frame_num = -1
    def dataReceived(self, data):
        if 'get_frame' in data:
            jpg = cam.get_frame()
            self.frame_num += 1
            code = b'img'
            count = bytes(str(len(jpg)))
            
            # write out u
            self.transport.write(b';'.join([code,
                                            count,
                                            str(frame_num),
                                            jpg]))
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