#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import serial
import time

sys.path.insert(0,"..")

from core import SubottoCore
from data import Session, Team, Player, Match, PlayerMatch, Event, Base, AdvantagePhase


from opcodes import *

from subotto_serial import SubottoSerial

    
def main():
    match_id = int(sys.argv[1])
    serial_port = sys.argv[2]
    ss = SubottoSerial(serial_port, 115200)
    # Here we wait for the SUB_READY command, otherwise we risk to
    # send commands before the unit is ready
    print ss.wait_for_ready()
    core = SubottoCore(match_id)
	
    # Run a test match
    ss.set_slave_mode()
    score = [0, 0]
    cached_score = [None, None]
    try:
        while True:
            events = ss.receive_events()
            for ev in events:
                team, var, desc, source = SubottoSerial.ASYNC_DESC[ev]
                score[team] += var
                print "%s; result is %d -- %d" % (desc, score[0], score[1])
                if var > 0:
                	core.act_goal(core.order[team], source)
                elif var < 0:
                	core.act_goal_undo(core.order[team], source)
            core.update()
            for i in [0, 1]:
                this_score = core.score[core.detect_team(core.order[i])]
                if this_score != cached_score[i]:
                    ss.set_score(this_score, i)
                    cached_score[i] = this_score
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
