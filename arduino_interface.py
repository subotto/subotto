#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys
import socket
import SocketServer
import time
import threading
import struct
import select

from data import Session, Team, Player, Match, PlayerMatch, Event, Base, AdvantagePhase
from core import SubottoCore

running = True
dry_run = True

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

IGNORE_CODES = []

allowed_IPs = ['127.0.0.1']


def timezone():
    t = int(time.time())
    return (t % 10 < 5)


# From https://docs.python.org/2/library/socketserver.html#asynchronous-mixins
class Connection(SocketServer.BaseRequestHandler):
    def handle(self):
        # TODO: print peer name
        print >> sys.stderr, "Connection received"
        addr = self.client_address
        print >> sys.stderr, addr
        if !dry_run and addr[0] not in allowed_IPs:
            self.request.shutdown(socket.SHUT_RDWR)
            return
        global running, core, core_lock
        fd = self.request.makefile('r+b', 0)
        actions = {
            CODE_NOOP: lambda: None,
            CODE_CELL_RED_PLAIN: core.easy_act_red_goal_cell,
            CODE_CELL_RED_SUPER: core.easy_act_red_supergoal_cell,
            CODE_CELL_BLUE_PLAIN: core.easy_act_blue_goal_cell,
            CODE_CELL_BLUE_SUPER: core.easy_act_blue_supergoal_cell,
            CODE_BUTTON_RED_GOAL: core.easy_act_red_goal_button,
            CODE_BUTTON_RED_UNDO: core.easy_act_red_goalundo_button,
            CODE_BUTTON_BLUE_GOAL: core.easy_act_blue_goal_button,
            CODE_BUTTON_BLUE_UNDO: core.easy_act_blue_goalundo_button,
            }
        last_gol = time.time()
        while running:
            ready_r, ready_w, ready_x = select.select([fd], [], [], 1.0)
            if fd in ready_r:
                code_str = fd.read(1)
                if code_str == '':
                    break
                code = ord(code_str)
                print >> sys.stderr, "Received code: %d" % (code)
                if code not in IGNORE_CODES:
                    with core_lock:
                        try:
                            if time.time()-last_gol > 0.8:
                                if dry_run:
                                    print >> sys.stdout, "fun: %s" % str(actions[code])
                                else:
                                    actions[code]()
                                if(code != 0):
                                    last_gol = time.time()
                        except KeyError:
                            print >> sys.stderr, "Wrong code"
                else:
                    print >> sys.stderr, "Ignore command because of configuration"
            with core_lock:
                core.update()
            if (time.time()-last_gol) < 5:
                red_score = core.easy_get_red_part()
                blue_score = core.easy_get_blue_part()
            else:
                red_score = core.easy_get_red_score()
                blue_score = core.easy_get_blue_score()
            print >> sys.stdout, red_score, blue_score
            fd.write(struct.pack(">HH", red_score, blue_score))
        fd.close()
        self.request.shutdown(socket.SHUT_RDWR)
        print >> sys.stderr, "Connection closed"

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

def main():
    global running, core, core_lock
    match_id = int(sys.argv[1])
    listen_addr = sys.argv[2]
    listen_port = int(sys.argv[3])
    arduino_ip = sys.argv[4]

    allowed_IPs.append(arduino_ip)

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
