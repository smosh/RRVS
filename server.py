import sys


from twisted.internet.protocol import Factory, Protocol
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor

sys.path.append('./include')
from cam_manager import CamManager

cam = CamManager()

DEBUG_PRINT = False

def packData(*args):
    '''
    Takes a set of arguments, and concatenates them in a string that '''
    # join the arg strings
    output_str = b';'.join(args)
    return output_str
def get_num_cams():
    return 1

class Receiver(Protocol):
    frame_num = -1
    def dataReceived(self, data):
        if 'get_frame' in data:
            # build the packet components
            code            = b'img'
            jpg             = cam.get_frame('primary')
            self.frame_num += 1
            count           = bytes(str(len(jpg)))
            
            # write out u
            packet = packData(code, count, str(self.frame_num), jpg)
            self.transport.write(packet)

            if DEBUG_PRINT:
                # print out other data
                print("sent a %s byte img" % count)

        if 'get_cam_stat' in data:
            # build the packet component
            code = b'status'
            status_type = b'cams_online'
            n_cams = bytes(str(get_num_cams()))

            cam_struct = collections.OrderedDict()
            cam_struct['online'] = 0
            cam_struct['fps']    = 30
            cam_struct['width']  = 540
            cam_struct['hight']  = 260

            fmt = '?hii' #TODO:move this definition to some include file

            struct.pack(fmt, *cam_struct.items())



class VideoServerFactory(Factory):
    protocol = Receiver
    auto_refresh = True

    def __init__(self):
        self.refresh()
    
    def refresh(self):
        cam.refresh_feeds()

        if self.auto_refresh:
            reactor.callLater(1.0, self.refresh)


# Connect to the IP Address
endpoint = TCP4ServerEndpoint(reactor, 5000)
endpoint.listen(VideoServerFactory())

# run the server
reactor.run()