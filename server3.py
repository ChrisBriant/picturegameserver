import sys, redis, uuid,json,ast, threading

from twisted.internet import reactor, ssl
from twisted.web.server import Site
from twisted.web.static import File
from twisted.python import log
from autobahn.twisted.websocket import WebSocketServerFactory, WebSocketServerProtocol, listenWS
from autobahn.twisted.resource import WebSocketResource
from resettimer import TimerReset

#The timeout value in seconds to keep a room active
ROOM_TIMEOUT_VALUE = 120

## TODO:  Add controls for when a message is sent to a room not in existance

# TUTORIAL https://medium.com/python-in-plain-english/identify-websocket-clients-with-autobahn-twisted-and-python-3f90b4c135d4

# Source: https://stackoverflow.com/questions/29951718/autobahn-sending-user-specific-and-broadcast-messages-from-external-application
class BroadcastServerProtocol(WebSocketServerProtocol):
    def onOpen(self):
        self.factory.register(self)

    def onConnect(self, request):
        print("Client connecting: {}".format(request.peer))

    def onMessage(self, payload, isBinary):
        if not isBinary:
            received_data = ast.literal_eval(payload.decode("utf-8"))
            print("msg",received_data)
            if (received_data['type'] == 'broadcast'):
                #Broadcast message
                send_payload = {
                    'type': 'message',
                    'message': received_data['message']
                }
                self.factory.broadcast(json.dumps(send_payload))
            elif received_data['type'] == 'client':
                #Currently not used
                send_payload = {
                    'type': 'message',
                    'message': 'Cheese'
                }
                self.factory.send_client(received_data['client_id'],json.dumps(send_payload))
            elif received_data['type'] == 'room_pm':
                print('RECEIVED DATA', received_data)
                message = received_data['message'].split(':')[1]
                send_payload = {
                    'type': 'in_room_pm',
                    'message': message,
                    'sender' : received_data['sender']
                }
                self.factory.send_client(received_data['client_id'],json.dumps(send_payload))
            elif received_data['type'] == 'create_room':
                room_list = self.factory.create_room(received_data['client_id'],received_data['name'])
            elif received_data['type'] == 'name':
                self.factory.set_name(received_data['client_id'],received_data['name'])
                send_payload = {
                    'type': 'set_name',
                    'message': received_data['name']
                }
                self.factory.send_client(received_data['client_id'],json.dumps(send_payload))
                #Broadcast client list now a name is set
                self.factory.send_client_list()
                #Broadcast room list
                self.factory.send_room_list()
            elif received_data['type'] == 'enter_room':
                self.factory.enter_room(received_data['client_id'],received_data['name'])
            elif received_data['type'] == 'exit_room':
                self.factory.exit_room(received_data['client_id'],received_data['name'])
            elif received_data['type'] == 'message_room':
                #Update timer
                if received_data['name'] in self.factory.rooms.keys():
                    self.factory.timers[received_data['name']]['timer'].reset()
                    send_payload = {
                        'type' : 'room_message',
                        'client': { 'id':received_data['client_id'] , 'name':self.factory.clients[received_data['client_id']]['name']},
                        'message':  received_data['message']
                    }
                    room = self.factory.rooms[received_data['name']]
                    self.factory.send_room(room,send_payload)



    def connectionLost(self, reason):
        print("Connection Lost", reason)
        #WebSocketServerProtocol.connectionLost(self, reason)
        self.factory.unregister(self)


class BroadcastServerFactory(WebSocketServerFactory):
    def __init__(self, url):
        WebSocketServerFactory.__init__(self, url)
        self.clients = {}
        self.rooms = {}
        self.timers = {}

    def register(self, client):
        registered = [self.clients[i] for i in list(self.clients.keys())]
        ids = list(self.clients.keys())
        if client not in registered:
            while (cid := str(uuid.uuid4())) in ids:
                pass
            print("registered client {} with id {}".format(client.peer, cid))
            self.clients[cid] = dict()
            self.clients[cid]['client'] = client
            self.clients[cid]['name'] = None
            self.clients[cid]['room'] = None
            payload = {
                'type': 'register',
                'yourid':cid
            }
            client.sendMessage(json.dumps(payload).encode())

    def send_client_list(self):
        #Get the clients and create
        clients_list = list(self.clients.keys())
        print('client list here',clients_list)
        clients_data = [{'id':cli, 'name':self.clients[cli]['name']} for cli in clients_list]
        payload = {
            'type' : 'client_list',
            'clients': json.dumps(clients_data)
        }
        print('The Clients',self.clients)
        for cid in self.clients:
            print(cid)
            try:
                self.clients[cid]['client'].sendMessage(json.dumps(payload).encode())
            except Exception as e:
                print(e)

    #The connection is closed tidy up
    def unregister(self, client):
        client_id = None
        all_clients = list(self.clients)
        for cli in all_clients:
            if client == self.clients[cli]['client']:
                client_id = cli
                #Notify room
                self.exit_room(client_id,self.clients[client_id]['room'])
                del self.clients[cli]

        #For now (for testing purposes destroy all the rooms)
        #Timer will be used to closed rooms when implemented
        #!!!!!!!!!!!!!!!! IMPORTANT BELOW MUST BE REMOVED IN PRODUCTION FOR IT TO WORK !!!!!!!!!!!!!!!# 
        self.rooms = {}


    def broadcast(self, msg):
        print("broadcasting message '{}' to {} clients ...".format(msg, len(self.clients)))
        cids = self.clients.keys()
        for cid in cids:
            print('here is a client', self.clients[cid])
            self.clients[cid]['client'].sendMessage(msg.encode('utf-8'))

    def send_client(self,client_id,data):
        print('sending to ',client_id)
        self.clients[client_id]['client'].sendMessage(data.encode('utf-8'))

    def set_name(self,client_id,name):
        print('set name',self.clients)
        self.clients[client_id]['name'] = name

    def create_room(self,client_id,room):
        rooms = self.rooms.keys()
        if room not in rooms:
            self.rooms[room] = dict()
            self.rooms[room]['owner'] = client_id
            self.rooms[room]['name'] = room
            self.rooms[room]['members'] = []
            self.timers[room] = dict()
            self.timers[room]['timer'] = TimerReset(ROOM_TIMEOUT_VALUE,self.close_room,args=[room])
            self.timers[room]['timer'].start()
            self.send_room_list()
        else:
            #Send a failure notification
            send_payload = {
                'type' : 'room_failure',
                'reason': 'Room already exists'
            }
            self.clients[client_id]['client'].sendMessage(json.dumps(send_payload).encode('utf-8'))

    def send_room_list(self):
            room_list = [ self.rooms[k] for k in self.rooms.keys()]
            send_payload = {
                'type' : 'room_list',
                'rooms': json.dumps(room_list)
            }
            cids = self.clients.keys()
            for cid in cids:
                try:
                    self.clients[cid]['client'].sendMessage(json.dumps(send_payload).encode('utf-8'))
                except Exception as e:
                    print(e)

    def enter_room(self,client_id,room_name):
        room = self.rooms[room_name]
        self.clients[client_id]['room'] = room_name
        if client_id not in room['members']:
            room['members'].append(client_id)
            send_payload = {
                'type' : 'room_entrance',
                'client': { 'id':client_id, 'name':self.clients[client_id]['name']},
                'name' : room_name,
                'members' : [ { 'id' : memb ,'name':self.clients[memb]['name'] } for memb in room['members']]
            }
            self.send_room(room,send_payload)

    #Send data to a room
    def send_room(self,room,payload):
        for cid in room['members']:
            try:
                self.clients[cid]['client'].sendMessage(json.dumps(payload).encode('utf-8'))
            except Exception as e:
                print(e)

    def exit_room(self,client_id,room_name):
        room = self.rooms[room_name]
        self.clients[client_id]['room'] = None
        if client_id in room['members']:
            send_payload = {
                'type' : 'room_exit',
                'client': { 'id':client_id, 'name':self.clients[client_id]['name']},
                'name' : room_name,
                'members' : [ { 'id' : memb ,'name':self.clients[memb]['name'] } for memb in room['members']]
            }
            print('send_payload', send_payload)
            self.send_room(room,send_payload)
            #Now remove the member
            room['members'].remove(client_id)

    def close_room(self,room_name):
        print('Closing Room: ', room_name)
        if room_name in self.rooms.keys():
            #Message the users in the room to make it exit
            room = self.rooms[room_name]
            print('Room members are ', room['members'])
            for client_id in room['members']:
                send_payload = {
                    'type' : 'destroy_room',
                }
                self.send_room(room,send_payload)
            del self.rooms[room_name]
            del self.timers[room_name]
            self.send_room_list()


if __name__ == "__main__":
    log.startLogging(sys.stdout)

    contextFactory = ssl.DefaultOpenSSLContextFactory('keys/server.key',
                                                          'keys/server.crt')
    ServerFactory = BroadcastServerFactory
    factory = BroadcastServerFactory("wss://127.0.0.1:8080")

    factory.protocol = BroadcastServerProtocol
    #listenWS(factory)
    resource = WebSocketResource(factory)

    root = File(".")
    root.putChild(b"ws", resource)
    site = Site(root)
    reactor.listenSSL(8080, site, contextFactory)

    reactor.run()
