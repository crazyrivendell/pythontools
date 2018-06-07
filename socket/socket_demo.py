# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import time
import socket
import select



class NewSocket(object):
    def __init__(self, protocol, ip, port):
        self.protocol = protocol
        self.ip = ip
        self.port = port

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) if self.protocol.upper() == "TCP"\
            else socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def __str__(self):
        return self.__class__.__name__ + "{" + str(self.task) + "}"

    def run_server(self):
        self.socket.bind((self.ip, self.port))
        self.socket.listen(1)
        while True:
            conn, addr = self.socket.accept()  # connection and ip address
            print('connected by', addr)
            while True:
                data = conn.recv(1024)
                print("receive from %s:%s" % (addr, data))
                conn.sendall("server receive your messages, good bye.")
                conn.close()
                break

    def build_client(self):
        address = (self.ip, self.port)
        self.socket.connect(address)

    def send(self, buf):
        try:
            self.socket.sendall(buf)
        except socket.error:
            print("socket die")
            return

    def receive(self):
        pass

    def close(self):
        self.socket.close()

import time
if __name__ == '__main__':
    s = NewSocket("TCP", "192.168.50.78", 8000)
    s.build_client()
    buf = "%x".format(0)
    s.send(buf.encode("utf-8"))
    s.close()
    # for i in range(100):
    #     s = NewSocket("TCP", "192.168.50.78", 8000)
    #     s.build_client()
    #     if i % 2 == 0:
    #         s.send(b"\x00")
    #     else:
    #         s.send(b"\x01")
    #
    #     # if i % 18 == 0:
    #     #     s.send(b"\x00")
    #     # elif i % 18 == 1:
    #     #     s.send(b"\x01")
    #     # elif i % 18 == 2:
    #     #     s.send(b"\x02")
    #     # elif i % 18 == 3:
    #     #     s.send(b"\x03")
    #     # elif i % 18 == 4:
    #     #     s.send(b"\x04")
    #     # elif i % 18 == 5:
    #     #     s.send(b"\x05")
    #     # elif i % 18 == 6:
    #     #     s.send(b"\x06")
    #     # elif i % 18 == 7:
    #     #     s.send(b"\x07")
    #     # elif i % 18 == 8:
    #     #     s.send(b"\x08")
    #     # elif i % 18 == 9:
    #     #     s.send(b"\x09")
    #     # elif i % 18 == 10:
    #     #     s.send(b"\x0a")
    #     # elif i % 18 == 11:
    #     #     s.send(b"\x0b")
    #     # elif i % 18 == 12:
    #     #     s.send(b"\x0c")
    #     # elif i % 18 == 13:
    #     #     s.send(b"\x0d")
    #     # elif i % 18 == 14:
    #     #     s.send(b"\x0e")
    #
    #     s.close()
    #     time.sleep(0.08)

