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
import socket
import os
import time
import select
#import threading
import traceback

#import glob

from gi.repository import Gtk, GObject, GLib
#GObject.threads_init()

sys.path.insert(0,"..")

#from opcodes import *

from core import SubottoCore
from data import Session, Team, Player, Match, PlayerMatch, Event, Base, AdvantagePhase




# This class contains the functions to communicate with the arduino in the Subotto
class ArdCon():

    BUFFER_RCV_LENGTH = 2
    TIMEOUT = 0.001
    ARD_TEAM = ["RED", "BLUE"]
    EVENT = ["VOID", "GOAL", "SUPERGOAL", "PLUS_ONE", "MINUS_ONE"]
    CORE_EVENT = {
        "RED":{
            "VOID":None,
            "GOAL":Event.EV_SOURCE_CELL_RED_PLAIN,
            "SUPERGOAL":Event.EV_SOURCE_CELL_RED_SUPER,
            "PLUS_ONE":Event.EV_SOURCE_BUTTON_RED_GOAL,
            "MINUS_ONE":Event.EV_SOURCE_BUTTON_RED_UNDO
        },
        "BLUE":{
            "VOID":None,
            "GOAL":Event.EV_SOURCE_CELL_BLUE_PLAIN,
            "SUPERGOAL":Event.EV_SOURCE_CELL_BLUE_SUPER,
            "PLUS_ONE":Event.EV_SOURCE_BUTTON_BLUE_GOAL,
            "MINUS_ONE":Event.EV_SOURCE_BUTTON_BLUE_UNDO
        }
    }
    UNDO_EVENT = [CORE_EVENT[team]["MINUS_ONE"] for team in ARD_TEAM]


    # Initialize with socket
    def __init__(self,sock,debugLog):
        self.s = sock
        self.debugLog = debugLog
        self.ATC_SIGNAL = {
            "score": lambda msg: ((msg[0] & 0xF)<<8) + msg[1],
            "team": lambda msg: "BLUE" if msg[0] & 0x80 else "RED",
            "event": lambda msg: self.EVENT[(msg[0] & 0x70) >> 4]
        }
        self.CTA_SIGNAL = {
            "askData": lambda team: self.sendNumber(64) if team == "RED" else self.sendNumber(192)
        }


    # Send an int to the Arduino
    def sendNumber(self,num):
        self.s.send(chr(num))
    

    # Elaborate the data received from arduino
    def dataFromBuff(self,rcv):
        rcv = map(ord, rcv)
        return {
            "score": self.ATC_SIGNAL["score"](rcv),
            "team": self.ATC_SIGNAL["team"](rcv),
            "event": self.ATC_SIGNAL["event"](rcv)
        }

    # Receive data from Arduino; return false as the second element if the socket is closed
    def receiveData(self):
        rlist, _, _ = select.select([self.s], [], [], 0)
        if len(rlist):
            rcv = ""
            while len(rcv) < self.BUFFER_RCV_LENGTH:
                rcv += self.s.recv(self.BUFFER_RCV_LENGTH - len(rcv))
            return self.dataFromBuff(rcv)
        return None

    # Send a score change command to the Arduino
    def sendScoreCommand (self, team, score_change ):
        if team == "RED":
            baseMsg = 0
        else:
            baseMsg = 128
        if score_change < 0:
            baseMsg += 32
            score_change = - score_change
        i = 0
        while score_change != 0:
            if score_change & 1:
                self.sendNumber(baseMsg + i)
            score_change = score_change >> 1
            i += 1
    
    # Send a sensor activation/deactivation command to the arduino
    def sendSensorCommand (self, team, event, toActivate):
        if team == "RED":
            baseMsg = 72
        else:
            baseMsg = 200
        baseMsg += (self.EVENT.index(event)-1) << 1
        if not toActivate:
            baseMsg += 1
        self.sendNumber(baseMsg)
    
    # Asks Arduino the score
    def askData(self,team):
        self.CTA_SIGNAL["askData"](team)



# This class contains the implementation of the interface
class Interface:

    _numDebugebugLines = 0

    DEVICE = ["arduino","core"]
    MAX_NUM_CONSOLE_ROWS = 100

    connected = False
    toDisconnect = False
    score = {dev:[0,0] for dev in DEVICE}
    lastToScore = {dev:None for dev in DEVICE}


    # === init function ===

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

        self.scoreTextView = {
            "arduino":{"RED":self.builder.get_object("redArduinoScore"),
                       "BLUE":self.builder.get_object("blueArduinoScore")},
            "core":{"RED":self.builder.get_object("redCoreScore"),
                    "BLUE":self.builder.get_object("blueCoreScore")}
        }
        self.lastToScoreBar = {
            "arduino":{"RED":self.builder.get_object("redArduinoLastToScore"),
                       "BLUE":self.builder.get_object("blueArduinoLastToScore")},
            "core":{"RED":self.builder.get_object("redCoreLastToScore"),
                    "BLUE":self.builder.get_object("blueCoreLastToScore")},
        }
        self.sensorSwitch = {
            "RED":{
                "VOID":None,
                "GOAL":self.builder.get_object("redGoalSwitch"),
                "SUPERGOAL":self.builder.get_object("redSupergoalSwitch"),
                "PLUS_ONE":self.builder.get_object("redAddButtonSwitch"),
                "MINUS_ONE":self.builder.get_object("redUndoButtonSwitch")
            },
            "BLUE":{
                "VOID":None,
                "GOAL":self.builder.get_object("blueGoalSwitch"),
                "SUPERGOAL":self.builder.get_object("blueSupergoalSwitch"),
                "PLUS_ONE":self.builder.get_object("blueAddButtonSwitch"),
                "MINUS_ONE":self.builder.get_object("blueUndoButtonSwitch")
            }
        }

        self.core = SubottoCore(int(sys.argv[1]))
        for i in [0,1]:
            self.score["core"][i] = self.getCoreScore(i)
       
        GObject.timeout_add(300, self.loopFunction)
        self.core = SubottoCore(int(sys.argv[1]))


    # === control functions ===

    # write on the console
    def debugLog(self,string):
        self._numDebugebugLines += 1
        self.debugConsole.append([string])
        #if len(self.debugConsole) > self.MAX_NUM_CONSOLE_ROWS:
        #    self.debugConsole.remove(self.debugConsole.get_iter_first())


    # === main loop ===

    def loopFunction(self,*args):
        if self.connected:
            self.updateScore()
        elif self.toDisconnect:
            self.disconnect()
        else:
            self.debugLog("Not connected")
        self.core.update()
        return True


    # === connection/disconnection functions ===

    # connect to socket
    def connect(self):
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
                self.debugLog("Creating arduino controller object...")
                self.ac = ArdCon(self.s,self.debugLog)
                self.debugLog("Arduino controller object Created!")
                self.debugLog("Asking Arduino data...")
                for i in [0,1]:
                    self.getArduinoScore(i)
                self.connectionWindow.hide()
            except:
                traceback.print_exc()
                self.debugLog("Connection failed\n")
            else:
                self.connected = True
                self.debugLog("Connection successful\n")

    # disconnect from socket
    def disconnect(self):
        self.toDisconnect = False
        if self.connected:
            try:
                self.s.close()
            except:
                pass
            self.connectionWindow.show()
            self.connected = False
            self.debugLog("Disconnected\n")


    def readEvents(self):
        try:
            rcv = self.ac.receiveData()
            while rcv is not None:
                self.sendEventToCore(rcv)
                rcv = self.ac.receiveData()
        except:
            traceback.print_exc()
            self.connected = False
            self.toDisconnect = True
            self.debugLog("Disconnected")


    # === update functions ===

    # asks the score to arduino and the core; updates arduino score
    def updateScore(self):
        self.readEvents()
        for i in [0,1]:
            self.score["core"][i] = self.getCoreScore(i)
            if self.score["arduino"][i] == None:
                self.debugLog("Arduino score unknown")
                self.lastToScore["arduino"] = None
            else:
                if self.score["core"][i] != self.score["arduino"][i]:
                    # server takes priority over arduino
                    self.setArduinoScore(i,self.score["core"][i])
                    self.lastToScore["arduino"] = None
            self.updateView(i)

    # update scores on the main window
    def updateView(self,team):
        for dev in self.DEVICE:
            score = self.score[dev][team]
            if score == None:
                self.scoreTextView[dev][self.ac.ARD_TEAM[team]].set_text("Unknown")
            else:
                self.scoreTextView[dev][self.ac.ARD_TEAM[team]].set_text(str(score))
            if self.lastToScore[dev] == team:
                self.lastToScoreBar[dev][self.ac.ARD_TEAM[team]].set_fraction(1)
            else:
                self.lastToScoreBar[dev][self.ac.ARD_TEAM[team]].set_fraction(0)


    # === core communication ===

    # get score from the core
    def getCoreScore(self,i):
        return self.core.score[self.core.detect_team(self.core.order[i])]

    # send an event received from arduino
    def sendEventToCore(self,data):
        team = self.ac.ARD_TEAM.index(data["team"])
        self.score["arduino"][team] = data["score"]
        event = self.ac.CORE_EVENT[data["team"]][data["event"]]
        if event is None:
            pass
        elif event in self.ac.UNDO_EVENT:
            self.core.act_goal_undo(self.core.order[team], event)
        else:
            self.core.act_goal(self.core.order[team], event)
            self.lastToScore["core"] = team
            self.lastToScore["arduino"] = team


    # === arduino communication ===

    # get arduino score
    def getArduinoScore(self,i):
        self.ac.askData(self.ac.ARD_TEAM[i])

    # set arduino score
    def setArduinoScore(self,team,score):
        scoreChange = score - self.score["arduino"][team]
        self.ac.sendScoreCommand(self.ac.ARD_TEAM[team],scoreChange)
        self.getArduinoScore(team)

    
    # === event handlers ===

    # called when the console shows
    def onConsoleShow(self,*args):
        adj = self.consoleView.get_vadjustment()
        adj.set_value( adj.get_page_size() )

    # called when a new line is added to the console
    def onSizeAllocate(self,*args):
        numDebugLines = self._numDebugebugLines
        self._numDebugebugLines = 0
        adj = self.consoleView.get_vadjustment()
        if adj.get_value() >= adj.get_upper() - adj.get_page_size() - numDebugLines * adj.get_step_increment():
            adj.set_value( adj.get_upper() - adj.get_page_size() )

    # called when a switch is switched
    def onSwitchNotify(self,*args):
        if self.connected:
            for team in self.ac.ARD_TEAM:
                for event in self.ac.EVENT:
                    if args[0] == self.sensorSwitch[team][event]:
                        toActivate = self.sensorSwitch[team][event].get_active()
                        self.ac.sendSensorCommand(team,event,toActivate)
                        self.debugLog("switch " + str(team) + " " + str(event) + " was turned " + str(toActivate))

    # called when the connection button is hit
    def onConnection(self,*args):
        self.debugLog("Connecting...")
        self.connect()

    # called when the main window is closed
    def onDestroyWindow(self,*args):
        try:
            del(self.ac)
            disconnect()
        except:
            pass
        sys.exit(0)
    




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
