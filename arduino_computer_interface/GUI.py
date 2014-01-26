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
import serial
import os
import time

import glob

from gi.repository import Gtk 

import gobject
gobject.threads_init()

from opcodes import *

from subotto_serial import SubottoSerial

TEST_MODE = 2
SLAVE_MODE = 1
MASTER_MODE = 0

class interfaccia:

    work_mode = MASTER_MODE
    connected = False
    sensors_swap_enable = False
    score = [0, 0]
    cached_score = [None, None]

    def __init__(self):
        filename = "main.glade"
        self.builder = Gtk.Builder()
        self.builder.add_from_file(filename)
        self.builder.connect_signals(self)
        gobject.timeout_add(300, self.loopFunction)
        self.refresh_device_list()
        self.builder.get_object("connection_general_baud").set_value(115200)
        self.builder.get_object("testmode_general_switch").set_active(False)

    def write_to_log(self,string):
        logBuffer = self.builder.get_object("connection_log_textview").get_buffer()
        logBuffer.insert(logBuffer.get_end_iter(),string)
        self.builder.get_object("connection_log_textview").set_buffer(logBuffer)

    def connect(self,*args):
        if not self.connected:    
            try:
                self.ss = SubottoSerial(
                        self.builder.get_object("connection_general_device").get_text(),
                        self.builder.get_object("connection_general_baud").get_value()
                        )
                if not self.ss.wait_for_ready():
                    raise Exception("MCU not ready")
            except:
                self.write_to_log("Connection failed\n")
            else:
                self.connected = True
                self.write_to_log("Connection successful\n")
            
    
    def disconnect(self,*args):
        if self.connected:
            self.switch_to_mastermode()
            del self.ss
            self.connected = False
            self.write_to_log("Disconnected\n")
    
    def quit(self,*args):
        try:
            disconnect()
        except:
            pass
        sys.exit(0)


    def refresh_device_list(self,*args):
        object = self.builder.get_object("connection_general_devicelist")
        buffer = object.get_buffer()
        buffer.delete(buffer.get_start_iter(),buffer.get_end_iter())
        for device in glob.glob("/dev/ttyACM*"):
            buffer.insert(buffer.get_end_iter(),device+"\n")
        object.set_buffer(buffer)
                          
    def loopFunction(self,*args):
        self.refresh_device_list()
        self.elaborate_async_events()
        if self.builder.get_object("testmode_mainsensors_sweep_switch").get_active():
            self.probe_blue1()
            self.probe_blue2()
            self.probe_red1()
            self.probe_red2()
        return True

    def elaborate_async_events(self):
        if self.connected:
            events = self.ss.receive_events()
            if self.work_mode is SLAVE_MODE:
                for ev in events:
                    team, var, desc, source = SubottoSerial.ASYNC_DESC[ev]
                    score[team] += var
                    print "%s; result is %d -- %d" % (desc, score[0], score[1])
                    if var > 0:
                        #core.act_goal(core.order[team], source)
                        print "ordine al core" #TODO
                    elif var < 0:
                        #core.act_goal_undo(core.order[team], source)
                        print "ordine al core" #TODO
                #core.update()
                for i in [0, 1]:
                    #this_score = core.score[core.detect_team(core.order[i])]
                    #if this_score != cached_score[i]:
                        #ss.set_score(this_score, i)
                        #cached_score[i] = this_score
                    this_score = score
                    if this_score != cached_score[i]:
                        ss.set_score(this_score, i)
                        this_score = core.score[core.detect_team(core.order[i])]
            if self.work_mode is TEST_MODE:
                if len(events) != 0:
                    self.write_to_log("Something wrong: received async codes in test mode")
            
            if self.work_mode is MASTER_MODE:
                if len(events) != 0:
                    self.write_to_log("Something wrong: received async codes in master mode")
                
        

    def ask_test(self,*args):
        if self.connected:
            self.elaborate_async_events()
            self.write_to_log("Sending ping probe... ")
            self.builder.get_object("connection_test_spinner").start()
            self.builder.get_object("connection_test_light").set_from_stock("gtk-dialog-warning",Gtk.IconSize.BUTTON)
            try:
                if self.ss.request_echo():
                    self.write_to_log("Pong received\n")
                    self.builder.get_object("connection_test_light").set_from_stock("gtk-yes",Gtk.IconSize.BUTTON)
                else:
                    self.write_to_log("Something wrong\n")
                    self.builder.get_object("connection_test_light").set_from_stock("gtk-no",Gtk.IconSize.BUTTON)
            except:
                self.write_to_log("Something very wrong\n")
                self.builder.get_object("connection_test_light").set_from_stock("gtk-no",Gtk.IconSize.BUTTON)
            self.builder.get_object("connection_test_spinner").stop()
        
    #def fake_end_test(self,*args):
        #self.write_to_log("Fake pong recived\n")
        #self.builder.get_object("connection_test_spinner").stop()
        #self.builder.get_object("connection_test_light").set_from_stock("gtk-yes",Gtk.IconSize.BUTTON)
        #return False

    def open_testmode_window(self,*args): #OUTDATED
        self.builder.get_object("testmode_window").show_all()

    def send_to_subotto(self,code): #OUTDATED
        print "Invio "+str(code)+" al subotto"

        
    def change_subotto_mode(self, target): #OUTDATED
        description = ""
        if target == TEST_MODE:
            description = "test mode"
        elif target == MASTER_MODE:
            description = "master mode"
        elif target == SLAVE_MODE:
            description = "slave mode"
        self.write_to_log("Asking subotto do enter "+description+"...")
        if (target == TEST_MODE):
            self.send_to_subotto(COM_SET_TEST_MODE)
        elif (target == MASTER_MODE):
            self.send_to_subotto(COM_SET_MASTER_MODE)
        elif (target == SLAVE_MODE):
            self.send_to_subotto(COM_SET_SLAVE_MODE)
        self.write_to_log(" done\n")
    
    
    def switch_to_slavemode(self):
        if self.connected:
            self.elaborate_async_events()
            try:
                if self.ss.set_slave_mode():
                    self.write_to_log("Successfully switched to slave mode\n")
                else:
                    self.write_to_log("Fail to switch to slave mode\n")
            except:
                self.write_to_log("Something went wront switching to slave mode\n")
            else:
                work_mode = SLAVE_MODE
                self.builder.get_object("testmode_general_switch").set_active(True)
        else:
            self.builder.get_object("testmode_general_switch").set_active(True)
        
    def switch_to_mastermode(self):
        if self.connected:
            self.elaborate_async_events()
            try:
                if self.ss.set_master_mode():
                    self.write_to_log("Successfully switched to master mode\n")
                else:
                    self.write_to_log("Fail to switch to master mode\n")
            except:
                self.write_to_log("Something went wront switching to master mode\n")
            else:
                work_mode = MASTER_MODE
                self.builder.get_object("testmode_general_switch").set_active(True)
        else:
            self.builder.get_object("testmode_general_switch").set_active(True)
        
    def switch_to_testmode(self):
        if self.connected:
            self.elaborate_async_events()
            try:
                if self.ss.set_test_mode():
                    self.write_to_log("Successfully switched to test mode\n")
                else:
                    self.write_to_log("Fail to switch to test mode\n")
            except:
                self.write_to_log("Something went wront switching to test mode\n")
            else:
                work_mode = TEST_MODE
                self.builder.get_object("testmode_general_switch").set_active(False)
        else:
            self.builder.get_object("testmode_general_switch").set_active(True)

    

    # testmode functions 

    def close_testmode_window(self,*args):
        self.builder.get_object("testmode_window").hide()

    def testmode_general_switch_activate(self,*args):
        if not self.builder.get_object("testmode_general_switch").get_active():
            self.switch_to_testmode()
        else:
            self.switch_to_mastermode()
    
    def probe_blue1(self,*args):
        if self.connected:
            self.elaborate_async_events()
            status = self.ss.send_recv(COM_BLUE_NORMAL_TEST)
            if status is SUB_TEST_OPEN:
                self.builder.get_object("testmode_mainsensors_blue1_image").set_from_stock("gtk-yes",Gtk.IconSize.BUTTON)
            elif status is SUB_TEST_CLOSE:
                self.builder.get_object("testmode_mainsensors_blue1_image").set_from_stock("gtk-no",Gtk.IconSize.BUTTON)
            else:
                self.write_to_log("Something wrong\n")
        else:
            self.builder.get_object("testmode_mainsensors_blue1_image").set_from_stock("gtk-dialog-warning",Gtk.IconSize.BUTTON)
            
    def probe_blue2(self,*args):
        if self.connected:
            self.elaborate_async_events()
            status = self.ss.send_recv(COM_BLUE_SUPER_TEST)
            if status is SUB_TEST_OPEN:
                self.builder.get_object("testmode_mainsensors_blue2_image").set_from_stock("gtk-yes",Gtk.IconSize.BUTTON)
            elif status is SUB_TEST_CLOSE:
                self.builder.get_object("testmode_mainsensors_blue2_image").set_from_stock("gtk-no",Gtk.IconSize.BUTTON)
            else:
                self.write_to_log("Something wrong\n")
        else:
            self.builder.get_object("testmode_mainsensors_blue2_image").set_from_stock("gtk-dialog-warning",Gtk.IconSize.BUTTON)
            
    def probe_red1(self,*args):
        if self.connected:
            self.elaborate_async_events()
            status = self.ss.send_recv(COM_RED_NORMAL_TEST)
            if status is SUB_TEST_OPEN:
                self.builder.get_object("testmode_mainsensors_red1_image").set_from_stock("gtk-yes",Gtk.IconSize.BUTTON)
            elif status is SUB_TEST_CLOSE:
                self.builder.get_object("testmode_mainsensors_red1_image").set_from_stock("gtk-no",Gtk.IconSize.BUTTON)
            else:
                self.write_to_log("Something wrong\n")
        else:
            self.builder.get_object("testmode_mainsensors_red1_image").set_from_stock("gtk-dialog-warning",Gtk.IconSize.BUTTON)
            
    def probe_red2(self,*args):
        if self.connected:
            self.elaborate_async_events()
            status = self.ss.send_recv(COM_RED_SUPER_TEST)
            if status is SUB_TEST_OPEN:
                self.builder.get_object("testmode_mainsensors_red2_image").set_from_stock("gtk-yes",Gtk.IconSize.BUTTON)
            elif status is SUB_TEST_CLOSE:
                self.builder.get_object("testmode_mainsensors_red2_image").set_from_stock("gtk-no",Gtk.IconSize.BUTTON)
            else:
                self.write_to_log("Something wrong\n")
        else:
            self.builder.get_object("testmode_mainsensors_red2_image").set_from_stock("gtk-dialog-warning",Gtk.IconSize.BUTTON)
            
        
        
    # slavemode functions


if __name__ == "__main__":
    app = interfaccia()

    window = app.builder.get_object("connection_window")
    window.show_all()
    Gtk.main()








def main():
    
    return 0

if __name__ == '__main__':
    main()

