#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import datetime

from data import Session, Team, Player, Match, PlayerMatch, Event, Base, AdvantagePhase, QueueElement
from core import SubottoCore, act_init_match, start_actually_match, end_actually_match

def main():
    if len(sys.argv)!= 3:
        print "Usage: {} match_id [start|end]".format(sys.argv[0])
        sys.exit(1)
    match_id = int(sys.argv[1])

    action = sys.argv[2]
    session = Session()
    if action == "start":
        ora = start_actually_match(session,match_id)
        print >> sys.stderr, "> Started match {} at {}".format(match_id,ora)
    elif action == "end":
        ora = end_actually_match(session,match_id)
        print >> sys.stderr, "> Ended match {} at {}".format(match_id,ora)
    else:
        print "Usage: {} match_id [start|end]".format(sys.argv[0])
        session.commit()
        sys.exit(1)

    session.commit()


if __name__ == '__main__':
    main()
