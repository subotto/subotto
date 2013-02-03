#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import serial
import os
import time

import glob


from gi.repository import Gtk 

import gobject

from opcodes import *

TEST_MODE = 0
SLAVE_MODE = 1

class interfaccia:

	work_mode = TEST_MODE

	def __init__(self):
		filename = "main.glade"
		self.builder = Gtk.Builder()
		self.builder.add_from_file(filename)
		self.builder.connect_signals(self)
		gobject.timeout_add(1000, self.loopFunction)
		self.builder.get_object("connection_general_baud").set_value(9600)
		self.builder.get_object("testmode_general_switch").set_active(1)

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

	def send_to_subotto(self,code):
		print "Invio "+str(code)+" al subotto"

		
	def change_subotto_mode(self, target):
		description = ""
		if target == TEST_MODE:
			description = "test mode"
		elif target == SLAVE_MODE:
			description = "slave mode"
		self.write_to_log("Asking subotto do enter "+description+"...")
		if (target == TEST_MODE):
			self.send_to_subotto(COM_SET_TEST_MODE)
		elif (target == SLAVE_MODE):
			self.send_to_subotto(COM_SET_SLAVE_MODE)
		self.write_to_log(" done\n")
	
	
	def switch_to_slavemode(self):
		self.change_subotto_mode(SLAVE_MODE)
		# TODO: verificare che il subotto abbia cambiato modalità
		
		work_mode = SLAVE_MODE
		self.builder.get_object("testmode_general_switch").set_active(0)
		# TODO: attivare lo switch della slavemode
	
	
	def switch_to_testmode(self):
		self.change_subotto_mode(TEST_MODE)
		# TODO: verificare che il subotto abbia cambiato modalità
		
		work_mode = TEST_MODE
		self.builder.get_object("testmode_general_switch").set_active(1)
		# TODO: disattivare lo switch della slavemode
	

	# testmode functions 

	def close_testmode_window(self,*args):
		self.builder.get_object("testmode_window").hide()

	def testmode_switch_activate(self, *args):
		if self.builder.get_object("testmode_general_switch").get_active():
			self.switch_to_testmode()
		else:
			self.switch_to_slavemode()
		
	
	
	# slavemode functions


if __name__ == "__main__":
	app = interfaccia()

	window = app.builder.get_object("connection_window")
	window.show_all()
	Gtk.main()

