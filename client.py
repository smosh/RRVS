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
        self.msg['read_busy'] = False
        self.msg['bus_idle'] = True
        self.msg['complete'] = False

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

    def async_msg_parser(self):
        # process image frames
        if self.msg['type'] == 'img':
            # self.process_frame
            msg_args = self.msg['buffer'].split(';')
            if len(msg_args) < 3:
                return None
                
            self.data['img_size'] = eval(msg_args[1])

            self.msg['header_offset'] = len(msg_args[0] + ';' + msg_args[1] + ';')

            goal_count = self['img_size'] + self.msg['header_offset']

            if len(self.msg['buffer']) >= goal_count:
                self.data['img'] = msg_args[2]
                return True

        else:
            print("unrec datatype")
            return False

xx

    def async_read_packet(self, data):
        new_packet = self.msg['bus_idle'] == True
        msg_type_known = self.

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
        
        if self.msg['type'] is None:
            msg_args = self.msg['buffer'].split(';')
            if len(msg_args) > 1:
                self.msg['type'] = msg_args[0]
        else:
            return None

        # at this point, there is enough information to run the message parser  
        self.async_msg_parser()


     
        if msg_done:
            return True # sucess!
            
        else:
            return False # not down yet
            = self.async_msg_parser()
            

        

    def dataReceived(self, data):
        if self.state['expecting_frame']:
            self.async_read_packet(data)

        else:
            print("received inappropiate packet")


            if self.state['frame_start'] == False:



                self.msg['buffer'] = data
                self.msg['count']  = len(data)

                # determine type of message
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