import sys
import socket
import logging
import os
import time
from threading import Thread
import hashlib
import sys

filename=time.strftime("%Y-%m-%d-%H-%M-%S",time.localtime())+"-log.txt"
logging.basicConfig(filename=filename,level=logging.DEBUG,
                    format="%(name)s: %(message)s",
                    )

# Python server.py filename clientsnumber
testfile = sys.argv[1]
testclients = sys.argv[2]

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ("localhost", 3000)

try:
    server.bind(server_address)
except:
    logging.error(server.error)

server.listen(30)

logging.info("Server Listening on: "+server_address)

concurrentConnections=0

clients=[]

readyClients=0

def calculatemd5(file):
    content = file.read()
    md5=hashlib.md5(content)
    md5bytes=md5.digest()
    return md5bytes

def getData(sock):
    datos = bytearray()
    while True:
        parte = sock.recv(4096)
        datos += bytearray(parte)
        if parte < 4096:
                break
    return datos

def sendData(sock,data):
    sock.sendall(data)

def sendFile(sock,filename):
    file=open(filename,"rb")
    logging.info("enviando archivo: "+filename+"; tamaño: "+os.path.getsize(filename)+"\n desde: "+sock.getsockname()+" hacia: "+sock.getpeername())
    sock.sendfile(file)
    file.close()

def sendMD5(sock,filename):
    file=open(filename,"rb")
    md5=calculatemd5(file)
    sock.sendall(md5)
    file.close()


class ClientThread(Thread):
    def __init__(self, ip, port, socket):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.sock = socket
        self.ready = False
        self.md5=False
        self.kill = False
        logging.info(" New thread started for "+ip+":"+str(port))

    def stop(self):
        self.kill=True

    def run(self):
        while True:
            data = getData(self.sock)
            message = data.decode("utf-8")
            if message.lower() == "exit":
                break
            elif message.lower() == "ready":
                readyClients+=1
                self.ready=True
                self.md5=False
            elif message.lower() == "md5":
                self.md5=True
            if self.kill:
                break
        self.sock.close()

def sendFileToNClients(n,pFilename):
    i=0
    while i<n:
        if(clients[i].ready):
            sendFile(sock=i.sock,filename=pFilename)
            i+=1

    i=0
    while i<n:
        if(clients[i].md5):
            sendMD5(sock=i.sock,filename=pFilename)
            i+=1

enoughClients=False

while True:
    client, (address,port) = server.accept()
    logging.info("Conectado con: " + address[0] + ":" + str(address[1]))
    newthread = ClientThread(address, port, client)
    newthread.start()
    clients.append(newthread)
    concurrentConnections += 1
    if(readyClients>=testclients):
        sendFileToNClients(testclients,testfile)
        break
    logging.info("Cantidad de clientes conectados: "+concurrentConnections)
logging.info("prueba terminada, cerrando conexiones y servicdor")
for i in clients:
    i.sock.close()
    i.stop()
server.close()