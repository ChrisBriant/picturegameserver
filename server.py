import sys, redis, uuid,json,ast, threading, random

from twisted.internet import reactor, ssl
from twisted.web.server import Site
from twisted.web.static import File
from twisted.python import log
from autobahn.twisted.websocket import WebSocketServerFactory, WebSocketServerProtocol #, listenWS
from autobahn.twisted.resource import WebSocketResource
from resettimer import TimerReset
from itertools import groupby
from difflib import SequenceMatcher

from getrandomword import get_random_word

#The timeout value in seconds to keep a room active
ROOM_TIMEOUT_VALUE = 1200000
R = redis.Redis()

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
                self.factory.start_game(received_data['name'])
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
            elif received_data['type'] == 'picture':
                self.factory.add_picture(received_data['client_id'],received_data['game_id'],received_data['picture'])
            elif received_data['type'] == 'guess':
                self.factory.process_guess(received_data['client_id'],received_data['game_id'],received_data['guess'])
            elif received_data['type'] == 'next_round':
                self.factory.start_new_round(received_data['game_id'])
            # elif received_data['type'] == 'play_card':
            #     self.factory.play_card(received_data['room_id'],received_data['card'],received_data['client_id'])
            # elif received_data['type'] == 'pick_trump':
            #     self.factory.pick_trump(received_data['room_id'],received_data['card'],received_data['client_id'])
            # elif received_data['type'] == 'tie_breaker_choice':
            #     self.factory.tie_break(received_data['room_id'],received_data['card'],received_data['client_id'],received_data['ties'],received_data['tie_break_id'])
            # elif received_data['type'] == 'end_tie_break':
            #     self.factory.tie_break_end(received_data['room_id'],received_data['client_id'],received_data['tie_break_id'])
            #
            #



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

    def is_in_store(self,id):
        obj = R.get(id)
        if obj:
            return True
        else:
            return False

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
            try:
                obj = R.get(room)
                dict_obj = ast.literal_eval(obj.decode('utf-8'))
                room_list.append(dict_obj)
            except Exception as e:
                #Room does not exist
                print("Room does not exist", e)
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
                print('CLIENT ID IS', client_id)
                client = self.get_from_store(client_id)
                #Exit room if still in there
                print("THE CLIENT SHOULD NOT HAVE A ROOM", client['room'])
                if client['room'] != '' and self.is_in_store(client['room']):
                    #Try removing the room here
                    client_room = self.get_from_store(client['room'])
                    print("There should be rooms", self.rooms)
                    if client['room'] in self.rooms:
                        print("CALLING EXIT ROOM", self.rooms)
                        self.exit_room(client_id,client['room'])
                del self.clients[cli]
                self.remove_from_store(cli)
                self.send_room_list()
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
        #check empty
        if room['game'] == '':
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
        else:
            send_payload = {
                'type' : 'room_occupied',
                'message' : 'Room {} is not available, a game is in progress.'.format(room['name']),
            }
            self.clients[client_id].sendMessage(json.dumps(send_payload).encode())

    #Send data to a room
    def send_room(self,room,payload):
        for cid in room['members']:
            try:
                self.clients[cid].sendMessage(json.dumps(payload).encode('utf-8'))
            except Exception as e:
                print(e)

    def exit_room(self,client_id,room_name):
        destroy_game_room = False
        room = self.get_from_store(room_name)
        print('Let me out of here!', room)
        client = self.get_from_store(client_id)
        #If a game is in progress
        if client_id in room['members']:
            if room['game'] != '':
                #Destroy the game and room send room exit payload
                self.remove_from_store(room['game'])
                self.remove_from_store(room_name)
                send_payload = {
                    'type' : 'game_exit',
                    'client': { 'id':client_id, 'name':client['name']},
                    'name' : room_name,
                    'members' : [ { 'id' : memb ,'name':self.get_from_store(memb)['name'] } for memb in room['members']],
                    'rooms': json.dumps(self.get_rooms_from_store())
                }
                self.send_room(room,send_payload)
                self.rooms.remove(room_name)
            else:
                send_payload = {
                    'type' : 'room_exit',
                    'client': { 'id':client_id, 'name':client['name']},
                    'name' : room_name,
                    'members' : [ { 'id' : memb ,'name':self.get_from_store(memb)['name'] } for memb in room['members']],
                    'rooms': json.dumps(self.get_rooms_from_store())
                }
                print('send_payload', send_payload)
                self.send_room(room,send_payload)
        else:
            send_payload = {
                'type' : 'room_exit_nonmember',
            }
            self.clients[client_id].sendMessage(json.dumps(send_payload).encode())
        client = self.get_from_store(client_id)
        client['room'] = ''
        self.store_object(client_id,client)


    def start_game(self,room_name):
        print("STARTING GAME")
        room = self.get_from_store(room_name)
        if room['game'] == '':
            room['locked'] = 'true'
            while (cid := str(uuid.uuid4())) in self.games:
                pass
            game_id = cid
            room['game'] = game_id
            self.games.append(game_id)
            #Get room member ids
            ids = [ { 'id' : memb ,'name':self.get_from_store(memb)['name'] } for memb in room['members']]
            rec,level,random_word = get_random_word(1)[0]
            game = {
                'startplayer': random.choice(ids),
                'players':room['members'],
                'remaining_players': room['members'],
                'canvas' : [],
                'word' : random_word,
                'room_name' : room_name,
                'guesses' : []
            }
            print(game)
            #Send data to client
            payload = {
                'type': 'game_start',
                'startplayer': game['startplayer'],
                'game_id': game_id
            }
            self.send_room(room,payload)
            self.store_object(game_id,game)
            #Update room
            self.store_object(room_name,room)
            self.send_room_list()
            #Send the random word to the other playes
            #others = [p['id'] for p in ids if p['id'] != game['startplayer']['id']]
            payload = {
                'type': 'word',
                'word': game['word']
            }
            try:
                self.clients[game['startplayer']['id']].sendMessage(json.dumps(payload).encode('utf-8'))
            except Exception as e:
                print(e)

    def add_picture(self,client_id,game_id,picture):
        game = self.get_from_store(game_id)
        game['canvas'] = picture
        print('START PLAYER', game['players'])
        others = [p for p in game['players'] if p != client_id]
        for player in others:
            payload = {
                'type' : 'picture',
                'picture' : game['canvas']
            }
            self.clients[player].sendMessage(json.dumps(payload).encode())
        self.store_object(game_id,game)

    def process_guess(self,client_id,game_id,guess):
        client_obj = self.get_from_store(client_id)
        game = self.get_from_store(game_id)
        room = self.get_from_store(game['room_name'])
        #Determine guessed correct
        matchscore = SequenceMatcher(None, guess, game['word']).ratio()
        if matchscore > 0.7:
            #Guess correct
            guess_correct = True
            guess_correct_store = 'true'
            #remove the winner
            #THIS IS CAUSING A PROBLEM AS EVALUATES TO NULL
            game['remaining_players'] =  [memb for memb in game['remaining_players'] if memb !=  game['startplayer']['id']]
            print('Here are the others', game['remaining_players'])
        else:
            guess_correct = False
            guess_correct_store = 'false'
        #ADD GUESS TO THE LIST AND CHECK AGAINST WORD
        new_guess = {
            'guess' : guess,
            'client_id' : client_id,
            'client_name':client_obj['name'],
            'correct' : guess_correct_store
        }
        game['guesses'].append(new_guess)


        if len(game['remaining_players']) <= 0:
            #Trigger end game send a different type to be processed differently
            type = 'game_over'
            self.remove_from_store(game_id)
        else:
            type = 'guess'
            self.store_object(game_id,game)
        payload = {
            'type' : type,
            'guess' : guess,
            'client_id' : client_id,
            'client_name':client_obj['name'],
            'correct' : guess_correct
        }
        self.send_room(room,payload)


    def start_new_round(self,game_id):
        print('NEW ROUND', game_id)
        game = self.get_from_store(str(game_id))
        rec,level,random_word = get_random_word(1)[0]

        room = self.get_from_store(game['room_name'])
        ids = [ { 'id' : memb ,'name':self.get_from_store(memb)['name'] } for memb in game['remaining_players']]
        #Set game variables
        game['startplayer'] = random.choice(ids)
        game['guesses'] = []
        game['word'] = random_word
        payload = {
            'type': 'new_round',
            'startplayer': game['startplayer'],
            'game_id': game_id
        }
        self.send_room(room,payload)
        #Send the word
        payload = {
            'type': 'word',
            'word': game['word']
        }
        self.clients[game['startplayer']['id']].sendMessage(json.dumps(payload).encode('utf-8'))
        self.store_object(game_id,game)



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


if __name__ == "__main__":
    log.startLogging(sys.stdout)
    contextFactory = ssl.DefaultOpenSSLContextFactory('keys/server.key',
                                                          'keys/server.crt')
    ServerFactory = BroadcastServerFactory
    factory = BroadcastServerFactory("wss://127.0.0.1:8080")
    factory.protocol = BroadcastServerProtocol
    resource = WebSocketResource(factory)
    root = File(".")
    root.putChild(b"ws", resource)
    site = Site(root)
    reactor.listenSSL(8080, site, contextFactory)
    reactor.run()
