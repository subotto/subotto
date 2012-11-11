#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import re
import datetime
import codecs

from data import Session, Team, Player, Match, PlayerMatch, Event, Base

line_re = re.compile("^\\[([0-9]*)\\] ([A-Z_]*) \\(([^)]*)\\)$")

def destroy_all():
    session = Session()
    Base.metadata.drop_all()
    session.commit()

def create_teams():
    session = Session()
    Base.metadata.create_all()
    session.commit()
    t1 = Team()
    t1.name = 'Matematici'
    t2 = Team()
    t2.name = 'Fisici'
    session.add(t1)
    session.add(t2)
    session.commit()

def import_from_2010():
    session = Session()
    match = Match()
    match.name = "24 ore 2010"
    import_log(match, session, '2010/log-finale.txt')

def import_from_2011():
    session = Session()
    match = Match()
    match.name = "24 ore 2011"
    import_log(match, session, '2011/log-seconda-24h.txt')

def import_log(match, session, logfile):
    first_team = session.query(Team).filter(Team.name == "Matematici").one()
    second_team = session.query(Team).filter(Team.name == "Fisici").one()

    events = []
    first_players = set()
    second_players = set()

    def add_player(p):
	if not p in goalPerPlayer:
            goalPerPlayer[p] = 0
            timePerPlayer[p] = 0
        try:
            fname, lname = p.split(' ', 1)
        except ValueError:
            fname = p
            lname = ''
        player = Player.get_or_create(session, fname, lname, None)
        return player

    def add_pair(p):
	if not p in goalPerPair:
            goalPerPair[p] = 0
            timePerPair[p] = 0

    def split_and_add_players(data):
	playersList = data.split(',')
	playersList.sort()
	players = tuple(playersList)
	p1 = add_player(players[0])
        p2 = add_player(players[1])
	add_pair(players)
        return players, (p1, p2)

    log = dict()
    for line in codecs.open(logfile, encoding='utf-8'):
	if line.startswith("#"):
            continue
	match_ = line_re.match(line)
	if match_ == None:
            print "Bad line: %s" % (line)
            sys.exit(1)
	else:
            log[int(match_.group(1))] = (match_.group(2),  match_.group(3))

    firstGoal = 0
    secondGoal = 0
    firstBest = 0
    secondBest = 0
    swapped = False
    goalPerPlayer = dict()
    goalPerPair = dict()
    timePerPlayer = dict()
    timePerPair = dict()
    freqPerPlayer = dict()
    freqPerPair = dict()
    firstLastTime = None
    secondLastTime = None
    firstPlayers = (None, None)
    secondPlayers = (None, None)
    startTime = None
    stopTime = None
    lastTime = None

    frames = log.keys()
    frames.sort()
    for time in frames:
        if lastTime != None:
            assert(time > lastTime)
            lastTime = time
        cmd = log[time][0]
	data = log[time][1]
	goal = 0
	first = None
	if cmd == 'TEAM_SWAP':
            swapped = not swapped

            # Event
            ev = Event()
            ev.match = match
            ev.timestamp = datetime.datetime.fromtimestamp(float(time) / 1000)
            ev.type = Event.EV_TYPE_SWAP
            ev.red_team = first_team if not swapped else second_team
            ev.blue_team = second_team if not swapped else first_team
            events.append(ev)
	elif cmd == 'RED_GOAL':
            goal = 1
            first = True
	elif cmd == 'BLUE_GOAL':
            goal = 1
            first = False
	elif cmd == 'RED_GOAL_UNDO':
            goal = -1
            first = True
	elif cmd == 'BLUE_GOAL_UNDO':
            goal = -1
            first = False
	elif cmd == 'FIRST_TEAM_CHANGE':
            if firstLastTime != None:
                timeDelta = time - firstLastTime
                timePerPair[firstPlayers] += timeDelta
                timePerPlayer[firstPlayers[0]] += 0.5 * timeDelta
                timePerPlayer[firstPlayers[1]] += 0.5 * timeDelta
            firstLastTime = time
            firstPlayers, (p1, p2) = split_and_add_players(data)
            first_players.add(p1)
            first_players.add(p2)

            # Event
            ev = Event()
            ev.match = match
            ev.timestamp = datetime.datetime.fromtimestamp(float(time) / 1000)
            ev.type = Event.EV_TYPE_CHANGE
            ev.team = first_team
            ev.player_a = p1
            ev.player_b = p2
            events.append(ev)
	elif cmd == 'SECOND_TEAM_CHANGE':
            if secondLastTime != None:
                timeDelta = time - secondLastTime
                timePerPair[secondPlayers] += timeDelta
                timePerPlayer[secondPlayers[0]] += 0.5 * timeDelta
                timePerPlayer[secondPlayers[1]] += 0.5 * timeDelta
            secondLastTime = time
            secondPlayers, (p1, p2) = split_and_add_players(data)
            second_players.add(p1)
            second_players.add(p2)

            # Event
            ev = Event()
            ev.match = match
            ev.timestamp = datetime.datetime.fromtimestamp(float(time) / 1000)
            ev.type = Event.EV_TYPE_CHANGE
            ev.team = second_team
            ev.player_a = p1
            ev.player_b = p2
            events.append(ev)
	elif cmd == 'START_MATCH':
            firstLastTime = time
            secondLastTime = time
            startTime = time

            # Match
            match.sched_begin = datetime.datetime.fromtimestamp(float(startTime) / 1000)
            match.begin = datetime.datetime.fromtimestamp(float(startTime) / 1000)
            _, first_team_name, second_team_name = data.split(',')
            assert(first_team_name == "Matematici")
            assert(second_team_name == "Fisici")
            match.team_a = first_team
            match.team_b = second_team

            # Initial swap
            ev = Event()
            ev.match = match
            ev.timestamp = match.begin
            ev.type = Event.EV_TYPE_SWAP
            ev.red_team = first_team
            ev.blue_team = second_team
            events.append(ev)
	elif cmd == 'STOP_MATCH':
            if firstLastTime != None:
                timeDelta = time - firstLastTime
                timePerPair[firstPlayers] += timeDelta
                timePerPlayer[firstPlayers[0]] += 0.5 * timeDelta
                timePerPlayer[firstPlayers[1]] += 0.5 * timeDelta
            if secondLastTime != None:
                timeDelta = time - secondLastTime
                timePerPair[secondPlayers] += timeDelta
                timePerPlayer[secondPlayers[0]] += 0.5 * timeDelta
                timePerPlayer[secondPlayers[1]] += 0.5 * timeDelta
		stopTime = time
            match.sched_end = datetime.datetime.fromtimestamp(float(stopTime) / 1000)
            match.end = datetime.datetime.fromtimestamp(float(stopTime) / 1000)
        elif cmd == 'START_LOG':
            pass
	else:
            print "Unknown command: %s" % (cmd)

	#print (first, goal)
        if first == None:
            assert(goal == 0)
        if first != None:
            ev = Event()
            ev.match = match
            ev.timestamp = datetime.datetime.fromtimestamp(float(time) / 1000)
            assert(goal == 1 or goal == -1)
            if goal == 1:
                ev.type = Event.EV_TYPE_GOAL
            else:
                ev.type = Event.EV_TYPE_GOAL_UNDO
            if swapped:
                first = not first
            if first:
                ev.team = first_team
                assert(goal != 0)
                firstGoal += goal
                goalPerPlayer[firstPlayers[0]] += 0.5 * goal
                goalPerPlayer[firstPlayers[1]] += 0.5 * goal
                goalPerPair[firstPlayers] += goal
                if firstGoal > secondGoal and firstBest < firstGoal - secondGoal:
                    firstBest = firstGoal - secondGoal
            else:
                ev.team = second_team
                assert(goal != 0)
                secondGoal += goal
                goalPerPlayer[secondPlayers[0]] += 0.5 * goal
                goalPerPlayer[secondPlayers[1]] += 0.5 * goal
                goalPerPair[secondPlayers] += goal
                if secondGoal > firstGoal and secondBest < secondGoal - firstGoal:
                    secondBest = secondGoal - firstGoal
            events.append(ev)

    session.add(match)

    # Player association
    for player in first_players:
        print >> sys.stderr, player.lname
        playermatch = PlayerMatch()
        playermatch.match = match
        playermatch.player = player
        playermatch.team = first_team
        session.add(playermatch)
        session.flush()
    for player in second_players:
        print >> sys.stderr, player.lname
        playermatch = PlayerMatch()
        playermatch.match = match
        playermatch.player = player
        playermatch.team = second_team
        session.add(playermatch)
        session.flush()

    for ev in events:
        session.add(ev)
        assert(ev.check_type())
    session.flush()
    session.commit()

if __name__ == '__main__':
    destroy_all()
    create_teams()
    import_from_2010()
    import_from_2011()
