import socket
import struct


def receiveInt(socket):
    return struct.unpack('I', socket.recv(4))[0]

def receiveFloat(socket):
    return struct.unpack('f', socket.recv(4))[0]

if __name__ == '__main__':
    socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket.connect(('127.0.0.1', 1234))
    while True:
        hand = receiveInt(socket)
        x = receiveFloat(socket)
        y = receiveFloat(socket)
        print(hand, x, y, flush=True)
        '''
        personNum = receiveInt(socket)
        print(personNum, flush=True)
        for i in range(personNum):
            keypointsNum = receiveInt(socket)
            print(keypointsNum, flush=True)
            for j in range(keypointsNum):
                x = receiveFloat(socket)
                y = receiveFloat(socket)
                z = receiveFloat(socket)
                print(x, y, z, flush=True)

        '''