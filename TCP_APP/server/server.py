import sys
import socket
import logging
import os
import time
from threading import Thread
import hashlib
import sys
import pathlib

# python server.py filename clientsnumber platform

def log(str):
    print(str)
    logging.info(str)


testfile = pathlib.Path("server/"+sys.argv[1])
testclients = sys.argv[2]
concurrentConnections=0
clients=[]

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


filename=time.strftime("%Y-%m-%d-%H-%M-%S",time.localtime())+"-log.txt"
path=pathlib.Path("Logs/"+filename)

server_address = ("", 3000)

pathlib.Path.touch(path)
logging.basicConfig(filename=path,level=logging.DEBUG,
                    format="%(name)s: %(message)s \n",
                    )
if sys.argv[3]=="ubuntu":
    ipv4 = os.popen('ip addr show ens33').read().split("inet ")[1].split("/")[0]
    server_address=(ipv4,3000)
    ipaddress=ipv4
    testfile = pathlib.Path(sys.argv[1])

hostname=socket.gethostname() 
ipaddress=server_address[0]
try:
    server.bind(server_address)
except:
    logging.error(server.error)

server.listen(30)

log("Server Listening on: "+str(ipaddress))
log("File to send: "+testfile.name+"number of clients: "+testclients)



def calculatemd5(file):
    content = file.read()
    md5=hashlib.md5(content)
    md5str=md5.hexdigest()
    log("Server: File MD5 is "+md5str)
    return md5str

def getData(sock):
    datos = bytearray()
    while True:
        parte = sock.recv(4096)
        datos += bytearray(parte)
        if len(parte) < 4096:
                break
    log("Server: Bytes received: "+str(len(datos)))
    return datos

def sendData(sock,data,client):
    log("Server: sending "+str(len(data))+" Bytes to client #"+str(client))
    sock.sendall(data)

def sendFile(sock,filename,client):
    file=open(filename,"rb")
    size=os.path.getsize(filename)
    send=("file:"+str(size)+":").encode("utf-8")
    sock.send(send)
    time.sleep(0.5)
    log("Sending file: "+filename.name+"; Size: "+str(size)+"\n from: "+str(sock.getsockname())+" to client #"+str(client)+" with address: "+str(sock.getpeername()))
    start=time.time()
    sock.sendfile(file)
    file.close()
    end=time.time()
    total=end-start
    log("Server: elapsed time to transfer file from "+str(sock.getsockname())+" to client #"+str(client)+" with address: "+str(sock.getpeername())+" :"+str(total)+"milliseconds")

def sendMD5(sock,filename,client):
    file=open(filename,"rb")
    log("Server: sending MD5 hash to client #"+str(client)+" with address: "+str(sock.getpeername()))
    md5=str("MD5:"+calculatemd5(file)).encode("utf-8")
    sock.sendall(md5)
    file.close()


class ClientThread(Thread):
    def __init__(self, ip, port, socket,identifier):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.sock = socket
        self.ready = False
        self.md5=False
        self.kill = False
        self.id=identifier
        log(" New thread started for Client #"+str(self.id)+" with address:"+ip+":"+str(port))

    def stop(self):
        self.kill=True

    def run(self):
        hello="Hello Client#"+str(self.id)
        self.sock.send(hello.encode("utf-8"))
        while True:
            data = getData(self.sock)
            message = data.decode("utf-8")
            log("Server: received message from Client#"+str(self.id)+":" +message)
            if message.lower() == "exit":
                sendData(self.sock,"exit".encode("utf-8"),self.id)
                break
            elif message.lower() == "ready":
                log("client #"+str(self.id)+"is ready to get a file")
                self.ready=True
                send="Filename: "+testfile.name
                msgsend=send.encode("utf-8")
                log("sending client #"+str(self.id)+"is ready to get a file")
                sendData(self.sock,msgsend,self.id)
                self.md5=False
            elif message.lower() == "md5":
                self.md5=True
            if self.kill:
                break
        log("closing connection from"+str(self.ip)+":"+str(self.port))
        self.sock.close()

def sendFileToNClients(n,pFilename):
    i=0
    log("server : starting file sending test: "+str(n)+" clients; File: "+str(pFilename))
    while i<n:
        if(clients[i].ready):
            th = Thread(target=sendFile(sock=clients[i].sock,filename=pFilename,client=clients[i].id))
            th.start()
            i+=1

    i=0
    while i<n:
        if(clients[i].md5):
            th = Thread(target=sendMD5(sock=clients[i].sock,filename=pFilename,client=clients[i].id))
            th.start()
            i+=1
            
while True:
    client, (address,port) = server.accept()
    
    log("Conectado con: " + str(address) + ":" + str(port))
    newthread = ClientThread(address, port, client,concurrentConnections)
    concurrentConnections += 1
    newthread.start()
    clients.append(newthread)
    if(concurrentConnections>=int(testclients)):
        sendFileToNClients(int(testclients),testfile)
    if(concurrentConnections==-1):
        break
    log("Cantidad de clientes conectados: "+str(concurrentConnections))
server.close()
