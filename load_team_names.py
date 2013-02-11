#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import datetime

from data import Session, Team, Player, Match, PlayerMatch, Event, Base, AdvantagePhase, QueueElement
from core import SubottoCore, act_init_match

def main():
    match_id = int(sys.argv[1])
    team_name = sys.argv[2]
    in_filename = sys.argv[3]

    core = SubottoCore(match_id)
    team = core.session.query(Team).filter(Team.name == team_name).one()
    with open(in_filename) as in_file:
        for line in in_file:
            line = line.strip()
            fname, lname, comment = line.split(',')
            if comment == '':
                comment = None
            core.act_add_player_match_from_name(team, fname, lname, comment, bulk=True)
    core.session.commit()

if __name__ == '__main__':
    main()
