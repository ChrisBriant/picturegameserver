import sys, redis, uuid,json,ast, threading, random

from twisted.internet import reactor, ssl
from twisted.web.server import Site
from twisted.web.static import File
from twisted.python import log
from autobahn.twisted.websocket import WebSocketServerFactory, WebSocketServerProtocol #, listenWS
from autobahn.twisted.resource import WebSocketResource
from resettimer import TimerReset

#The timeout value in seconds to keep a room active
ROOM_TIMEOUT_VALUE = 1200
R = redis.Redis()

CARD_SET = [
                'c2','c3','c4','c5','c6','c7','c8','c9','c10','cJ','cQ','cK','cA',
                'd2','d3','d4','d5','d6','d7','d8','d9','d10','dJ','dQ','dK','dA',
                'h2','h3','h4','h5','h6','h7','h8','h9','h10','hJ','hQ','hK','hA',
                's2','s3','s4','s5','s6','s7','s8','s9','s10','sJ','sQ','sK','sA'
            ]

#Deal amount of cards from deck to the members and return dict
def deal(deck,cards,members):
    hand = {m:[] for m in members}
    for i in range(0,cards):
        for member in members:
            hand[member].append(deck.pop())
    return hand



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
            elif received_data['type'] == 'start_game':
                room_list = self.factory.start_game(received_data['name'])
            elif received_data['type'] == 'name':
                self.factory.set_name(received_data['client_id'],received_data['name'])
                send_payload = {
                    'type': 'set_name',
                    'message': received_data['name']
                }
                self.factory.send_client(received_data['client_id'],json.dumps(send_payload))
                print('Hello anyone home?')
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
            elif received_data['type'] == 'play_card':
                self.factory.play_card(received_data['room_id'],received_data['card'],received_data['client_id'])



    def connectionLost(self, reason):
        print("Connection Lost", reason)
        #WebSocketServerProtocol.connectionLost(self, reason)
        self.factory.unregister(self)


class BroadcastServerFactory(WebSocketServerFactory):
    def __init__(self, url):
        WebSocketServerFactory.__init__(self, url)
        self.clients = {}
        self.rooms = []
        self.timers = {}
        self.games = []

    #Stores an object in Redis
    def store_object(self,id,obj):
        obj_to_store = json.dumps(obj)
        R.set(id,obj_to_store)

    def get_from_store(self,id):
        obj = R.get(id)
        dict_obj = ast.literal_eval(obj.decode('utf-8'))
        #print('This is from redis',dict_obj)
        return dict_obj

    def remove_from_store(self,id):
        R.delete(id)

    def get_clients_from_store(self):
        cli_list = []
        for cli in self.clients.keys():
            obj = R.get(cli)
            dict_obj = ast.literal_eval(obj.decode('utf-8'))
            cli_list.append(dict_obj)
        return cli_list

    def get_rooms_from_store(self):
        room_list = []
        for room in self.rooms:
            obj = R.get(room)
            dict_obj = ast.literal_eval(obj.decode('utf-8'))
            room_list.append(dict_obj)
        return room_list

    def register(self, client):
        registered = [self.clients[i] for i in list(self.clients.keys())]
        ids = list(self.clients.keys())
        if client not in registered:
            while (cid := str(uuid.uuid4())) in ids:
                pass
            print("registered client {} with id {}".format(client.peer, cid))
            self.clients[cid] = client
            client_obj = {
                'cid' : cid,
                'name' : '',
                'room' : ''
            }
            self.store_object(cid,client_obj)
            payload = {
                'type': 'register',
                'yourid':cid
            }
            client.sendMessage(json.dumps(payload).encode())

    def send_client_list(self):
        #Get the clients and create
        #clients_data = [{'id':cli, 'name':self.clients[cli]['name']} for cli in clients_list]
        clients_data = self.get_clients_from_store()
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
        #client_id = None
        all_clients = list(self.clients)
        for cli in all_clients:
            if client == self.clients[cli]:
                client_id = cli
                #Notify room
                print('Here is the client ID ',client_id)
                client_room = self.get_from_store(client_id)['room']
                if client_room in self.rooms:
                    self.exit_room(client_id,client_room)
                del self.clients[cli]
                self.remove_from_store(cli)

        #For now (for testing purposes destroy all the rooms)
        #Timer will be used to closed rooms when implemented
        #!!!!!!!!!!!!!!!! IMPORTANT BELOW MUST BE REMOVED IN PRODUCTION FOR IT TO WORK !!!!!!!!!!!!!!!#
        self.rooms = []


    def broadcast(self, msg):
        print("broadcasting message '{}' to {} clients ...".format(msg, len(self.clients)))
        cids = self.clients.keys()
        for cid in cids:
            self.clients[cid].sendMessage(msg.encode('utf-8'))

    def send_client(self,client_id,data):
        print('sending to ',client_id)
        self.clients[client_id].sendMessage(data.encode('utf-8'))

    def set_name(self,client_id,name):
        client_obj = self.get_from_store(client_id)
        print('set name',client_obj)
        client_obj['name'] = name
        self.store_object(client_id,client_obj)

    def create_room(self,client_id,room):
        if room not in self.rooms:
            self.rooms.append(room)
            room_obj = {
                'owner' : client_id,
                'name' : room,
                'members' : [],
                'locked' : 'false',
                'game' : ''
            }
            self.store_object(room,room_obj)
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
            self.clients[client_id].sendMessage(json.dumps(send_payload).encode('utf-8'))

    def send_room_list(self):
            send_payload = {
                'type' : 'room_list',
                'rooms': json.dumps(self.get_rooms_from_store())
            }
            cids = self.clients.keys()
            for cid in cids:
                try:
                    self.clients[cid].sendMessage(json.dumps(send_payload).encode('utf-8'))
                except Exception as e:
                    print(e)

    def enter_room(self,client_id,room_name):
        room = self.get_from_store(room_name)
        client = self.get_from_store(client_id)
        client['room'] = room_name
        self.store_object(client_id,client)

        if client_id not in room['members']:
            room['members'].append(client_id)
            send_payload = {
                'type' : 'room_entrance',
                'client': { 'id':client_id, 'name':client['name']},
                'name' : room_name,
                'members' : [ { 'id' : memb ,'name':self.get_from_store(memb)['name'] } for memb in room['members']]
            }
            self.send_room(room,send_payload)
            self.store_object(room_name,room)

    #Send data to a room
    def send_room(self,room,payload):
        for cid in room['members']:
            try:
                self.clients[cid].sendMessage(json.dumps(payload).encode('utf-8'))
            except Exception as e:
                print(e)

    def exit_room(self,client_id,room_name):
        print('Let me out of here!', room_name)
        room = self.get_from_store(room_name)
        client = self.get_from_store(client_id)
        if client_id in room['members']:
            send_payload = {
                'type' : 'room_exit',
                'client': { 'id':client_id, 'name':client['name']},
                'name' : room_name,
                'members' : [ { 'id' : memb ,'name':self.get_from_store(memb)['name'] } for memb in room['members']]
            }
            print('send_payload', send_payload)
            self.send_room(room,send_payload)
            #Now remove the member
            room['members'].remove(client_id)
            self.store_object(room_name,room)
        client['room'] = None
        self.store_object(client_id,client)

    def close_room(self,room_name):
        print('Closing Room: ', room_name)
        if room_name in self.rooms:
            #Message the users in the room to make it exit
            room = self.get_from_store(room_name)
            print('Room members are ', room['members'])
            for client_id in room['members']:
                send_payload = {
                    'type' : 'destroy_room',
                }
                self.send_room(room,send_payload)
            self.remove_from_store(room_name)
            self.rooms.remove(room_name)
            del self.timers[room_name]
            self.send_room_list()

    def start_game(self,room_name):
        room = self.get_from_store(room_name)
        if room['game'] == '':
            room['locked'] = 'true'
            game_id = 'game' + room['owner']
            room['game'] = game_id
            self.games.append(game_id)
            deck = random.sample(CARD_SET,len(CARD_SET))#
            hands = deal(deck,7,room['members'])
            game = {
                'cards' : deck,
                'hands' : hands,
                'startplayer': random.choice(list(hands.keys()))
            }
            #Send data to client
            for player in hands.keys():
                payload = {
                    'type': 'hand',
                    'hand': hands[player],
                    'startplayer': game['startplayer']
                }
                self.clients[player].sendMessage(json.dumps(payload).encode())
            self.store_object(game_id,game)
            self.store_object(room_name,room)
            print(game)


    def play_card(self,room_name,card,client_id):
        room = self.get_from_store(room_name)
        game_id = 'game' + room['owner']
        game = self.get_from_store(game_id)
        print('ere is the game', game)




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
