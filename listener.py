#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import re
import datetime
import codecs
import time

from mako.template import Template

from data import Session, Team, Player, Match, PlayerMatch, Event, Base, AdvantagePhase

SLEEP_TIME = 0.5
INTERESTING_SCORES = [42, 100, 250, 500, 750, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000]

def format_time(total_seconds):
    seconds = total_seconds % 60
    total_seconds = total_seconds / 60
    minutes = total_seconds % 60
    hours = total_seconds / 60
    return "%d:%02d:%02d" % (hours, minutes, seconds)

def format_player(player):
    return "%s %s" % (player.fname, player.lname)

def remount_index(score, elapsed, length):
    to_go = length - elapsed
    if to_go <= 0.0:
        return u"&infin;"
    else:
        return u"%0.8f" % (float(score[0] - score[1]) / to_go * 60.0 * 60.0)

def compute_interesting_score(score):
    idx = map(lambda x: x > score, INTERESTING_SCORES).index(True)
    return INTERESTING_SCORES[idx]

def compute_linear_projection(score, target, elapsed, begin):
    ratio = score / elapsed
    return begin + datetime.timedelta(seconds=float(target-score)/ratio)

class Statistics:

    def __init__(self, match, old_matches):
        self.match = match
        self.old_matches = old_matches

        self.score = [0, 0]
        self.players = [None, None]
        self.partial = [0, 0]

    def detect_team(self, team):
        if team == self.match.team_a:
            return 0
        else:
            return 1

    def new_event(self, event):
        print "> Received new event: %r" % (event)

        if event.type == Event.EV_TYPE_CHANGE:
            i = self.detect_team(event.team)
            self.partial = [0, 0]
            self.players[i] = [event.player_a, event.player_b]

        elif event.type == Event.EV_TYPE_GOAL:
            i = self.detect_team(event.team)
            self.score[i] += 1
            self.partial[i] += 1

        elif event.type == Event.EV_TYPE_GOAL_UNDO:
            i = self.detect_team(event.team)
            self.score[i] -= 1
            if self.partial[i] > 0:
                self.partial[i] -= 1

    def new_player_match(self, player_match):
        print "> Received new player match: %r" % (player_match)

    def regenerate(self):
        print "> Regeneration"

        # Prepare mako arguments
        kwargs = {}
        kwargs['begin'] = self.match.begin
        kwargs['elapsed'] = (datetime.datetime.now() - self.match.begin).total_seconds()
        kwargs['length'] = (self.match.sched_end - self.match.sched_begin).total_seconds()
        kwargs['score'] = self.score
        kwargs['partial'] = self.partial
        kwargs['players'] = self.players
        kwargs['teams'] = (self.match.team_a, self.match.team_b)
        kwargs['format_time'] = format_time
        kwargs['format_player'] = format_player
        kwargs['remount_index'] = remount_index
        kwargs['compute_interesting_score'] = compute_interesting_score
        kwargs['compute_linear_projection'] = compute_linear_projection

        # Generate stats dir
        try:
            os.mkdir('stats')
        except OSError:
            pass

        # Generate base.html
        template = Template(filename='templates/base.mako', output_encoding='utf-8')
        with codecs.open('stats/base.html', 'w', encoding='utf-8') as fout:
            fout.write(template.render_unicode(**kwargs))

        # Generate graph.png

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
            stats.regenerate()

            time.sleep(SLEEP_TIME)

    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    listen_match(int(sys.argv[1]))
