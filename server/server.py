import sys
import socket
import logging
import os
import time
from threading import Thread
import hashlib


filename=time.strftime("%Y-%m-%d-%H-%M-%S",time.localtime())+"-log.txt"
logging.basicConfig(filename=filename,level=logging.DEBUG,
                    format="%(name)s: %(message)s",
                    )
def calculatemd5(file):
    content = file.read()
    md5=hashlib.md5(content)
    md5bytes=md5.digest()
    return md5bytes

def recibirTodo(sock):
    datos = bytearray()
    while True:
        parte = sock.recv(4096)
        datos += bytearray(parte)
        if parte < 4096:
                break
    return datos

def enviarDatos(sock,datos):
    sock.sendall(datos)

def enviarArchivo(sock,filename):
    file=open(filename,"rb")
    sock.sendfile(file)
    file.close()

def enviarMD5(sock,filename):
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
        logging.info(" New thread started for "+ip+":"+str(port))

    def run(self):
        while True:
            data = recibirTodo(self.sock)
            message = data.decode("utf-8")
            if message.lower() == "exit":
                break
            elif message.lower() == "ready":
                self.ready=True

            elif message.lower().startsWith("md5:"):
                filename=message.split(":")[1]
                
        self.sock.close()



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

while True:
    client, (address,port) = server.accept()
    logging.info("Conectado con: " + address[0] + ":" + str(address[1]))
    newthread = ClientThread(address, port, client)
    newthread.start()
    clients.append(newthread)
    concurrentConnections += 1
    logging.info("Cantidad de clientes conectados: "+concurrentConnections)
server.close()