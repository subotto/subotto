#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import serial
import time

from opcodes import *

class SubottoSerial:

    def __init__(self, port, speed):
        self.port = port
        self.speed = speed
        self.serial = serial.Serial(port=port, baudrate=speed, timeout=None)
        #self.serial.nonblocking()

    # BASIC IO INTERFACE

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

    def send_recv(self, send):
        self.send_number(send)
        return self.recv_number()

    def send_expect(self, send, expect):
        res = self.send_recv(send)
        return res == expect

    # UPPER LEVEL COMMANDS

    def wait_for_ready(self):
        num = self.recv_number()
        return num == SUB_READY

    def request_echo(self):
        return self.send_expect(COM_ECHO_TEST, SUB_ECHO_REPLY)

    def set_slave_mode(self):
        return self.send_expect(COM_SET_SLAVE_MODE, SUB_SLAVE_MODE)

    def set_test_mode(self):
        return self.send_expect(COM_SET_TEST_MODE, SUB_TEST_MODE)


if __name__ == '__main__':
    ss = SubottoSerial('/dev/ttyACM0', 9600)
    # Here we wait for the SUB_READY command, otherwise we risk to
    # send commands before the unit is ready
    print ss.recv_number()

    ss.send_number(255)
    time.sleep(2)
    print ss.has_data()
    print ss.recv_number()
