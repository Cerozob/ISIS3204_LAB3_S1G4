import sys
import socket
import logging
import os
import time
from threading import Thread
import hashlib
import sys

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