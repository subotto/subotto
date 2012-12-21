#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import re
import datetime
import codecs
import time

from data import Session, Team, Player, Match, PlayerMatch, Event, Base, AdvantagePhase

def replay_match(orig_match_id, mult=1.0):

    session = Session()

    # Retrieve the original match and its beginning time
    orig_match = session.query(Match).filter(Match.id == orig_match_id).one()
    orig_start_time = orig_match.begin

    # Prepare the time conversion function
    start_time = datetime.datetime.now()
    def convert_time(time):
        return start_time + (time - orig_start_time)

    # Prepare the event list (they're already sorted by SQLAlchemy)
    events = map(lambda x: (max(x.timestamp - orig_start_time, datetime.timedelta(0)).total_seconds(), x), orig_match.events)
    ref_time = 0.0
    for i in xrange(len(events)):
        delta = events[i][0] - ref_time
        ref_time = events[i][0]
        events[i] = (delta, events[i][1])

    # Replicate the original match
    match = Match()
    match.sched_begin = convert_time(orig_match.sched_begin)
    match.sched_end = convert_time(orig_match.sched_end)
    match.begin = convert_time(orig_match.begin)
    match.name = "Replay of \"%s\"" % (orig_match.name)
    match.team_a = orig_match.team_a
    match.team_b = orig_match.team_b
    session.add(match)

    # Add the advantage phases
    phase = AdvantagePhase()
    phase.match = match
    phase.start_sec = 0
    phase.advantage = 10
    session.add(phase)
    phase = AdvantagePhase()
    phase.match = match
    phase.start_sec = 30 * 60
    phase.advantage = 5
    session.add(phase)
    phase = AdvantagePhase()
    phase.match = match
    phase.start_sec = 60 * 60
    phase.advantage = 3
    session.add(phase)

    # Replicate the player_matches
    for orig_pm in session.query(PlayerMatch).filter(PlayerMatch.match == orig_match):
        pm = PlayerMatch()
        pm.match = match
        pm.player = orig_pm.player
        pm.team = orig_pm.team
        session.add(pm)

    # Flush and commit
    session.flush()
    session.commit()

    # Print match ID
    print "Feeding match with ID %d" % (match.id)

    # Replay events
    for wait_secs, orig_ev in events:
        print "> Waiting %f seconds..." % (wait_secs)
        time.sleep(wait_secs / mult)
        ev = Event()
        ev.timestamp = convert_time(orig_ev.timestamp)
        ev.match = match
        ev.type = orig_ev.type
        ev.source = orig_ev.source
        ev.team = orig_ev.team
        ev.player_a = orig_ev.player_a
        ev.player_b = orig_ev.player_b
        ev.red_team = orig_ev.red_team
        ev.blue_team = orig_ev.blue_team
        ev.phase = orig_ev.phase
        print "> Pushing event of type %s and timestamp %s" % (ev.type, ev.timestamp)
        session.add(ev)
        ev.check_type()
        session.commit()

    match.end = convert_time(orig_match.end)
    session.commit()

if __name__ == '__main__':
    replay_match(3, 10.0)
