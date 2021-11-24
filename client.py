import socket
import sys
from socket import *

from segmentProcessor import segmentProcessor

class TCPClient(BaseException):
    def __init__(self, sourceFile, udplIP, udplPort, windowSizeInByte, ackPort):
        self.buffer = []
        self.MSS = 8 # measured in byte, 1 character takes exactly 1 byte
        self.headerSize = 20

        self.sourceFile = sourceFile
        self.udplIP = udplIP
        self.udplPort = udplPort
        self.windowSizeInByte = windowSizeInByte
        self.windowSizeInCount = windowSizeInByte // self.MSS
        self.ackPort = ackPort

        self.timeoutInterval = 100
        self.estimatedRTT = 0.5
        self.devRTT = 0

    def initiateCommunication(self):
        # initiate UDP sockets for sending segments and receiving ACKs
        sendSocket = socket(AF_INET, SOCK_DGRAM)
        ackSocket = socket(AF_INET, SOCK_DGRAM)
        ackSocket.bind(('localhost', self.ackPort))

        # parse the source file to the TCP client side buffer
        try:
            file = open(self.sourceFile, 'r')
        except IOError:
            print("Source file does not exist")
            sendSocket.close()
            ackSocket.close()
            sys.exit()
        self.readInBuffer(file)

        # send segments with timeout mechanism (fixed timeout interval for now)
        processor = segmentProcessor()
        largest_inorder_sequence_number = -1
        leftBound = 0
        rightBound = self.windowSizeInCount - 1
        for i in range(leftBound, rightBound + 1):
            sendSocket.sendto(self.buffer[i], (self.udplIP, self.udplPort))

        while largest_inorder_sequence_number < len(self.buffer) - 1:
            try:
                ackSocket.settimeout(self.timeoutInterval)
                while largest_inorder_sequence_number < len(self.buffer) - 1:
                    ackSegment = ackSocket.recv(2048)
                    sourcePort, destPort, sequenceNumber, ackNumber, headerLength, ack, fin, windowSize, checkSum, data = processor.disassemble_segment(
                        ackSegment)
                    if ack == 1 and sequenceNumber == largest_inorder_sequence_number + 1:
                        largest_inorder_sequence_number += 1
                        leftBound += 1
                        rightBound += 1
                        if rightBound < len(self.buffer):
                            ackSocket.sendto(self.buffer[rightBound], (self.udplIP, self.udplPort))
                        ackSocket.settimeout(self.timeoutInterval)
            except timeout:
                for i in range(leftBound, rightBound + 1):
                    if i < len(self.buffer):
                        sendSocket.sendto(self.buffer[i], (self.udplIP, self.udplPort))

        # close sockets
        sendSocket.close()
        ackSocket.close()

    def readInBuffer(self, file):
        processor = segmentProcessor()
        sequenceNumber = 0
        ackNumber = 0

        currentData = file.read(self.MSS)
        while len(currentData) > 0:
            nextData = file.read(self.MSS)
            # if the next data read from the file is empty, that means the current data is the final segment
            if len(nextData) == 0:
                segment = processor.assemble_segment(self.ackPort, self.udplPort, sequenceNumber, ackNumber, 0, 1, self.windowSizeInByte, currentData)
            else:
                segment = processor.assemble_segment(self.ackPort, self.udplPort, sequenceNumber, ackNumber, 0, 0, self.windowSizeInByte, currentData)
            self.buffer.append(segment)
            currentData = nextData
            sequenceNumber += 1
            ackNumber += 1

# test
if __name__ == '__main__':
    # try:
    #     sourceFile = sys.argv[1]
    #     udplIP = sys.argv[2]
    #     udplPort = int(sys.argv[3])
    #     windowSizeInByte = int(sys.argv[4])
    #     ackPort = int(sys.argv[5])
    # except IndexError:
    #     exit("Please type: $ client.py [sending_filename] [remote_IP] [remote_port] [ack_port] [log_filename] [window_size]")

    sourceFile = "source_file.txt"
    udplIP = "localhost"
    udplPort = 41192
    windowSizeInByte = 32
    ackPort = 9000

    client = TCPClient(sourceFile, udplIP, udplPort, windowSizeInByte, ackPort)
    client.initiateCommunication()

    processor = segmentProcessor()
    for i in range(0, len(client.buffer)):
        print(client.buffer[i])
        sourcePort, destPort, sequenceNumber, ackNumber, headerLength, ack, fin, windowSize, checkSum, data = processor.disassemble_segment(
            client.buffer[i])
        print(sourcePort, destPort, sequenceNumber, ackNumber, headerLength, ack, fin, windowSize, checkSum, data)
        print()