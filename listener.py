#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import re
import datetime
import codecs
import time
import datetime
from pprint import pprint
import copy

import requests, json

from numpy import arange
import matplotlib.pyplot
import matplotlib.pylab
import matplotlib.dates

# from mako.template import Template

from data import Session, Team, Player, Match, PlayerMatch, Event, StatsPlayerMatch, Base, AdvantagePhase


SLEEP_TIME = 0.5
INTERESTING_SCORES = [42, 100, 250, 500, 750, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000]

with open('passwd_web') as fpasswd:
    PASSWD = fpasswd.read().strip()


def format_player(player):
    return "%s %s" % (player.fname, player.lname)


def get_status(begin, phase, end):
    if begin is None:
        return "before"
    
    elif end is not None:
        return "ended"
    
    elif phase is None:
        return "running"
    
    else:
        return "advantage"


def get_estimated_score(score, elapsed, length):
    if elapsed is None or elapsed <= 0.1:
        return [None, None]
    elif length - elapsed <= 0.1:
        return score
    else:
        return [int(s*length/elapsed) for s in score]


def get_remount_index(score, elapsed, length):
    if elapsed is None:
        return None
    
    to_go = length - elapsed
    if to_go <= 0.0:
        return "Infinity"
    else:
        return float(abs(score[0] - score[1])) / to_go * 60.0 * 60.0


def get_winning_team(teams, score):
    if score[0] > score[1]:
        return teams[0].name
    elif score[0] < score[1]:
        return teams[1].name
    else:
        return None

def get_losing_team(teams, score):
    if score[0] > score[1]:
        return teams[1].name
    elif score[0] < score[1]:
        return teams[0].name
    else:
        return None


def get_interesting_score(score):
    idx = map(lambda x: x > score, INTERESTING_SCORES).index(True)
    return INTERESTING_SCORES[idx]


def get_linear_projection(score, target, elapsed, begin):
    
    if begin is None or elapsed is None or elapsed <= 0.1:
        return None
    if score == 0:
        return "Infinity"
    
    ratio = float(score) / elapsed
    return ( begin + datetime.timedelta(seconds=float(target)/ratio) ).strftime("%H:%M:%S")




class Statistics:

    def __init__(self, match, old_matches, players, old_player_matches, old_events, old_stats_player_matches, target_dir):
        self.match = match
        self.old_matches = old_matches
        self.target_dir = target_dir
        self.last_match = old_matches[-1] if len(old_matches) > 0 else None
        self.last_score_plot = [[[], []], [[], []]]
        self.last_score = [0, 0]

        self.score = [0, 0]
        self.current_players = [None, None]
        self.partial = [0, 0]
        self.rev_colors = [None, None]    # 0 => red_team_id, 1 => blue_team_id
        
        self.current_phase = None
        
        self.total_goals = dict([])    # Map from player.id to the total number of goals ever
        self.num_goals = dict([])    # Map from player.id to the number of goals in this 24-hours tournament
        self.total_time = dict([])    # Map from player.id to the total number of seconds played ever
        self.played_time = dict([])    # Map from player.id to the number of seconds played in this 24-hours tournament
        self.participations = dict([])    # Map from player.id to the number of 24-hours played
        
        # Informazioni sui singoli giocatori...
        for player in players:
            self.total_goals[ player.id ] = 0
            self.num_goals[ player.id ] = 0
            self.total_time[ player.id ] = datetime.timedelta(0,0,0)
            self.played_time[ player.id ] = datetime.timedelta(0,0,0)
            self.participations[ player.id ] = 0
        
        self.score_plot = [[[], []], [[], []]]
        
        
        for player_match in old_player_matches:
            self.participations[ player_match.player_id ] += 1
        
        
        self.goal_sequence = dict([])        # Match id => Team id => Stack of the sequence of player id
        self.current_contestants = dict([])    # Match id => Team id => Pair of player id
        self.last_change = dict([])            # Match id => Team id => Time of last change
        self.turn_begin = None                # Beginning of last turn (in the current match)
        
        
        for old_match in old_matches:
            self.goal_sequence[ old_match.id ] = dict([ ( old_match.team_a_id, [] ), ( old_match.team_b_id, [] ) ])
            self.current_contestants[ old_match.id ] = dict([ ( old_match.team_a_id, [] ), ( old_match.team_b_id, [] ) ])
            self.last_change[ old_match.id ] = dict([ ( old_match.team_a_id, None ), ( old_match.team_b_id, None ) ])
        
        self.goal_sequence[ match.id ] = dict([ ( match.team_a_id, [] ), ( match.team_b_id, [] ) ])
        self.current_contestants[ match.id ] = dict([ ( match.team_a_id, [] ), ( match.team_b_id, [] ) ])
        self.last_change[ match.id ] = dict([ ( match.team_a_id, None ), ( match.team_b_id, None ) ])
        
        #pprint( self.last_change )
        
        for event in old_events:
            if event.type == Event.EV_TYPE_CHANGE:
                match_id = event.match_id
                team_id = event.team_id
                timestamp = event.timestamp
                
                '''
                if self.last_change[ match_id ][ team_id ] is not None:
                    # Aggiorno il tempo di gioco dei giocatori che stanno uscendo
                    delta_time = timestamp - self.last_change[ match_id ][ team_id ]
                    self.total_time[ self.current_contestants[ match_id ][ team_id ][0] ] += delta_time
                    self.total_time[ self.current_contestants[ match_id ][ team_id ][1] ] += delta_time
                '''
                
                # Effettuo il cambio
                self.current_contestants[ match_id ][ team_id ] = [ event.player_a_id, event.player_b_id ]
                if self.last_change[ match_id ][ team_id ] is None:
                    self.last_change[ match_id ][ team_id ] = event.match.begin
                else:
                    self.last_change[ match_id ][ team_id ] = timestamp
            
            elif event.type == Event.EV_TYPE_GOAL:
                match_id = event.match_id
                team_id = event.team_id
                contestants = self.current_contestants[ match_id ][ team_id ]
                
                # Segno il gol
                '''
                for c in contestants:
                    self.total_goals[ c ] += 1
                '''
                
                self.goal_sequence[ match_id ][ team_id ].append( contestants )

                if match_id == self.last_match.id:
                    i = 0 if team_id == self.last_match.team_a_id else 1
                    self.last_score[i] += 1
                    if self.match.begin is not None:
                        self.last_score_plot[i][0].append((event.timestamp - self.last_match.begin) + self.match.begin)
                    self.last_score_plot[i][1].append(self.last_score[i])
            
            elif event.type == Event.EV_TYPE_GOAL_UNDO:
                match_id = event.match_id
                team_id = event.team_id
                
                # Tolgo il gol
                contestants = self.goal_sequence[ match_id ][ team_id ].pop()
                '''
                for c in contestants:
                    self.total_goals[ c ] -= 1
                '''
                
                if match_id == self.last_match.id:
                    i = 0 if team_id == self.last_match.team_a_id else 1
                    self.last_score[i] -= 1
                    if self.match.begin is not None:
                        self.last_score_plot[i][0].pop()
                    self.last_score_plot[i][1].pop()
        
        # Bisogna segnare il tempo delle ultime due coppie che hanno giocato!
        for old_match in old_matches:
            
            match_id = old_match.id
            
            for team_id in [ old_match.team_a_id, old_match.team_b_id ]:
                delta_time = old_match.end - self.last_change[ match_id ][ team_id ]
                
                '''
                for player_id in self.current_contestants[ match_id ][ team_id ]:
                    self.total_time[ player_id ] += delta_time
                '''
        
        # Inserting data from table stats_player_matches
        
        for stats_player_match in old_stats_player_matches:
            self.total_time[ stats_player_match.player_id ] += datetime.timedelta(seconds=stats_player_match.seconds)
            self.total_goals[ stats_player_match.player_id ] += stats_player_match.pos_goals
    
    
    def detect_team(self, team):
        if team == self.match.team_a:
            return 0
        else:
            return 1

    def new_event(self, event):
        print >> sys.stderr, "> Received new event: %r" % (event)

        if self.match.begin != None and len(self.score_plot[0][0]) == 0:
            self.score_plot[0][0].append(self.match.begin)
            self.score_plot[0][1].append(0)
            self.score_plot[1][0].append(self.match.begin)
            self.score_plot[1][1].append(0)
            self.last_score_plot[0][0].insert(0, self.match.begin)
            self.last_score_plot[0][1].insert(0, 0)
            self.last_score_plot[1][0].insert(0, self.match.begin)
            self.last_score_plot[1][1].insert(0, 0)
        
        if event.type == Event.EV_TYPE_SWAP:
            self.rev_colors[0] = event.red_team_id
            self.rev_colors[1] = event.blue_team_id
        
        elif event.type == Event.EV_TYPE_CHANGE:
            i = self.detect_team(event.team)
            self.partial = [0, 0]
            self.current_players[i] = [event.player_a, event.player_b]
            
            # Ora aggiorno le statistiche individuali...
            match_id = self.match.id
            team_id = event.team_id
            timestamp = event.timestamp
            
            if self.last_change[ match_id ][ team_id ] is not None:
                # Aggiorno il tempo di gioco dei giocatori che stanno uscendo
                delta_time = timestamp - self.last_change[ match_id ][ team_id ]
                
                for player_id in [ self.current_contestants[ match_id ][ team_id ][0], self.current_contestants[ match_id ][ team_id ][1] ]:
                    self.total_time[ player_id ] += delta_time
                    self.played_time[ player_id ] += delta_time
            
            # Effettuo il cambio
            self.current_contestants[ match_id ][ team_id ] = [ event.player_a_id, event.player_b_id ]
            if self.last_change[ match_id ][ team_id ] is None:
                self.last_change[ match_id ][ team_id ] = self.match.begin
                self.turn_begin = self.match.begin
            else:
                self.last_change[ match_id ][ team_id ] = timestamp
                self.turn_begin = timestamp
            

        elif event.type == Event.EV_TYPE_GOAL:
            i = self.detect_team(event.team)
            self.score[i] += 1
            self.partial[i] += 1

            self.score_plot[i][0].append(event.timestamp)
            self.score_plot[i][1].append(self.score[i])
            
            match_id = self.match.id
            team_id = event.team_id
            contestants = self.current_contestants[ match_id ][ team_id ]
            
            # Segno il gol
            for c in contestants:
                self.total_goals[ c ] += 1
                self.num_goals[ c ] += 1
            
            self.goal_sequence[ match_id ][ team_id ].append( contestants )

        elif event.type == Event.EV_TYPE_GOAL_UNDO:
            i = self.detect_team(event.team)

            # BAD
            if self.score[i] == 0:
                return

            self.score[i] -= 1
            if self.partial[i] > 0:
                self.partial[i] -= 1

            self.score_plot[i][0].pop()
            self.score_plot[i][1].pop()

            match_id = self.match.id
            team_id = event.team_id
            
            # Tolgo il gol
            contestants = self.goal_sequence[ match_id ][ team_id ].pop()
            for c in contestants:
                self.total_goals[ c ] -= 1
                self.num_goals[ c ] -= 1
        
        elif event.type == Event.EV_TYPE_ADVANTAGE_PHASE:
            self.current_phase = event.phase


    def new_player_match(self, player_match):
        print >> sys.stderr, "> Received new player match: %r" % (player_match)
        
        # TODO: verificare (sperare) che questa funzione venga chiamata solo se quel player_match non esisteva ancora
        self.participations[ player_match.player_id ] += 1


    def send_data(self):
        print >> sys.stderr, "> Send data"

        # Compute time-related data
        now = datetime.datetime.now()
        if self.match.begin is not None:
            # La partita è già iniziata
            elapsed_time = (now - self.match.begin).total_seconds()
            time_to_begin = None
        else:
            # La partita deve ancora iniziare
            elapsed_time = None
            time_to_begin = (self.match.sched_begin - now).total_seconds()
        
        if self.match.end is not None:
            # La partita, oltre che essere iniziata, è anche finita.
            elapsed_time = (self.match.end - self.match.begin).total_seconds()
            time_to_end = None
        else:
            # La partita non è ancora finita
            time_to_end = (self.match.sched_end - now).total_seconds()
        
        if elapsed_time is not None and elapsed_time > 0.01 :
            goals_per_minute = float(self.score[0] + self.score[1]) * 60.0 / elapsed_time
        
        # Compute team-related data
        teams = (self.match.team_a, self.match.team_b)
        if self.match.begin is not None:
            colors = [ ['red', 'blue'][self.rev_colors.index(team.id)] for team in teams] # 0 => color of team_a, 1 => color of team_b
        else:
            colors = [None, None]
        
        
        # Compute turn-related data
        turn_end = datetime.datetime.now()
        if self.match.end is not None:
            turn_end = self.match.end
        
        if self.turn_begin is None and self.match.begin is not None:
        	self.turn_begin = self.match.begin
        if self.turn_begin is not None:
            turn_duration = turn_end - self.turn_begin
        
        
        # Compute (played time)-related data (it must be updated by hand for the current players,
        # even after the end of the match!)
        old_total_time = dict([])
        old_played_time = dict([])
        
        for team_id in [ self.match.team_a_id, self.match.team_b_id ]:
            for player_id in self.current_contestants[ self.match.id ][ team_id ]:
                old_total_time[ player_id ] = self.total_time[ player_id ]
                old_played_time[ player_id ] = self.played_time[ player_id ]
        
        
        for team_id in [ self.match.team_a_id, self.match.team_b_id ]:
            t = now
            if self.match.end is not None:
                t = self.match.end
            
            s = self.last_change[ self.match.id ][ team_id ]
            if self.match.begin is None or s is None:
                s = t
            
            if self.match.begin is not None and s is None:
                print "SOMETHING WRONG!"
            
            delta_time = t - s
        
            for player_id in self.current_contestants[ self.match.id ][ team_id ]:
                self.total_time[ player_id ] += delta_time
                self.played_time[ player_id ] += delta_time
        
        
        # Compute estimation-related data
        length = (self.match.sched_end - self.match.sched_begin).total_seconds()
        estimated_score = get_estimated_score(self.score, elapsed_time, length)
        remount_index = get_remount_index(self.score, elapsed_time, length)
        interesting_score = [get_interesting_score(s) for s in self.score]
        linear_projection = [get_linear_projection(self.score[i], interesting_score[i], elapsed_time, self.match.begin) for i in xrange(2)]
        
        
        # Send data to the web server
        data = {
            'status': get_status(self.match.begin, self.current_phase, self.match.end),
            'time_to_begin': time_to_begin,
            'time_to_end': time_to_end,
            'elapsed_time': elapsed_time,
            'teams': [
                {
                    'id': teams[i].id,
                    'name': teams[i].name,
                    'score': self.score[i],
                    'partial_score': self.partial[i],
                    'estimated_score': estimated_score[i],
                    'color': colors[i],
                    'interesting_score': interesting_score[i],
                    'linear_projection': linear_projection[i],
                    'players': [
                        {
                            'id': self.current_players[i][j].id,
                            'fname': self.current_players[i][j].fname,
                            'lname': self.current_players[i][j].lname,
                            'total_time': self.total_time[ self.current_players[i][j].id ].total_seconds(),
                            'played_time': self.played_time[ self.current_players[i][j].id ].total_seconds(),
                            'total_goals': self.total_goals[ self.current_players[i][j].id ],
                            'num_goals': self.num_goals[ self.current_players[i][j].id ],
                            'participations': self.participations[ self.current_players[i][j].id ],
                        }
                    for j in xrange(2)],
                }
                for i in xrange(2)],
            'goal_difference': abs(self.score[0] - self.score[1]),
            'total_goals': self.score[0] + self.score[1],
            'goals_per_minute': goals_per_minute,
            'turn_duration': turn_duration.total_seconds(),
            'remount_index': remount_index,
            }
        
        headers = {'content-type': 'application/json'}
        json_data = json.dumps({'action': 'set', 'password': PASSWD, 'data': data})
        print json_data
        
        r = requests.post("http://uz.sns.it/24h/score", data=json_data, headers=headers)
        print 'Request done', r.status_code
        print r.text

        
        # Restore previous status of current players
        for team_id in [ self.match.team_a_id, self.match.team_b_id ]:
            for player_id in self.current_contestants[ self.match.id ][ team_id ]:
                self.total_time[ player_id ] = old_total_time[ player_id ]
                self.played_time[ player_id ] = old_played_time[ player_id ]



def listen_match(match_id, target_dir, old_matches_id):

    session = Session()

    match = session.query(Match).filter(Match.id == match_id).one()
    old_matches = session.query(Match).filter(Match.id.in_(old_matches_id)).all()
    players = session.query(Player).all()
    old_player_matches = session.query(PlayerMatch).filter(PlayerMatch.match_id.in_(old_matches_id)).all()
    old_events = session.query(Event).filter(Event.match_id.in_(old_matches_id)).order_by(Event.timestamp).all()
    old_stats_player_matches = session.query(StatsPlayerMatch).filter(StatsPlayerMatch.match_id.in_(old_matches_id)).all()
    
    stats = Statistics(match, old_matches, players, old_player_matches, old_events, old_stats_player_matches, target_dir)
    last_event_id = 0
    last_player_match_id = 0
    last_timestamp = None

    try:
        while True:
            session.rollback()
            for player_match in session.query(PlayerMatch).filter(PlayerMatch.match == match).filter(PlayerMatch.id > last_player_match_id).order_by(PlayerMatch.id):
                stats.new_player_match(player_match)
                last_player_match_id = player_match.id
            for event in session.query(Event).filter(Event.match == match).filter(Event.id > last_event_id).order_by(Event.id):
                if last_timestamp is not None and event.timestamp <= last_timestamp:
                    print >> sys.stderr, "> Timestamp monotonicity error at %s!\n" % (event.timestamp)
                    #sys.exit(1)
                stats.new_event(event)
                last_timestamp = event.timestamp
                last_event_id = event.id
            stats.send_data()

            time.sleep(SLEEP_TIME)

    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    match_id = int(sys.argv[1])
    target_dir = sys.argv[2]
    old_matches_id = [1, 2, 3, 4]
    listen_match(match_id, target_dir, old_matches_id)
