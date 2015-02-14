#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  GUI.py
#  
#  Copyright 2014 Enrico Polesel <saggiopol@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

import sys
#import serial
import socket
import os
import time
import select
import threading

import glob

from gi.repository import Gtk 

from gi.repository import GObject
GObject.threads_init()

sys.path.insert(0,"..")

from opcodes import *

from core import SubottoCore
from data import Session, Team, Player, Match, PlayerMatch, Event, Base, AdvantagePhase

#from subotto_serial import SubottoSerial

#TEST_MODE = 2
#SLAVE_MODE = 1
#MASTER_MODE = 0



# This class contains the functions to communicate with the arduino in the Subotto
class ArdCon():

    BUFFER_RCV_LENGTH = 2
    TIMEOUT = 0.001


    # Initialize with socket
    def __init__(self,sock,debugLog):
        self.s = sock
        self.debugLog = debugLog
        self.debugLog("Creating ac class")


    # Send an int to the Arduino
    def sendNumber(self,num):
        self.s.send(chr(num))
    

    # Elaborate the data received from arduino
    def dataFromBuff(self,rcv):
        rcv = map(ord, rcv)
        score = ((rcv[0] & 0xF)<<8) + rcv[1]
        team = "BLUE" if rcv[0] & 0x80 else "RED"
        return {
            "score": score,
            "team": team,
            "event": EVENTS[(rcv[0] & 0x70) >> 4]
        }

    # Receive data from Arduino; return false as the second element if the socket is closed
    def receiveData(self):
        try:
            rlist, _, _ = select.select([self.s], [], [], self.TIMEOUT)
        except:
            self.debugLog ("Socket closed.")
            return (None,False)
        if rlist:
            try:
                rcv = self.s.recv(self.BUFFER_RCV_LENGTH)
                while len(rcv) < self.BUFFER_RCV_LENGTH:
                    rcv += self.s.recv(self.BUFFER_RCV_LENGTH)
                    return (self.dataFromBuff(rcv),True)
            except:
                self.debugLog ("Socket closed.")
                return (None,False)
        else:
            return (None,True)

    # Send a score change message to the Arduino
    def sendMessage (self, team, score_change ):
        if team == "RED":
            msg = 0
        else:
            msg = 2
        if score_change > 0:
            msg += 1
        else:
            score_change = - score_change
        for i in range(score_change):
            self.sendNumber(msg)
        
    # Asks Arduino the score
    def askData(self,team):
        if team == "RED":
            self.sendNumber(0x4)
        else:
            self.sendNumber(0x6)
        data = self.ac.receiveData()
        if data["event"] != "VOID":
            self.debugLog("ERROR: non void event received")
        return data



# This class contains the implementation of the interface
class Interface:

    connected = False
    toDisconnect = False
    score = [0, 0]
    cached_score = [None, None]

    def __init__(self):
        filename = "main.glade"
        self.builder = Gtk.Builder()
        self.builder.add_from_file(filename)
        self.builder.connect_signals(self)

        self.mainWindow = self.builder.get_object("mainWindow")
        self.connectionWindow = self.builder.get_object("connectionWindow")
        self.debugConsole = Gtk.ListStore(str)
        self.consoleView = self.builder.get_object("console")
        self.consoleView.set_model(self.debugConsole)
        self.consoleView.insert_column(Gtk.TreeViewColumn("Debug Log", Gtk.CellRendererText(), text=0),0)
       
        GObject.timeout_add(300, self.loopFunction)
        self.core = SubottoCore(int(sys.argv[1]))
        

    # the function that keeps controlling the sensors
    def run(self):
        try:
            while self.connected:
                time.sleep(0)
                self.ac.debugLog("Connected!")
                (rcv,isSocketOpen) = self.ac.receiveData()
                if (isSocketOpen) and (rcv != None):
                    self.ac.debugLog(str(rcv))
            self.connect = False
            self.toDisconnect = True
        except:
            self.connect = False
            self.toDisconnect = True


    def debugLog(self,string):
        self.debugConsole.append([string])


    def onSizeAllocate(self,*args):
        adj = self.consoleView.get_vadjustment()
        adj.set_value( adj.get_upper() - adj.get_page_size())


    def onConnection(self,*args):
        if not self.connected:    
            try:
                self.debugLog("Getting data..")
                TCP_IP = self.builder.get_object("tcpipText").get_text()
                TCP_PORT = int(self.builder.get_object("tcpportText").get_text())
                PWD = self.builder.get_object("pwdText").get_text()
                self.debugLog("Connecting to socket...")
                self.debugLog("TCP_IP: " + TCP_IP)
                self.debugLog("TCP_PORT: " + str(TCP_PORT))
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.connect((TCP_IP, TCP_PORT))
                self.debugLog("Connected!")
                self.s.send(PWD)
                self.connected = True
                self.ac = ArdCon(self.s,self.debugLog)
                self.controlThread = threading.Thread(target=self.run)
                self.controlThread.start()
                self.connectionWindow.hide()
            except:
                self.debugLog("Connection failed\n")
            else:
                self.connected = True
                self.debugLog("Connection successful\n")
            
    
    def disconnect(self,*args):
        self.toDisconnect = False
        if self.connected:
            self.s.close()
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connectionWindow.show()
            self.connected = False
            self.debugLog("Disconnected\n")
    
    def onDestroyWindow(self,*args):
        try:
            del(self.ac)
            disconnect()
        except:
            pass
        sys.exit(0)


    def loopFunction(self,*args):
        if self.connected:
            self.controlScore()
        elif self.toDisconnect:
            self.disconnect()
        else:
            self.debugLog("Not connected")
        self.core.update()
        return True



    def controlScore(self):
        (rcv,isSocketOpen) = self.ac.receiveData()
        if not isSocketOpen:
            self.disconnect()
        if rcv != None:
            debugLog(str(rcv))
            self.updateScore(rcv)


    def updateScore(self,rcv):
        ## DA DEFINIRE
        debugLog("Sono le 3 e mezza di notte, lo finirò domani...")



    def ask_test(self,*args):
        self.debugLog("ask_test: da implementare")


    def getScore(self,*args):
        self.core.update()
        for i in [0, 1]:
            self.cached_score[i] = self.core.score[self.core.detect_team(self.core.order[i])]
            self.cached_score[i] = self.score[i]
        self.cache_to_entry()
        self.cache_to_display()
    


def main():
    app = Interface()

    mainWindow = app.builder.get_object("mainWindow")
    mainWindow.show_all()
    connectionWindow = app.builder.get_object("connectionWindow")
    connectionWindow.show_all()

    Gtk.main()
    
    return 0

if __name__ == '__main__':
    main()
