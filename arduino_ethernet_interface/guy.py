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
import threading

import glob

from gi.repository import Gtk 

from gi.repository import GObject
GObject.threads_init()

sys.path.insert(0,"..")

from opcodes import *

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
            "event": lambda msg: EVENT[(msg[0] & 0x70) >> 4]
        }
        self.CTA_SIGNAL = {
            "askData": lambda team: self.sendNumber(0x4) if team == "RED" else self.sendNumber(0x6)
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

    # Send a score change command to the Arduino
    def sendScoreCommand (self, team, score_change ):
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
    
    # Send a sensor activation/deactivation command to the arduino
    def sendSensorCommand (self, team, event, toActivate):
        command = 16
        command += 8 if team =="RED" else 0
        command += self.EVENT.index(event) - 1
        command += 1 if toActivate else 0
        self.sendNumber(command)
    
    # Asks Arduino the score
    def askData(self,team):
        self.CTA_SIGNAL["askData"](team)
        (data,isConnected) = self.receiveData()
        if (not isConnected) or (data == None):
            return None
        if data["event"] != "VOID":
            self.debugLog("ERROR: non void event received from Arduino while asking data")
        return data



# This class contains the implementation of the interface
class Interface:

    _numDebugebugLines = 0

    DEVICE = ["arduino","core"]
    MAX_NUM_CONSOLE_ROWS = 100

    connected = False
    toDisconnect = False
    score = {dev:[0,0] for dev in DEVICE}
    lastToScore = {dev:None for dev in DEVICE}

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
    

    # === core communication ===

    # get score from the core
    def getCoreScore(self,i):
        return self.core.score[self.core.detect_team(self.core.order[i])]

    # send an event received from arduino
    def sendEventToCore(self,data):
        team = self.ac.ARD_TEAM.index(data["team"])
        scoreChange = data["score"] - self.score["arduino"][team]
        self.score["arduino"][team] = data["score"]
        event = self.ac.CORE_EVENT[data["event"]]
        if event == None:
            debugLog("WARNING!!! VOID event received on receiving")
        elif event in self.ac.UNDO_EVENT:
            self.core.act_goal_undo(self.core.order[team], event)
        else:
            self.core.act_goal(self.core.order[team], event)
            self.lastToScore["core"] = team


    # === arduino communication ===

    # get arduino score
    def getArduinoScore(self,i):
        data = self.ac.askData(self.ac.ARD_TEAM[i])
        if data == None:
            self.debugLog("No response from Arduino while asking data")
            return None
        return data["score"]

    # set arduino score
    def setArduinoScore(self,team,score):
        scoreChange = score - self.score["arduino"][team]
        self.ac.sendScoreCommand(self.ac.ARD_TEAM[team],scoreChange)


    # === thread controller ===

    # the function that keeps controlling the sensors
    def run(self):
        try:
            while self.connected:
                time.sleep(0)
                (rcv,isSocketOpen) = self.ac.receiveData()
                if (isSocketOpen) and (rcv != None):
                    self.ac.debugLog("data received:" + str(rcv))
                    data = self.ac.dataFromBuff(rcv)
                    self.sendEventToCore(data)
            self.connect = False
            self.toDisconnect = True
        except:
            self.connect = False
            self.toDisconnect = True

    # === control functions ===

    def debugLog(self,string):
        self._numDebugebugLines += 1
        self.debugConsole.append([string])
        if len(self.debugConsole) > self.MAX_NUM_CONSOLE_ROWS:
            self.debugConsole.remove(self.debugConsole.get_iter_first())


    # === event handlers ===
    def onConsoleShow(self,*args):
        adj = self.consoleView.get_vadjustment()
        adj.set_value( adj.get_page_size() )


    def onSizeAllocate(self,*args):
        numDebugLines = self._numDebugebugLines
        self._numDebugebugLines = 0
        adj = self.consoleView.get_vadjustment()
        if adj.get_value() >= adj.get_upper() - adj.get_page_size() - numDebugLines * adj.get_step_increment():
            adj.set_value( adj.get_upper() - adj.get_page_size() )


    def onSwitchNotify(self,*args):
        if self.connected:
            for team in self.ac.ARD_TEAM:
                for event in self.ac.EVENT:
                    if args[0] == self.sensorSwitch[team][event]:
                        toActivate = self.sensorSwitch[team][event].get_active()
                        self.ac.sendSensorCommand(team,event,toActivate)
                        self.debugLog("switch " + str(team) + " " + str(event) + " was turned " + str(toActivate))


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
                self.debugLog("Creating arduino controller object...")
                self.ac = ArdCon(self.s,self.debugLog)
                self.debugLog("Arduino controller object Created!")
                self.debugLog("Asking Arduino data...")
                for i in [0,1]:
                    self.score["arduino"][i] = self.getArduinoScore(i)
                self.debugLog("Arduino data received!")
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
            self.updateScore()
        elif self.toDisconnect:
            self.disconnect()
        else:
            self.debugLog("Not connected")
        self.core.update()
        return True



    def updateScore(self):
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
