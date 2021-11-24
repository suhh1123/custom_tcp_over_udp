import codecs
import socket
import struct
import sys
from socket import *

from segmentProcessor import segmentProcessor


class TCPServer:
    def __init__(self, destFile, listeningPort, ackIP, ackPort):
        self.destFile = destFile
        self.listeningPort = listeningPort
        self.ackIP = ackIP
        self.ackPort = ackPort

    def initiateCommunication(self):
        # initiate UDP sockets for receiving segments and sending ACKs
        receiveSocket = socket(AF_INET, SOCK_DGRAM)
        receiveSocket.bind(('localhost', self.listeningPort))
        ackSocket = socket(AF_INET, SOCK_DGRAM)

        # build tunnel to destination file
        try:
            file = open(self.destFile, 'w')
        except IOError:
            print("Destination file does not exist")
            receiveSocket.close()
            ackSocket.close()
            sys.exit()

        # receive segment and send ACK
        processor = segmentProcessor()
        largest_inorder_sequence_number = -1

        while True:
            segment, clientAddress = receiveSocket.recvfrom(2048)

            if segment:
                # disassemble the received segment
                sourcePort, destPort, sequenceNumber, ackNumber, headerLength, ack, fin, checkSum, data = processor.disassemble_segment(segment)

                headerLength = 20
                flags = (ack << 4) + fin
                checksum = 0
                urgPointer = 0
                windowSize = 32
                raw_header = struct.pack('!HHIIBBHHH', sourcePort, destPort, sequenceNumber, ackNumber, headerLength, flags, windowSize, 0, urgPointer)
                raw_segment = raw_header + codecs.encode(data, encoding="UTF-16")
                decoded_msg = codecs.decode(raw_segment, encoding="UTF-16")

                # check if segment has been corrupted
                if (processor.calculateCheckSum(decoded_msg) == checkSum):

                    if (sequenceNumber == largest_inorder_sequence_number + 1):
                        if fin:
                            file.write(data.rstrip(' \t\r\n\0'))
                        else:
                            file.write(data)

                        largest_inorder_sequence_number += 1
                        ackSegment = processor.assemble_segment(self.listeningPort, self.ackPort, largest_inorder_sequence_number, largest_inorder_sequence_number + 1, 1, 0, 0, "")
                        ackSocket.sendto(ackSegment, (self.ackIP, self.ackPort))

if __name__ == '__main__':
    # try:
    #     destFile = sys.argv[1]
    #     listeningPort = int(sys.argv[2])
    #     ackIP = sys.argv[3]
    #     ackPort = int(sys.argv[4])
    # except IndexError:
    #    exit("Please type: $ receiver.py [receiving_filename] [listening_port] [sender_IP] [sender_port] [log_filename] ")

    destFile = "dest_file.txt"
    listeningPort = 8000
    ackIP = "localhost"
    ackPort = 9000

    server = TCPServer(destFile, listeningPort, ackIP, ackPort)
    server.initiateCommunication()








