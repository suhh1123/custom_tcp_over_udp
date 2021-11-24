import codecs
import struct
import sys

class segmentProcessor:

    def assemble_segment(self, sourcePort, destPort, sequenceNumber, ackNumber, ack, fin, windowSize, data):
        # construct the rest fields
        headerLength = 20
        flags = (ack << 4) + fin
        checksum = 0
        urgPointer = 0

        # assemble raw segment (currently checksum == 0)
        raw_header = struct.pack('!HHIIBBHHH', sourcePort, destPort, sequenceNumber, ackNumber, headerLength, flags, windowSize, checksum, urgPointer)
        raw_segment = raw_header + bytes(data, encoding="UTF-16")

        # calculate checksum
        decoded_msg = codecs.decode(raw_segment, encoding="UTF-16")
        checksum = self.calculateCheckSum(decoded_msg)

        # reassemble raw segment (current checksum is calculated)
        full_header = struct.pack("!HHIIBBHHH", sourcePort, destPort, sequenceNumber, ackNumber, headerLength, flags, windowSize, checksum, urgPointer)
        full_segment = full_header + bytes(data, encoding="UTF-16")

        return full_segment

    def disassemble_segment(self, segment):
        # separate the header and payload in the segment
        header = segment[:20]
        data = segment[20:]

        # fetch out the header fields from the received segment
        sourcePort, destPort, sequenceNumber, ackNumber, headerLength, flags, windowSize, checkSum, urgPointer = struct.unpack("!HHIIBBHHH", header)
        ack = 1 if (flags >> 4) == 1 else 0
        fin = 1 if flags & 0xff == 1 else 0

        # fetch out the data from the segment
        data = codecs.decode(data, encoding="UTF-16")
        return sourcePort, destPort, sequenceNumber, ackNumber, headerLength, ack, fin, checkSum, data

    def calculateCheckSum(self, msg):
        checksum = 0
        for i in range(0, len(msg) - 1, 2):
            current = (ord(msg[i]) << 8) + (ord(msg[i + 1]))
            checksum = checksum + current
            checksum = (checksum >> 16) + (checksum & 0xffff)
        checksum = ~checksum & 0xffff

        return checksum

# test
if __name__ == '__main__':
    processor = segmentProcessor()

    segment = processor.assemble_segment(80, 50, 1, 2, 0, 1, 512, "Hello World")
    print("The byte stream representation of the segment:")
    print(segment)
    print()

    sourcePort, destPort, sequenceNumber, ackNumber, headerLength, ack, fin, checkSum, data = processor.disassemble_segment(segment)
    print("The header fields parsed from the byte stream:")
    print(sourcePort, destPort, sequenceNumber, ackNumber, headerLength, ack, fin, checkSum, data)
    print()

    msg = codecs.decode(segment, encoding="UTF-16")
    print("The checksum for the full byte stream:")
    print(processor.calculateCheckSum(msg))










