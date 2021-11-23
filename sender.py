import socket
import sys
from socket import *

class TCPClient:
    def __init__(self, sourceFile, udplIP, udplPort, windowSizeInByte, ackPort):
        self.buffer = []
        self.MSS = 512
        self.headerSize = 20

        self.sourceFile = sourceFile
        self.udplIP = udplIP
        self.udplPort = udplPort
        self.windowSizeInByte = windowSizeInByte
        self.windowSizeInCount = windowSizeInByte // (self.MSS + self.headerSize)
        self.ackPort = ackPort

    def initiateCommunication(self):
        # initiate UDP sockets for sending segments and receiving ACKs
        sendSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ackSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ackSocket.bind((socket.gethostname(), self.ackPort))

        # parse the source file to the TCP client side buffer
        try:
            file = open(self.sourceFile, 'r')
        except IOError:
            print("Source file does not exist")
            sendSocket.close()
            ackSocket.close()
            sys.exit()
        self.readInBuffer(file)

    # def readInBuffer(self, file):















if __name__ == '__main__':
    client = TCPClient()
    client.initiateCommunication()