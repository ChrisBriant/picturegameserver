# knockoutwhistgameserver

This is a game server project to allow players to play a game of knock out whist. It will use the Python Twisted framework and Autobahn to implement a websockets solution at the backend.

#To generate a self signed cert in the keys folder
# Generate Private Key:
openssl genrsa -out server.key 2048

# Generate Certificate Signing Request:
openssl req -new -key server.key -sha256 -out server.csr

# Generate a Self-Signed Certificate:
openssl x509 -req -days 365 -in server.csr -signkey server.key -sha256 -out server.crt

# Convert the CRT to PEM format:
openssl x509 -in server.crt -out server.pem -outform PEM
