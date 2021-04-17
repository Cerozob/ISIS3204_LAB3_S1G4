import sys
import socket
import logging
import os
import threading
import time
from threading import Thread
import hashlib
import sys
import pathlib

# python server.py filename clientsnumber platform

def log(str):
    print(str)
    logging.info(str)


testfile = pathlib.Path(sys.argv[1])
testclients = sys.argv[2]
concurrentConnections=0
clients=[]
clientudpaddr=""

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
    logging.error(msg="e")

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

def sendFile(sock,filename,client,clientthread):
    
    udpsocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    udpsocket.bind((server_address[0],0))
    log("Server: UDP Socket with address"+str(udpsocket.getsockname())+" created")
    file=open(filename,"rb")
    size=os.path.getsize(filename)
    send=("file:"+str(size)+":").encode("utf-8")
    sock.send(send)
    time.sleep(0.3)
    sock.send(str(str(udpsocket.getsockname()[0])+":"+str(udpsocket.getsockname()[1])).encode("utf-8"))
    clientthread.availableaddress.wait()
    address=clientthread.clientudpaddr.split(":")[0]
    port=int(clientthread.clientudpaddr.split(":")[1])
    log("Server: received Client #"+str(client)+" UDP address: "+address+":"+str(port))
    time.sleep(0.5)
    log("Sending file through UDP: "+filename.name+"; Size: "+str(size)+"\n from: "+str(udpsocket.getsockname())+" to client #"+str(client)+" with address: "+str(address)+":"+str(port))
    
    time.sleep(2)
    start = time.time()
    # el máximo es 65508,pero 51200 permite divir los archivos de 100MB y 250MB en partes exactas
    data = file.read(51200)
    while (data):
        if(udpsocket.sendto(data,(address,port))):
            data = file.read(51200)
        # archivo de 100MB sleep en 0.001 dura 31 segundos en 1 cliente, en 250mb aun no se 
        time.sleep(0.000001)
    file.close()
    end=time.time()
    total=end-start
    udpsocket.close()
    log("Server: elapsed time to transfer using UDP a file from "+str(sock.getsockname())+" to client #"+str(client)+" with address: "+str(address)+" :"+str(total)+"seconds")

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
        self.clientudpaddr=""
        self.availableaddress= threading.Event()
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
            if message.lower().startswith("udpaddr:"):
                self.clientudpaddr=message.split(":")[1]+":"+message.split(":")[2]
                self.availableaddress.set()
            if message.lower() == "exit":
                sendData(self.sock,"exit".encode("utf-8"),self.id)
                break
            elif message.lower() == "ready":
                log("client #"+str(self.id)+" is ready to get a file")
                self.ready=True
                send="Filename: "+testfile.name
                msgsend=send.encode("utf-8")
                log("sending client #"+str(self.id)+" file data")
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
            th = Thread(target=sendFile(sock=clients[i].sock,filename=pFilename,client=clients[i].id,clientthread=clients[i]))
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
        log("server : starting file sending test in...")
        time.sleep(0.5)
        log("server : 5")
        time.sleep(0.5)
        log("server : 4")
        time.sleep(0.5)
        log("server : 3")
        time.sleep(0.5)
        log("server : 2")
        time.sleep(0.5)
        log("server : 1")
        time.sleep(0.5)
        sendFileToNClients(int(testclients),testfile)
    if(concurrentConnections==-1):
        break
    log("Cantidad de clientes conectados: "+str(concurrentConnections))
server.close()
