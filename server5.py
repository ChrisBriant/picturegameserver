import sys, redis, uuid,json,ast, threading, random

from twisted.internet import reactor, ssl
from twisted.web.server import Site
from twisted.web.static import File
from twisted.python import log
from autobahn.twisted.websocket import WebSocketServerFactory, WebSocketServerProtocol #, listenWS
from autobahn.twisted.resource import WebSocketResource
from resettimer import TimerReset
from itertools import groupby

#The timeout value in seconds to keep a room active
ROOM_TIMEOUT_VALUE = 1200000
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
    if cards == 7:
        #choose trump
        trump = deck.pop()
    else:
        trump = ''
    return hand, trump

def get_highest(trick,suit):
    highest = None
    #filter for suit
    playable_cards = [play for play in trick if play['card'][0] == suit]
    for card in playable_cards:
        if card['card'][1:] == 'J':
            cardval = 11
        elif card['card'][1:] == 'Q':
            cardval = 12
        elif card['card'][1:] == 'K':
            cardval = 13
        elif card['card'][1:] == 'A':
            cardval = 14
        else:
            cardval = int(card['card'][1:])
        if highest and highest['val'] < cardval:
            highest['player'] = card['player']
            highest['val'] = cardval
        #First iteration hhighest doesn't exist
        if not highest:
            highest = dict()
            highest['player'] = card['player']
            highest['val'] = cardval
    return highest


def get_order(c):
    return c['order']


def calc_trick(trick,trump):
    #Find if trump is played
    suit = trump[0]
    suits = [card['card'][0] for card in trick]
    if suit in suits:
        #trumps = [play['card'][1:] for play in trick if play['card'][0] == suit]
        #print('TRUMPS',trumps)
        winner = get_highest(trick,suit)
        print('The winner is ', winner)
    else:
        #Get the suit of the first played card
        first = min(trick,key=get_order)
        print('First Card is',first)
        suit = first['card'][0]
        winner = get_highest(trick,suit)
        print('The winner is ', winner)
    return winner


def calc_round_winner(completed_tricks,round_number):
    scores = []
    for key,list in groupby(completed_tricks, lambda x: x['winner']):
        #print(key,sum(1 for _ in list))
        score = {
            'player' : key,
            'score' : sum(1 for _ in list)
        }
        scores.append(score)
    #Find the highest score
    highest = None
    for score in scores:
        if not highest:
            highest = score
        else:
            if score['score'] > highest['score']:
                highest = score
    #Find if other elements are tied
    ties = [ item for item in scores if item['score'] == highest['score']]
    # print('scores', scores)
    # print('highest',highest)
    # print('ties', ties)
    round_result = {
        'scores' : scores,
        'winner' : highest,
        'ties' : ties,
        'round_number':round_number
    }
    return round_result



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
            elif received_data['type'] == 'pick_trump':
                self.factory.pick_trump(received_data['room_id'],received_data['card'],received_data['client_id'])
            elif received_data['type'] == 'tie_breaker_choice':
                self.factory.tie_break(received_data['room_id'],received_data['card'],received_data['client_id'],received_data['ties'],received_data['tie_break_id'])
            elif received_data['type'] == 'end_tie_break':
                self.factory.tie_break_end(received_data['room_id'],received_data['client_id'],received_data['tie_break_id'])





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

    def calc_overall_winner(self,results):
        scores = []
        results.sort(key=lambda x: x['winner']['player']['player'])
        print('LETS SEE THE WINNER')
        #The list needs to be sorted first to work properly
        for key,list in groupby(results, lambda x: x['winner']['player']['player']):
            score = sum(1 for _ in list)
            print(key,score)
            score = {
                'player' : key,
                'score' : score,
                'winner_name' : self.get_from_store(key)['name']
            }
            scores.append(score)
        #Find the highest score
        highest = None
        for score in scores:
            if not highest:
                highest = score
            else:
                if score['score'] > highest['score']:
                    highest = score
        ties = [ item for item in scores if item['score'] == highest['score']]
        results.sort(key=lambda x: x['round_number'])
        overall_result = {
            'scores' : scores,
            'winner' : highest,
            'ties' : ties,
            'round_results' : results
        }
        return overall_result

    def suit_to_value(self,suit):
        #Convert the suit to a value to make tie breaking easier
        if suit == 'h':
            return 1
        elif suit == 's':
            return 2
        elif suit == 'd':
            return 3
        elif suit == 'c':
            return 4

    def calc_tie_winner(self,ties):
        highest = None
        for tie in ties['tie_breaks']:
            suit = tie['card'][0]
            value = tie['card'][0]
            if value == 'J' :
                value = 11
            elif value == 'Q':
                value = 12
            elif value == 'K':
                value = 13
            elif value == 'A':
                value = 14
            if not highest:
                highest = {
                    'client_id' : tie['client_id'],
                    'user_name' :  tie['user_name'],
                    'value' : value,
                    'suit' : suit
                }
            else:
                if value > highest['value']:
                    highest = {
                        'client_id' : tie['client_id'],
                        'user_name' :  tie['user_name'],
                        'value' : value,
                        'suit' : suit
                    }
                elif value == highest['value']:
                     #Same value so go by suit
                     if self.suit_to_value(suit) > self.suit_to_value(highest['suit']):
                         highest = {
                             'client_id' : tie['client_id'],
                             'user_name' :  tie['user_name'],
                             'value' : value,
                             'suit' : suit
                         }
        return highest



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
        STARTING_HAND = 6
        room = self.get_from_store(room_name)
        if room['game'] == '':
            room['locked'] = 'true'
            game_id = 'game' + room['owner']
            room['game'] = game_id
            self.games.append(game_id)
            deck = random.sample(CARD_SET,len(CARD_SET))#
            hands, trump = deal(deck,STARTING_HAND,room['members'])

            ###########TEST END GAME CONDITION#################
            #Fix the round results so we are on the last round
            # fixed_round_results = self.fix_rounds()
            trump = 'h'
            ###################################################
            game = {
                'cards' : deck,
                'hands' : hands,
                'startplayer': random.choice(list(hands.keys())),
                'trick' : [],
                'trick-count': STARTING_HAND,
                'trump' : trump,
                'completed_tricks':[],
                #'round_number': 1,
                'round_results': [],
                #Test values below
                'round_number': 6,
                # 'round_results': fixed_round_results
            }
            print(game)
            #Send data to client
            for player in hands.keys():
                payload = {
                    'type': 'hand',
                    'hand': hands[player],
                    'startplayer': game['startplayer'],
                    'trump' : trump,
                    'trick' : game['trick'],
                    'completed_tricks': game['completed_tricks'],
                    'round_number': game['round_number']
                }
                self.clients[player].sendMessage(json.dumps(payload).encode())
            self.store_object(game_id,game)
            self.store_object(room_name,room)

    #Putting trick completion logic into procedure for reuse
    def complete_trick(self,game):
        # deal_amount = 7 - game['round_number']
        # game['round_number'] += 1
        # #Deal new hands - Trump is discarded
        # deck = random.sample(CARD_SET,len(CARD_SET))#
        # hands, trump = deal(deck,deal_amount,room['members'])
        # game['trump'] = trump
        # game['hands'] = hands
        #Calculate winner of round
        round_result = calc_round_winner(game['completed_tricks'],game['round_number'])
        #Add the name of the winner
        #winner_name = self.get_from_store(round_result['winner']['player']['player'])['name']
        winner_name = 'bob' #FOR NOW
        round_result['winner_name'] = winner_name
        game['round_results'].append(round_result)


    def play_card(self,room_name,card,client_id):
        endofgame = False  #Flag
        room = self.get_from_store(room_name)
        game_id = 'game' + room['owner']
        game = self.get_from_store(game_id)
        #The last card is played
        #len(game['trick']) + 1 == len(room['members']) and len(game['hands'][client_id]) == 1:
        if len(game['trick']) + 1 == len(room['members']):
            #Calculate winner of trick
            game['trick'].append({
                'player' : client_id,
                'card' : card,
                'order' : len(game['trick']),
            })
            winner = calc_trick(game['trick'],game['trump'])

            # FIX THE WINNER
            # winner =  {
            #     'player': game['startplayer'],
            #     'val' : 1
            # }

            #Decrement the trick count
            game['trick-count'] -= 1

            #SOMETIMES FAILS AFTER HERE - NEED TO FIND OUT WHY
            print('GAME HANDS',client_id, game['hands'])
            #############################################

            #Send the completed trick data back
            game['hands'][client_id].remove(card)
            game['startplayer'] = winner['player']
            completed_trick = {
                'trick' : game['trick'],
                'winner' : winner
            }
            game['completed_tricks'].append(completed_trick)
            #Reset the trick to empty
            game['trick'] = []
            if game['trick-count'] == 0:
                #Start new round
                type = 'new_round'
                deal_amount = 7 - game['round_number']
                game['round_number'] += 1
                #Deal new hands - Trump is discarded
                deck = random.sample(CARD_SET,len(CARD_SET))#
                hands, trump = deal(deck,deal_amount,room['members'])
                game['trump'] = trump
                game['hands'] = hands
                #Calculate winner of round
                round_result = calc_round_winner(game['completed_tricks'],game['round_number'])
                #Add the name of the winner
                winner_name = self.get_from_store(round_result['winner']['player']['player'])['name']
                round_result['winner_name'] = winner_name
                game['round_results'].append(round_result)
                print('WINNER NAME',game['round_results'])
            else:
                type = 'hand'
                round_result = {}
            if game['round_number'] >= 7:
                #Trigger end of game
                print("END GAME", game['round_number'])
                winner = self.calc_overall_winner(game['round_results'])
                winner_name = self.get_from_store(winner['winner']['player'])['name']
                winner['winner_name'] = winner_name
                ##################FIX TIE BREAKER################
                # ties = [
                #     {
                #         'player': room['members'][0],
                #         'score' : 3,
                #         'winner_name' :self.get_from_store(room['members'][0])['name']
                #     },
                #     {
                #         'player': room['members'][1],
                #         'score' : 3,
                #         'winner_name' :self.get_from_store(room['members'][1])['name']
                #     }
                # ]
                # winner['ties'] = ties
                ####################################################
                if len(winner['ties']) > 1:
                    #Create a tie breaker deck
                    winner['tie_breaker_deck'] = random.sample(CARD_SET,len(CARD_SET))
                    ## TODO: ADD A START PLAYER
                    winner['tie_starter'] = random.sample(winner['ties'],1)[0]['player']
                    #If on tie breaker we don't want to destry the game
                    endofgame = False
                else:
                    endofgame = True
                for player in room['members']:
                    payload = {
                        'type': 'end_game',
                        'winner': winner
                        #'overall':game['round_results']
                    }
                    self.clients[player].sendMessage(json.dumps(payload).encode())
                #Flag to stop game from being added

            else:
                #Send the result of the completed trick wheter new round or new hand
                for player in room['members']:
                    payload = {
                        'type': type,
                        'hand': game['hands'][player],
                        'startplayer': game['startplayer'],
                        'trump' : game['trump'],
                        'trick' : game['trick'],
                        'completed_tricks': game['completed_tricks'],
                        'round_number': game['round_number'],
                        'round_result' : round_result
                    }
                    self.clients[player].sendMessage(json.dumps(payload).encode())
        else:
            #Add card to trick and then switch player
            game['trick'].append({
                'player' : client_id,
                'card' : card,
                'order' : len(game['trick']),
            })
            #remove from hand
            print('card and hand' ,game['hands'][client_id], card)
            game['hands'][client_id].remove(card)
            remaining_players = [p for p in room['members'] if p != client_id]
            game['startplayer'] = remaining_players[0]
            for player in room['members']:
                payload = {
                    'type': 'hand',
                    'hand': game['hands'][player],
                    'startplayer': game['startplayer'],
                    'trump' : game['trump'],
                    'trick' : game['trick'],
                    'completed_tricks': game['completed_tricks'],
                    'round_number': game['round_number']
                }
                self.clients[player].sendMessage(json.dumps(payload).encode())
        if endofgame:
            self.remove_from_store(game_id)
        else:
            self.store_object(game_id,game)


    def pick_trump(self,room_name,card,client_id):
        room = self.get_from_store(room_name)
        game_id = 'game' + room['owner']
        game = self.get_from_store(game_id)
        suit = card[0]
        game['trump'] = suit
        for player in room['members']:
            payload = {
                'type': 'trump_selected',
                'trump' : game['trump'],
            }
            self.clients[player].sendMessage(json.dumps(payload).encode())
        self.store_object(game_id,game)


    def tie_break(self,room_name,card,client_id,ties,tie_break_id):
        room = self.get_from_store(room_name)
        print('THIS IS A TIE BREAK', room_name,card,client_id,ties,tie_break_id)
        #Filter the ties to exclude the player
        ties = [t for t in ties if t != client_id]
        if tie_break_id == '':
            #Create new tie break object
            tie_break_id = "tiebreak" + str(uuid.uuid4())
            tie_break = {
                'tie_breaks' : [],
                'winner' : ''
            }
            tie_break['tie_breaks'].append(
                {
                    'client_id' : client_id,
                    'user_name' : self.get_from_store(client_id),
                    'card' : card,
                    'ties' : ties
                }
            )
        else:
            print('TIE BREAK ID IS',tie_break_id)
            tie_break = self.get_from_store(tie_break_id)
            tie_break['tie_breaks'].append(
                {
                    'client_id' : client_id,
                    'user_name' : self.get_from_store(client_id),
                    'card' : card,
                    'ties' : ties
                }
            )
        if len(ties) == 0:
            winner = self.calc_tie_winner(tie_break)
            print('HERE IS THE TIE BREAK WINNER', winner)
            payload = {
                'type': 'tie_break',
                'start_player': winner['client_id'],
                'ties' : ties,
                'winner' : winner,
                'tie_break_id' : tie_break_id
            }
            tie_break['winner'] = winner
        else:
            payload = {
                'type': 'tie_break',
                'start_player': ties[0],
                'ties' : ties,
                'winner' : None,
                'tie_break_id' : tie_break_id
            }
        self.store_object(tie_break_id,tie_break)
        #Send tie break data
        for player in room['members']:
            self.clients[player].sendMessage(json.dumps(payload).encode())

    def tie_break_end(self,room_name,client_id,tie_break_id):
        room = self.get_from_store(room_name)
        game_id = 'game' + room['owner']
        game = self.get_from_store(game_id)
        tiebreak = self.get_from_store(tie_break_id)
        #Get the latest round result and modify
        last_round = [ result for result in game['round_results'] if result['round_number'] == game['round_number']]
        last_round = last_round[0]
        new_rounds = [ result for result in game['round_results'] if result['round_number'] != game['round_number']]
        print('GAME ROUND RESULT', game['round_number'], tiebreak)
        last_round['winner']['player']['player'] = tiebreak['winner']['client_id']
        new_rounds.append(last_round)
        game['round_results'] = new_rounds
        #Remove the tie break object
        self.remove_from_store(tie_break_id)
        if game['round_number'] >= 7:
            #End game
            winner = self.calc_overall_winner(game['round_results'])
            winner_name = self.get_from_store(winner['winner']['player'])['name']
            winner['winner_name'] = winner_name
            self.remove_from_store(game_id)
        else:
            #End round
            #Winner doesn't exist yet
            winner = None
            #CHANGE start_player, round_result, winner
        for player in room['members']:
            payload = {
                'type': 'end_tie_break',
                'winner': winner,
                'start_player': tiebreak['winner']['client_id'],
                'round_result': last_round
            }
            self.clients[player].sendMessage(json.dumps(payload).encode())



    #For testing purposes only - lay out the rounds up until the last one
    def fix_rounds(self):
        round_results = []
        for i in range(0,6):
            rand_client = random.sample(list(self.clients.keys()),1)
            player = self.get_from_store(rand_client[0])
            result_obj = {
                'scores' : [],
                'winner': {'player': {'player': rand_client[0], 'val': 1}, 'score': 6},
                'round_number': i+1,
                'winner_name': player['name']
            }
            round_results.append(result_obj)
        print('ROUND RESULTS', round_results, list(self.clients.keys()))
        return round_results


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
