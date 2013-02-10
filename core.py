#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import datetime 
import os
from select import select
now=datetime.datetime.now

from data import Session, Team, Player, Match, PlayerMatch, Event, Base, AdvantagePhase, QueueElement

def act_init_match(session, name, team_a, team_b, sched_begin, sched_end):
    match = Match()
    match.sched_begin = sched_begin
    match.sched_end = sched_end
    match.begin = None
    match.end = None
    match.name = name
    match.team_a = team_a
    match.team_b = team_b
    session.add(match)
    session.commit()
    return match.id

class SubottoCore:

    def __init__(self, match_id):
        self.session = Session()
        self.match = self.session.query(Match).filter(Match.id == match_id).one()
        self.teams = [self.match.team_a, self.match.team_b]
        self.order = [None, None]
        self.queues = [[], []]
        self.score = [0, 0]
        self.players = [[None, None], [None, None]]
        self.listeners = []

        self.last_event_id = 0
        self.last_player_match_id = 0
        self.last_timestamp = None

    def close(self):
        self.session.rollback()
        self.session.close()

    def detect_team(self, team):
        if team == self.match.team_a:
            return 0
        else:
            return 1

    def new_player_match(self, player_match):
        print >> sys.stderr, "> Received new player match: %r" % (player_match)

        for listener in self.listeners:
            listener.new_player_match(player_match)

    def new_event(self, event):
        print >> sys.stderr, "> Received new event: %r" % (event)

        if event.type == Event.EV_TYPE_SWAP:
            self.order = [event.red_team, event.blue_team]

        elif event.type == Event.EV_TYPE_CHANGE:
            self.players[self.detect_team(event.team)] = [event.player_a, event.player_b]

        elif event.type == Event.EV_TYPE_GOAL:
            self.score[self.detect_team(event.team)] += 1

        elif event.type == Event.EV_TYPE_GOAL_UNDO:
            self.score[self.detect_team(event.team)] -= 1

        elif event.type == Event.EV_TYPE_ADVANTAGE_PHASE:
            pass

        else:
            print >> sys.stderr, "> Wrong event type %r\n" % (event.type)

        for listener in self.listeners:
            listener.new_event(event)

    def regenerate(self):
        print >> sys.stderr, "> Regeneration"
        for listener in self.listeners:
            listener.regenerate()

    def update(self):
        self.session.rollback()

        for player_match in self.session.query(PlayerMatch).filter(PlayerMatch.match == self.match).filter(PlayerMatch.id > self.last_player_match_id).order_by(PlayerMatch.id):
            self.new_player_match(player_match)
            self.last_player_match_id = player_match.id

        for event in self.session.query(Event).filter(Event.match == self.match).filter(Event.id > self.last_event_id).order_by(Event.id):
            if self.last_timestamp is not None and event.timestamp <= self.last_timestamp:
                print >> sys.stderr, "> Timestamp monotonicity error at %s!\n" % (event.timestamp)
                #sys.exit(1)
            self.new_event(event)
            self.last_timestamp = event.timestamp
            self.last_event_id = event.id

        for idx in [0, 1]:
            team = self.teams[idx]
            this_num = 0
            self.queues[idx] = []
            for queue_element in self.match.get_queue(team):
                if queue_element.num != this_num:
                    printf >> sys.stderr, "> Error: queues are inconsistent"
                this_num += 1
                self.queues[idx].append((queue_element.player_a, queue_element.player_b))

        self.regenerate()
        return True

    def act_event(self, event, source=None):
        event.timestamp = now()
        event.match = self.match
        if source is None:
            event.source = Event.EV_SOURCE_MANUAL
        else:
            event.source = source
        if not event.check_type():
            print >> sys.stderr, "> Sending bad event..."
        self.session.add(event)
        self.session.commit()
        self.update()

    def act_switch_teams(self, source=None):
        e = Event()
        e.type = Event.EV_TYPE_SWAP
        if self.order == [None, None]:
            e.red_team = self.teams[0]
            e.blue_team = self.teams[1]
        else:
            e.red_team = self.order[1]
            e.blue_team = self.order[0]
        self.act_event(e, source)

    def act_goal(self, team, source=None):
        e = Event()
        e.type = Event.EV_TYPE_GOAL
        e.team = team
        self.act_event(e, source)

    def act_goal_undo(self, team, source=None):
        e = Event()
        e.type = Event.EV_TYPE_GOAL_UNDO
        e.team = team
        self.act_event(e, source)

    def act_team_change(self, team, player_a, player_b, source=None):
        e = Event()
        e.type = Event.EV_TYPE_CHANGE
        e.team = team
        e.player_a = player_a
        e.player_b = player_b
        self.act_event(e, source)

    def act_add_to_queue(self, team, player_a, player_b):
        qe = QueueElement()
        qe.match = self.match
        qe.team = team
        qe.player_a = player_a
        qe.player_b = player_b
        qe.num = len(self.queues[self.detect_team(team)])
        self.session.add(qe)
        self.session.commit()
        self.update()

    def act_remove_from_queue(self, team, num):
        queue = self.match.get_queue(team)
        self.session.delete(queue[num])
        self.session.flush()
        del queue[num]
        # Indirect assignement to prevent failing constraints
        for i in xrange(num, len(queue)):
            queue[i].num = None
        self.session.flush()
        for i in xrange(num, len(queue)):
            queue[i].num = i
        self.session.commit()
        self.update()

    def act_swap_queue(self, team, num1, num2):
        queue = self.match.get_queue(team)
        # Indirect assignement to prevent failing constraints
        queue[num1].num = None
        queue[num2].num = None
        self.session.flush()
        queue[num1].num = num2
        queue[num2].num = num1
        self.session.commit()
        self.update()

    def act_begin_match(self, begin=None):
        if begin is None:
            begin = datetime.datetime.now()
        self.match.begin = begin
        self.session.commit()

    def act_end_match(self, end=None):
        if end is None:
            end = datetime.datetime.now()
        self.match.end = end
        self.session.commit()
