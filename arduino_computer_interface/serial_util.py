#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import serial
import time

class SubottoSerial:

    def __init__(self, port, speed):
        self.port = port
        self.speed = speed
        self.serial = serial.Serial(port=port, baudrate=speed, timeout=None)
        #self.serial.nonblocking()

    def send_number(self, num):
        print >> sys.stderr, "> TO SERIAL PORT: %d" % (num)
        self.serial.write("%d" % (num))
        self.serial.flush()

    def recv_number(self):
        num = int(self.serial.readline().strip())
        print >> sys.stderr, "> FROM SERIAL PORT: %d" % (num)
        return num

    def has_data(self):
        return self.serial.inWaiting() > 0


if __name__ == '__main__':
    ss = SubottoSerial('/dev/ttyACM0', 9600)
    print ss.recv_number()
    ss.send_number(255)
    time.sleep(2)
    print ss.has_data()
    print ss.recv_number()
