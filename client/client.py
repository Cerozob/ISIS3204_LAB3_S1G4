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
path=pathlib.Path("server/Logs/"+filename)
pathlib.Path.touch(path)
logging.basicConfig(filename=path,level=logging.DEBUG,
                    format="%(name)s: %(message)s",
                    )

def log(str):
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
        if parte < 4096:
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
        self.filename="Cliente"+self.id+"-Prueba-"+clientsNumber+".txt"
        logging.info(" New thread started for Cliente"+str(self.id)+";"+socket.getsockname())

    def stop(self):
        self.kill=True

    
    def run(self):
        
        fullpath=pathlib.Path("client/ArchivosRecibidos/"+self.filename)
        fullpath.touch()
        while True: 
            data = getData(self.sock,self.id)
            message=data.decode("utf-8")
            if message.lower() == "hello":
                send="Ready".encode("utf-8")
                sendData(self.sock,send,self.id)
            if message.lower().startswith()== "filename:":
                self.ready=True
            if self.ready and data:
                file=open(fullpath,"wb")
                file.write(data)
                file.close()
                msgsend="MD5".encode("utf-8")
                sendData(self.sock,msgsend,self.id)
                self.md5=True
            if message.lower() == "md5":
                self.md5=True
            if self.md5 and data:
                file=open(fullpath,"rb")
                hash1=calculatemd5(file,self.id)
                hash2=message
                result=comparehashes(hash1,hash2)
                log("Client#"+str(self.id)+": hashing comparison result: "+str(result))
            if self.kill:
                break 
        self.sock.close()

i=0
while i < clientsNumber:
    serveraddress=sys.argv[2]
    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM) 
    sock.connect(address=(serveraddress,3000))
    logging.info("Connected to"+sock.getsockname())
    newthread = Client(sock)
    newthread.start()
    i+=1