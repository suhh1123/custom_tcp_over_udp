import codecs
import socket
import struct
import sys
import datetime
from socket import *

from segmentProcessor import segmentProcessor


class TCPServer:
    def __init__(self, destFile, listeningPort, ackIP, ackPort):
        self.destFile = destFile
        self.logFile = "server_log.txt"
        self.listeningPort = listeningPort
        self.ackIP = ackIP
        self.ackPort = ackPort

    def initiateCommunication(self):
        # TODO: Initiate UDP sockets for receiving segments and sending ACKs
        receiveSocket = socket(AF_INET, SOCK_DGRAM)
        receiveSocket.bind(('localhost', self.listeningPort))
        ackSocket = socket(AF_INET, SOCK_DGRAM)

        # TODO Open the destination file
        try:
            file = open(self.destFile, 'w')
        except IOError:
            print("Destination file does not exist")
            receiveSocket.close()
            ackSocket.close()
            sys.exit()

        # TODO Open the server log
        try:
            log = open(self.logFile, 'w')
        except IOError:
            print("Server log does not exist")
            sys.exit()

        # TODO Receive segment and send ACK
        processor = segmentProcessor()
        largest_inorder_sequence_number = -1
        flag = True

        while flag:
            segment, clientAddress = receiveSocket.recvfrom(2048)

            if segment:
                # Disassemble the received segment
                sourcePort, destPort, sequenceNumber, ackNumber, headerLength, ack, fin, windowSize, checkSum, data = processor.disassemble_segment(segment)

                # Reversed engineer, calculating the checksum on the entire segment with checksum not equal to 0
                # somehow throws exception
                headerLength = 20
                flags = (ack << 4) + fin
                urgPointer = 0
                raw_header = struct.pack('!HHIIBBHHH', sourcePort, destPort, sequenceNumber, ackNumber, headerLength, flags, windowSize, 0, urgPointer)
                raw_segment = raw_header + codecs.encode(data, encoding="UTF-16")
                decoded_msg = codecs.decode(raw_segment, encoding="UTF-16")

                # Check if segment has been corrupted and received in order
                if (processor.calculateCheckSum(decoded_msg) == checkSum and sequenceNumber == largest_inorder_sequence_number + 1):
                    if fin:
                        file.write(data.rstrip(' \t\r\n\0'))
                        flag = False
                    else:
                        file.write(data)

                    largest_inorder_sequence_number += 1
                    ackSegment = processor.assemble_segment(self.listeningPort, self.ackPort, largest_inorder_sequence_number, largest_inorder_sequence_number + 1, 1, 0, windowSize, "")
                    ackSocket.sendto(ackSegment, (self.ackIP, self.ackPort))

                    # Write receiving log
                    self.writeLog(log, "RECEIVE", sourcePort, destPort, sequenceNumber, ackNumber, headerLength, ack, fin, windowSize, checkSum)

                    # Write sending log
                    send_sourcePort, send_destPort, send_sequenceNumber, send_ackNumber, send_headerLength, send_ack, send_fin, send_windowSize, send_checkSum, send_data = processor.disassemble_segment(ackSegment)
                    self.writeLog(log, "SEND", send_sourcePort, send_destPort, send_sequenceNumber, send_ackNumber, send_headerLength, send_ack, send_fin, send_windowSize, send_checkSum)

        # TODO Close sockets
        receiveSocket.close()
        ackSocket.close()

    def writeLog(self, log, status, sourcePort, destPort, sequenceNumber, ackNumber, headerLength, ack, fin, windowSize, checkSum):
        content = "[" + status + " - " + "Time: " + str(datetime.datetime.now()) + " - source port: " + str(sourcePort) + \
                  " - dest port: " + str(destPort) + " - sequence number: " + str(sequenceNumber) + \
                  " - ack number: " + str(ackNumber) + " - header length: " + str(headerLength) + \
                  " - ACK: " + str(ack) + " - FIN: " + str(fin) + " - window size: " + str(windowSize) + \
                  " - checksum: " + str(checkSum) + "]\n"
        log.write(content)

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








