#Author: Samatha Kolagatla
#UNCC ID:800864273
import os
import select
import socket
import struct
import sys
import time

ICMP_ECHO_REQUEST = 8


def checksum(str):

    csum = 0
    CountTo = (len(str) / 2) * 2
	
    for count in xrange(0, CountTo, 2):
        thisVal = ord(str[count + 1]) * 256 + ord(str[count])
        csum = csum + thisVal
        csum = csum & 0xffffffffL

    if CountTo < len(str):
        csum = csum + ord(str[len(str) - 1])
        csum = csum & 0xffffffffL

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff

    answer = answer >> 8 | (answer << 8 & 0xff00)

    return answer


def receiveOnePing(mySocket, ID, timeout):
    timeLeft = timeout
    while True:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []:
            return "Request timed out."

        timeReceived = time.time()
        receivedPacket, addr = mySocket.recvfrom(1024)
        icmp_header = receivedPacket[20:28]
        type, code, checksum, packet_ID, sequence = struct.unpack(
            "bbHHh", icmp_header
        )
        if packet_ID == ID:
            bytes = struct.calcsize("d")
            timeSent = struct.unpack("d", receivedPacket[28:28 + bytes])[0]
            return timeReceived - timeSent

        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return "Request timed out."


def sendOnePing(mySocket, destAddr, ID, packet_size):
    destAddr  =  socket.gethostbyname(destAddr)

    packet_size = packet_size - 8

    # Header is type (8), code (8), checksum (16), ID (16), sequence (16)
    myChecksum = 0

    # Make a dummy header with a 0 checksum.
	# struct -- Interpret strings as packed binary data
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    bytes = struct.calcsize("d")
    data = (packet_size - bytes) * "Q"
    data = struct.pack("d", time.time()) + data

    # Calculate the checksum on the data and the dummy header.
    myChecksum = checksum(header + data)

	# Get the right checksum, and put in the header
    header = struct.pack(
        "bbHHh", ICMP_ECHO_REQUEST, 0, socket.htons(myChecksum), ID, 1
    )
    packet = header + data
    mySocket.sendto(packet, (destAddr, 1)) # AF_INET address must be tuple, not str
	#Both LISTS and TUPLES consist of a number of objects
	#which can be referenced by their position number within the object


def doOnePing(destAddr, timeout, packet_size):
    icmp = socket.getprotobyname("icmp")
    try:
        mySocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
    except socket.error, (errno, msg):
        if errno == 1:
            # Operation not permitted
            msg = msg + (
                " - Note that ICMP messages can only be sent from processes"
                " running as root."
            )
            raise socket.error(msg)
        raise # raise the original error

    myID = os.getpid() & 0xFFFF

    sendOnePing(mySocket, destAddr, myID, packet_size)
    delay = receiveOnePing(mySocket, myID, timeout)

    mySocket.close()
    return delay


def ping(destAddr, timeout = 1, count = 5, packet_size = 64):
	#timeout=1 means: If one second goes by without a reply from the server,
    for i in xrange(count):
        print "pinging %s using Python:" % destAddr,
        try:
            delay  =  doOnePing(destAddr, timeout, packet_size)
        except socket.gaierror, e:
            print "failed. (socket error: '%s')" % e[1]
            break

        if delay  ==  None:
            print "failed. (timeout within %ssec.)" % timeout
        else:
            delay  =  delay * 1000
            print "get ping in %0.4fms" % delay


if __name__ == '__main__':

	ping("yahoo.com")