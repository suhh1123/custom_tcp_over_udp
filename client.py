import datetime
import socket
import sys
import time
from socket import *

from segment_processor import segmentProcessor

class TCPClient(BaseException):
    def __init__(self, sourceFile, udplIP, udplPort, windowSizeInByte, ackPort):
        self.buffer = []
        self.sending_time_cache = []
        self.MSS = 512 # measured in byte, 1 character takes exactly 1 byte
        self.headerSize = 20
        self.sourceFile = sourceFile
        self.logFile = "client_log.txt"
        self.udplIP = udplIP
        self.udplPort = udplPort
        self.windowSizeInByte = windowSizeInByte
        self.windowSizeInCount = windowSizeInByte // self.MSS
        self.ackPort = ackPort
        self.timeoutInterval = 1
        self.estimatedRTT = 1
        self.devRTT = 0

    def initiateCommunication(self):

        # TODO Initiate UDP sockets for sending segments and receiving ACKs
        sendSocket = socket(AF_INET, SOCK_DGRAM)
        ackSocket = socket(AF_INET, SOCK_DGRAM)
        ackSocket.bind(('localhost', self.ackPort))

        # TODO Parse the source file to the client side buffer
        try:
            file = open(self.sourceFile, 'r')
        except IOError:
            print("Source file does not exist")
            sendSocket.close()
            ackSocket.close()
            sys.exit()
        self.readInBuffer(file)

        # TODO Open the client log
        try:
            log = open(self.logFile, 'w')
        except IOError:
            print("Client log does not exist")
            sys.exit()

        # TODO Send segments with timeout mechanism
        processor = segmentProcessor()
        largest_inorder_sequence_number = -1
        leftBound = 0
        rightBound = self.windowSizeInCount - 1

        # Send all segments in the window in a row
        for i in range(leftBound, rightBound + 1):
            if i < len(self.buffer):
                sendSocket.sendto(self.buffer[i], (self.udplIP, self.udplPort))
                self.sending_time_cache.append(time.time())
                # Write sending log
                send_sourcePort, send_destPort, send_sequenceNumber, send_ackNumber, send_headerLength, send_ack, send_fin, send_windowSize, send_checkSum, send_data = processor.disassemble_segment(self.buffer[i])
                self.writeLog(log, "SEND", send_sourcePort, send_destPort, send_sequenceNumber, send_ackNumber, send_headerLength, send_ack, send_fin, send_windowSize, send_checkSum, self.timeoutInterval)

        while largest_inorder_sequence_number < len(self.buffer) - 1:
            try:
                ackSocket.settimeout(self.timeoutInterval)
                while largest_inorder_sequence_number < len(self.buffer) - 1:
                    ackSegment = ackSocket.recv(2048)
                    ack_sourcePort, ack_destPort, ack_sequenceNumber, ack_ackNumber, ack_headerLength, ack_ack, ack_fin, ack_windowSize, ack_checkSum, ack_data = processor.disassemble_segment(ackSegment)
                    if ack_ack == 1 and ack_sequenceNumber == largest_inorder_sequence_number + 1:
                        largest_inorder_sequence_number += 1
                        leftBound += 1
                        rightBound += 1

                        # Update timeout interval, we know the client received an inorder segment, record the current
                        # time, and look for the time when the segment was sent in the sending time cache
                        sendTime = self.sending_time_cache[largest_inorder_sequence_number]
                        ackTime = time.time()
                        sampleRTT = ackTime - sendTime
                        self.estimatedRTT = 0.875 * self.estimatedRTT + 0.125 * sampleRTT
                        self.devRTT = 0.75 * self.devRTT + 0.25 * abs(sampleRTT - self.estimatedRTT)
                        self.timeoutInterval = self.estimatedRTT + 4 * self.devRTT
                        print("ack " + str(largest_inorder_sequence_number) + " received ")

                        # Write receiving log
                        self.writeLog(log, "RECEIVE", ack_sourcePort, ack_destPort, ack_sequenceNumber, ack_ackNumber, ack_headerLength, ack_ack, ack_fin, ack_windowSize, ack_checkSum, self.timeoutInterval)

                        if rightBound < len(self.buffer):
                            ackSocket.sendto(self.buffer[rightBound], (self.udplIP, self.udplPort))
                            self.sending_time_cache.append(time.time())
                            ackSocket.settimeout(self.timeoutInterval)

                            # Write sending log
                            send_sourcePort, send_destPort, send_sequenceNumber, send_ackNumber, send_headerLength, send_ack, send_fin, send_windowSize, send_checkSum, send_data = processor.disassemble_segment(self.buffer[i])
                            self.writeLog(log, "SEND", send_sourcePort, send_destPort, send_sequenceNumber, send_ackNumber, send_headerLength, send_ack, send_fin, send_windowSize, send_checkSum, self.timeoutInterval)
            except timeout:
                for i in range(leftBound, rightBound + 1):
                    if i < len(self.buffer):
                        sendSocket.sendto(self.buffer[i], (self.udplIP, self.udplPort))
                        self.sending_time_cache[i] = time.time()

                        # Write resending log
                        send_sourcePort, send_destPort, send_sequenceNumber, send_ackNumber, send_headerLength, send_ack, send_fin, send_windowSize, send_checkSum, send_data = processor.disassemble_segment(self.buffer[i])
                        self.writeLog(log, "RESEND", send_sourcePort, send_destPort, send_sequenceNumber, send_ackNumber, send_headerLength, send_ack, send_fin, send_windowSize, send_checkSum, self.timeoutInterval)

        # TODO Close sockets
        sendSocket.close()
        ackSocket.close()

    def readInBuffer(self, file):
        processor = segmentProcessor()
        sequenceNumber = 0
        ackNumber = 0

        currentData = file.read(self.MSS)
        while len(currentData) > 0:
            nextData = file.read(self.MSS)
            # If the next data read from the file is empty, that means the current data is the final segment
            if len(nextData) == 0:
                segment = processor.assemble_segment(self.ackPort, self.udplPort, sequenceNumber, ackNumber, 0, 1, self.windowSizeInByte, currentData)
            else:
                segment = processor.assemble_segment(self.ackPort, self.udplPort, sequenceNumber, ackNumber, 0, 0, self.windowSizeInByte, currentData)
            self.buffer.append(segment)
            currentData = nextData
            sequenceNumber += 1
            ackNumber += 1

    def writeLog(self, log, status, sourcePort, destPort, sequenceNumber, ackNumber, headerLength, ack, fin, windowSize, checkSum, timeoutInterval):
        content = "[" + status + " - " + "Time: " + str(datetime.datetime.now()) + " - source port: " + str(sourcePort) + \
                  " - dest port: " + str(destPort) + " - sequence number: " + str(sequenceNumber) + \
                  " - ack number: " + str(ackNumber) + " - header length: " + str(headerLength) + \
                  " - ACK: " + str(ack) + " - FIN: " + str(fin) + " - window size: " + str(windowSize) + \
                  " - checksum: " + str(checkSum)
        if (status == "SEND" or status == "RESEND"):
            content += " - timeout interval: " + str(timeoutInterval)
        content += "]\n"
        log.write(content)

# test
if __name__ == '__main__':
    try:
        sourceFile = sys.argv[1]
        udplIP = sys.argv[2]
        udplPort = int(sys.argv[3])
        windowSizeInByte = int(sys.argv[4])
        ackPort = int(sys.argv[5])
    except IndexError:
        exit("Please type: python3 client.py [filename] [adress_of_udpl] [port_number_of_udpl] [windowsize] [ack_port_number]")

    # sourceFile = "source_file.txt"
    # udplIP = "localhost"
    # udplPort = 41192
    # windowSizeInByte = 1536
    # ackPort = 9000

    client = TCPClient(sourceFile, udplIP, udplPort, windowSizeInByte, ackPort)
    client.initiateCommunication()