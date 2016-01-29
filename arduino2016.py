#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys
import socket
import SocketServer
import time
import threading
import struct

from data import Session, Team, Player, Match, PlayerMatch, Event, Base, AdvantagePhase
from core import SubottoCore

running = True

# Always hold this lock to access the core
core_lock = threading.Lock()
core = None

CODE_NOOP = 0
CODE_CELL_RED_PLAIN = 1
CODE_CELL_RED_SUPER = 2
CODE_CELL_BLUE_PLAIN = 3
CODE_CELL_BLUE_SUPER = 4
CODE_BUTTON_RED_GOAL = 7
CODE_BUTTON_RED_UNDO = 8
CODE_BUTTON_BLUE_GOAL = 5
CODE_BUTTON_BLUE_UNDO = 6

# From https://docs.python.org/2/library/socketserver.html#asynchronous-mixins
class Connection(SocketServer.BaseRequestHandler):
    def handle(self):
        global running, core, core_lock
        fd = self.request.makefile('r+b', 0)
        actions = {
            CODE_NOOP: lambda: None,
            CODE_CELL_RED_PLAIN: core.act_red_goal_cell,
            CODE_CELL_RED_SUPER: core.act_red_supergoal_cell,
            CODE_CELL_BLUE_PLAIN: core.act_blue_goal_cell,
            CODE_CELL_BLUE_SUPER: core.act_blue_supergoal_cell,
            CODE_BUTTON_RED_GOAL: core.act_red_goal_button,
            CODE_BUTTON_RED_UNDO: core.act_red_goalundo_button,
            CODE_BUTTON_BLUE_GOAL: core.act_blue_goal_button,
            CODE_BUTTON_BLUE_UNDO: core.act_blue_goalundo_button,
            }
        while running:
            code = ord(fd.read(1))
            # Do something with the code
            with core_lock:
                core.update()
                actions[code]()
            red_score = core.easy_get_red_score()
            blue_score = core.easy_get_blue_score()
            fd.write(struct.pack(">HH", red_score, blue_score))
        fd.close()

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

def main():
    global running, core, core_lock
    match_id = int(sys.argv[1])
    listen_addr = sys.argv[2]
    listen_port = int(sys.argv[3])

    core = SubottoCore(match_id)
    with core_lock:
        core.update()

    # Initialize ConnectionServer
    server = ThreadedTCPServer((listen_addr, listen_port), Connection)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()

    # Do things
    try:
        while True:
            with core_lock:
                core.update()
            time.sleep(1.0)
    except KeyboardInterrupt:
        running = False

    running = False
    server.shutdown()
    server.server_close()
    server_thread.join()

if __name__ == '__main__':
    main()
