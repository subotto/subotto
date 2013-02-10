#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import datetime

from data import Session, Team, Player, Match, PlayerMatch, Event, Base, AdvantagePhase, QueueElement
from core import SubottoCore, act_init_match

def main():
    name = sys.argv[1]

    session = Session()
    team_a = session.query(Team).filter(Team.name == "Matematici").one()
    team_b = session.query(Team).filter(Team.name == "Fisici").one()
    sched_begin = datetime.datetime.strptime(sys.argv[2], '%Y-%m-%d %H:%M:%S')
    sched_end = datetime.datetime.strptime(sys.argv[3], '%Y-%m-%d %H:%M:%S')
    match_id = act_init_match(session, name, team_a, team_b, sched_begin, sched_end)
    session.commit()
    print "> Created match with ID %d" % (match_id)

if __name__ == '__main__':
    main()
