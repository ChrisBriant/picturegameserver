#Trying this stuff with asyncio

import asyncio, ssl, redis,uuid,json,ast

from autobahn.asyncio.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory

#The timeout value in seconds to keep a room active
ROOM_TIMEOUT_VALUE = 120
R = redis.Redis()

clients = {}
rooms = {}
timers = {}

#Stores an object in Redis
def store_object(id,obj):
    obj_to_store = json.dumps(obj)
    R.set(id,obj_to_store)

def get_from_store(id):
    obj = R.get(id)
    print('This is from redis',obj)
    dict_obj = ast.literal_eval(obj)
    return obj

class BroadcastServerProtocol(WebSocketServerProtocol):
    def __init__(self):
        WebSocketServerProtocol.__init__(self)


    def onOpen(self):
        print('ON OPEN')
        registered = [clients[i] for i in list(clients.keys())]
        ids = list(clients.keys())
        if self not in registered:
            while (cid := str(uuid.uuid4())) in ids:
                pass
            print("registered client {} with id {}".format(self.peer, cid))
            clients[cid] = self
            client_obj = {
                'cid' : cid,
                'name' : '',
                'room' : ''
            }
            store_object(cid,client_obj)
            payload = {
                'type': 'register',
                'yourid':cid
            }
            self.sendMessage(json.dumps(payload).encode())
            print('done register')


    def onConnect(self, request):
        print("Client connecting: {0}".format(request.peer))


    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            print("Text message received: {0}".format(payload.decode('utf8')))

        # echo back message verbatim
        self.sendMessage(payload, isBinary)

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))


if __name__ == '__main__':
    ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_ctx.check_hostname = False
    ssl_ctx.load_cert_chain('./keys/server.pem','./keys/server.key')

    factory = WebSocketServerFactory("wss://127.0.0.1:8080")
    factory.protocol = BroadcastServerProtocol

    loop = asyncio.get_event_loop()
    coro = loop.create_server(factory, '0.0.0.0', 8080, ssl=ssl_ctx)
    server = loop.run_until_complete(coro)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()
        loop.close()
