import sys
import socket
import logging
import os
import time
from threading import Thread
import hashlib
import sys
import pathlib


filename=time.strftime("%Y-%m-%d-%H-%M-%S",time.localtime())+"-log.txt"
path=pathlib.Path("client/Logs/"+filename)
pathlib.Path.touch(path)
logging.basicConfig(filename=path,level=logging.DEBUG,
                    format="%(name)s: %(message)s",
                    )

def log(str):
    print(str)
    logging.info(str)

clientsNumber=sys.argv[1]

def calculatemd5(file,cident):
    content = file.read()
    md5=hashlib.md5(content)
    md5str=md5.hexdigest()
    log("Client#"+str(cident)+": File MD5 is "+md5str)
    return md5str

def comparehashes(hash1,hash2,cident):
    result=False
    if hash1 == hash2:
        result = True
    log("Client #"+str(cident)+": hash comparison result: "+str(result))
    return result

def getData(sock,cident):
    datos = bytearray()
    while True:
        parte = sock.recv(4096)
        datos += bytearray(parte)
        if len(parte) < 4096:
                break
    log("Client #"+str(cident)+": Bytes received: "+str(len(datos)))
    return datos

def getDataSize(sock,size,cident):
    datos = bytearray()
    while True:
        parte = sock.recv(1024)
        datos += bytearray(parte)
        if len(datos)>=size:
            break
    log("Client #"+str(cident)+": Bytes received: "+str(len(datos)))
    return datos


def sendData(sock,data,cident):
    log("Client #"+str(cident)+": sending "+str(len(data))+" Bytes")
    sock.sendall(data)

class Client(Thread):

    def __init__(self,socket,id):
        Thread.__init__(self)
        self.sock = socket
        self.ready = False
        self.md5=False
        self.kill = False
        self.id=id
        self.filename="Cliente"+str(self.id)+"-Prueba-"+str(clientsNumber)+".txt"
        log("New thread started for Cliente"+str(self.id)+";"+str(socket.getsockname()))

    def stop(self):
        self.kill=True

    
    def run(self):
        
        fullpath=pathlib.Path("client/ArchivosRecibidos/"+self.filename)
        pathlib.Path.touch(fullpath)
        while True: 
            data = getData(self.sock,self.id)
            message=data.decode("utf-8")
            log("Client#"+str(self.id)+": received message:" +message)
            if message.lower() == "hello":
                send="Ready".encode("utf-8")
                sendData(self.sock,send,self.id)
            if message.lower().startswith("filename"):
                self.ready=True
            if message.lower().startswith("file:"):
                size=int(message.split(":")[1])
                filedata=getDataSize(self.sock,size,self.id)
                file=open(fullpath,"wb")
                file.write(filedata)
                file.close()
                log("file saved as: "+fullpath.name)
                msgsend="MD5".encode("utf-8")
                sendData(self.sock,msgsend,self.id)
            if message.lower().startswith("md5:"):
                md5=message.split(":")[1]
                file=open(fullpath,"rb")
                hash1=calculatemd5(file,self.id)
                comparehashes(hash1,md5,self.id)
                sendData(self.sock,"exit".encode("utf-8"),self.id)
            if message.lower() == "exit":
                break
            if self.kill:
                break 
        log("closing connection from cliente#"+str(self.id))
        self.sock.close()

i=0
while i < int(clientsNumber):
    serveraddress=sys.argv[2]
    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM) 
    sock.connect((serveraddress,3000))
    log("Connected to"+str(sock.getsockname()))
    newthread = Client(sock,i)
    newthread.start()
    i+=1