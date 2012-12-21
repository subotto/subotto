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

    def __init__(self, match, old_matches):
        self.match = match
        self.old_matches = old_matches

    def new_event(self, event):
        print "> Received new event: %r" % (event)

    def new_player_match(self, player_match):
        print "> Received new player match: %r" % (player_match)

def listen_match(match_id):

    session = Session()

    match = session.query(Match).filter(Match.id == match_id).one()
    old_matches = session.query(Match).filter(Match.id <= 3).all()
    stats = Statistics(match, old_matches)
    last_event_id = 0
    last_player_match_id = 0

    try:
        while True:
            session.rollback()
            for player_match in session.query(PlayerMatch).filter(PlayerMatch.match == match).filter(PlayerMatch.id > last_player_match_id):
                stats.new_player_match(player_match)
                last_player_match_id = player_match.id
            for event in session.query(Event).filter(Event.match == match).filter(Event.id > last_event_id):
                stats.new_event(event)
                last_event_id = event.id

            time.sleep(SLEEP_TIME)

    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    listen_match(int(sys.argv[1]))
