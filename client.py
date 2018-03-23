from twisted.internet.protocol import Protocol, ReconnectingClientFactory
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor

class Message(Protocol):

    def __init__(self):
        self.config = {}
        self.config['feed_running'] = False
        self.config['frame_rate'] = 5.0 # hz

        self.state = {}
        self.state['expecting_frame'] = False
        self.state['frame_start'] = False

        self.data = {}
        self.data['img'] = None
        self.data['img_size'] = None

        self.msg = {}
        self.msg['buffer'] = ''
        self.msg['count'] = 0
        self.msg['type'] = None
        self.msg['header_offset'] = 0
        self.msg['ptr'] = -1

    def connectionMade(self):
        self.start_stream()

    def start_stream(self):
        self.config['feed_running'] = True
        self.get_frame()

    def get_frame(self):
        self.transport.write('get_frame')
        self.state['expecting_frame'] = True

        if self.config['feed_running']:
            rate = self.config['frame_rate']
            reactor.callLater(1.0/rate, self.get_frame)

    def dataReceived(self, data):
        if self.state['expecting_frame']:
            if self.state['frame_start'] == False:
                self.msg['buffer'] = ''

                self.msg['buffer'] = data
                self.msg['count']  = len(data)

                # do some processing
                msg = self.msg['buffer']
                msg = msg.split(';')
                self.msg['type'] = msg[0]
                self.data['img_size'] = eval(msg[1])
                self.msg['header_offset'] = (2 
                    + len(self.msg['type']) 
                    + len(msg[1])
                )

                # set start frame flag
                self.state['frame_start'] = True

            # frame already started
            else:
                # update msg buffer
                self.msg['buffer'] += data
                self.msg['count'] += len(data)

                # 

                if self.msg['count'] >= (self.data['img_size'] + self.msg['header_offset'] - 4): #4=fudge value
                    self.state['expecting_frame'] = False
                    self.state['frame_start'] = False
                    #print('collected %d byte packet.' % (self.msg['count']))
                
                    a = self.msg['header_offset']
                    self.data['img'] = self.msg['buffer'][a:-1]
                
        else:
            print('Received data (%d bytes), but not sure what to do with it! (%s)' % (len(data), data[0:12]))

class MessageFactory(ReconnectingClientFactory):

    def startedConnecting(self, connector):
        print('Started to connect')
        #protocol.connectionMade()

    def buildProtocol(self, addr):
        return Message()

    def clientConnectionLost(self, connector, reason):
        print('Lost connection. Reason:', reason)
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        pass

reactor.connectTCP('10.0.0.56', 5000, MessageFactory())
reactor.run()