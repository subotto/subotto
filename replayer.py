#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import re
import datetime
import codecs
import time

from data import Session, Team, Player, Match, PlayerMatch, Event, Base, AdvantagePhase

def multiply_timedelta(mult, td):
    return datetime.timedelta(seconds=mult * td.total_seconds())

def replay_match(orig_match_id, mult=1.0, initial_wait=0.0):

    session = Session()

    # Retrieve the original match and prepare the new event list
    # (already sorted by SQLAlchemy)
    orig_match = session.query(Match).filter(Match.id == orig_match_id).one()
    events = [((min(max(x.timestamp, orig_match.begin), orig_match.end) - orig_match.begin).total_seconds(), x)
              for x in orig_match.events]
    ref_time = 0.0
    for i in xrange(len(events)):
        delta = events[i][0] - ref_time
        ref_time = events[i][0]
        events[i] = (delta / mult, events[i][1])

    # Replicate the original match
    match = Match()
    match.sched_begin = datetime.datetime.now() + datetime.timedelta(seconds=0.5 * initial_wait)
    match.sched_end = match.sched_begin + multiply_timedelta(1.0 / mult, orig_match.sched_end - orig_match.sched_begin)
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

    # Print match ID and start wait
    print "> Feeding match with ID %d" % (match.id)
    print "> Scheduled times: %s -- %s" % (match.sched_begin, match.sched_end)
    print "> Waiting initial %f seconds..." % (initial_wait)
    time.sleep(initial_wait)

    # Set begin
    match.begin = datetime.datetime.now()
    print "> Match begins at %s" % (match.begin)
    session.commit()

    # Replay events
    for wait_secs, orig_ev in events:
        print "> Waiting %f seconds..." % (wait_secs)
        time.sleep(wait_secs / mult)
        ev = Event()
        ev.timestamp = datetime.datetime.now()
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

    # Set end
    match.end = datetime.datetime.now()
    print "> Match ends at %s" % (match.end)
    session.commit()

    print "> Finished feeding match with ID %d" % (match.id)
    print "> Scheduled times were: %s -- %s" % (match.sched_begin, match.sched_end)

if __name__ == '__main__':
    match_id, mult, initial_wait = sys.argv[1:]
    match_id = int(match_id)
    mult = float(mult)
    initial_wait = float(initial_wait)
    replay_match(match_id, mult, initial_wait)
