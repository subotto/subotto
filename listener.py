#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import re
import datetime
import codecs
import time

from data import Session, Team, Player, Match, PlayerMatch, Event, Base, AdvantagePhase

SLEEP_TIME = 0.5

class Statistics:

    def __init__(self, match):
        self.match = match

    def new_event(self, event):
        print "> Received new event: %r" % (event)

def listen_match(match_id):

    session = Session()

    match = session.query(Match).filter(Match.id == match_id).one()
    stats = Statistics(match)
    last_event_id = 0

    try:
        while True:
            session.rollback()
            for event in session.query(Event).filter(Event.match == match).filter(Event.id > last_event_id):
                stats.new_event(event)
                last_event_id = event.id

            time.sleep(SLEEP_TIME)

    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    listen_match(int(sys.argv[1]))
