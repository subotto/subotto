#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import serial
import time

from opcodes import *

class SubottoSerial:

    # These codes are received asynchronously, i.e., even if they
    # weren't solicited by the host
    ASYNC_CODES = set([SUB_PHOTO_RED_NORMAL,
                       SUB_PHOTO_RED_SUPER,
                       SUB_PHOTO_BLUE_NORMAL,
                       SUB_PHOTO_BLUE_SUPER,
                       SUB_BUTTON_RED_GOAL,
                       SUB_BUTTON_RED_UNDO,
                       SUB_BUTTON_BLUE_GOAL,
                       SUB_BUTTON_BLUE_UNDO])

    def __init__(self, port, speed):
        self.port = port
        self.speed = speed
        self.serial = serial.Serial(port=port, baudrate=speed, timeout=None)
        self.events = []

        #self.serial.nonblocking()

    # BASIC IO INTERFACE

    def send_number(self, num):
        print >> sys.stderr, "> TO SERIAL PORT: %d" % (num)
        self.serial.write("%d" % (num))
        self.serial.flush()

    def recv_number(self):
        str_num = self.serial.readline().strip()
        print >> sys.stderr, "> FROM SERIAL PORT: %s" % (str_num)
        num = int(str_num)
        return num

    def recv_sync_number(self):
        while True:
            num = self.recv_number()
            if num in self.ASYNC_CODES:
                self.events.append(num)
            else:
                return num

    def has_data(self):
        return self.serial.inWaiting() > 0

    def send_recv(self, send):
        self.send_number(send)
        return self.recv_sync_number()

    def send_expect(self, send, expect):
        res = self.send_recv(send)
        return res == expect

    # UPPER LEVEL COMMANDS

    # I'm not sure this reset protocol is the best possible, but it
    # works reasonably
    def wait_for_ready(self):
        try:
            num = self.recv_number()
            if num == SUB_READY:
                return True
        except ValueError:
            pass

        self.send_number(COM_RESET)
        attempts = 0
        while True:
            try:
                num = self.recv_number()
            except ValueError:
                pass

            if num == SUB_READY:
                return True

            attempts += 1
            if attempts == 5:
                return False

    def receive_events(self):
        while self.has_data():
            num = self.recv_number()
            if num in self.ASYNC_CODES:
                self.events.append(num)
            else:
                print >> sys.stderr, "> Strange, I received asynchronously a synchronous opcode (%d), I'll ignore it..." % (num)

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
    print ss.wait_for_ready()

    ss.set_slave_mode()
    time.sleep(2)
    ss.receive_events()
