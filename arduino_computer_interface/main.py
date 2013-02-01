#!/usr/bin/env python

import sys
import serial
import os
import time

import glob

#try:  
#    import pygtk  
#    pygtk.require("2.0")  
#except:  
#    pass  
#try:  
#    import gtk  
#    import gtk.glade  
#except:  
#    print("GTK Not Availible")

from gi.repository import Gtk 

import gobject

class interfaccia:

    work_mode = 0

    def __init__(self):
        filename = "main.glade"
        self.builder = Gtk.Builder()
        self.builder.add_from_file(filename)
        self.builder.connect_signals(self)
        gobject.timeout_add(1000, self.loopFunction)
        self.builder.get_object("connection_general_baud").set_value(9600)

    def quit(self, *args):
        sys.exit(0)

    def write_to_log(self,string):
        buffer = self.builder.get_object("connection_log_textview").get_buffer()
        buffer.insert(buffer.get_end_iter(),string)
        self.builder.get_object("connection_log_textview").set_buffer(buffer)


    def refresh_device_list(self,*args):
        object = self.builder.get_object("connection_general_devicelist")
        buffer = object.get_buffer()
        buffer.delete(buffer.get_start_iter(),buffer.get_end_iter())
        for device in glob.glob("/dev/ttyS*"):
            buffer.insert(buffer.get_end_iter(),device+"\n")
        object.set_buffer(buffer)
                          
    def loopFunction(self,*args):
        self.refresh_device_list()
        return True

    def ask_test(self,*args):
        self.write_to_log("Sending ping probe\n")
        self.builder.get_object("connection_test_spinner").start()
        self.builder.get_object("connection_test_light").set_from_stock("gtk-no",Gtk.IconSize.BUTTON)
        gobject.timeout_add(5000, self.fake_end_test)
        
    def fake_end_test(self,*args):
        self.write_to_log("Fake pong recived\n")
        self.builder.get_object("connection_test_spinner").stop()
        self.builder.get_object("connection_test_light").set_from_stock("gtk-yes",Gtk.IconSize.BUTTON)
        return False

    def open_testmode_window(self,*args):
        self.builder.get_object("testmode_window").show_all()

    def send_to_subotto(self,string):
        print "Invio "+string+" al subotto"

        
    def change_subotto_mode(self):
        description = ""
        if mode == 0:
            description = "test mode"
        elif mode == 1:
            description = "slave mode"
        write_to_log("Asking subotto do enter "+description+"...")
        if (mode == 0):
            send_to_subotto("0")
        elif (mode == 1):
            send_to_subotto("16")
        write_to_log(" done\n")
    
        

    # testmode functions 

    def close_testmode_window(self,*args):
        self.builder.get_object("testmode_window").hide()

    def testmode_switch_activate(self, *args):
        mode = 1
        self.change_subotto_mode()
        # TODO: disattivare la slavemode
        
    


    # slavemode functions


if __name__ == "__main__":
    app = interfaccia()

    window = app.builder.get_object("connection_window")
    window.show_all()
    Gtk.main()

