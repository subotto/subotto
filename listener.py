#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import re
import datetime
import codecs
import time
from pprint import pprint

from mako.template import Template

from data import Session, Team, Player, Match, PlayerMatch, Event, Base, AdvantagePhase

SLEEP_TIME = 0.5
INTERESTING_SCORES = [42, 100, 250, 500, 750, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000]

def communicate_status(begin, phase, end):
	if begin is None:
		return "before"
	
	elif end is not None:
		return "ended"
	
	elif phase is None:
		return "running"
	
	else:
		return "advantage"

def format_time(total_seconds):
    seconds = total_seconds % 60
    total_seconds = total_seconds / 60
    minutes = total_seconds % 60
    hours = total_seconds / 60
    return "%02d:%02d:%02d" % (hours, minutes, seconds)

def format_time2(total_seconds):
    seconds = total_seconds % 60
    total_seconds = total_seconds / 60
    minutes = total_seconds % 60
    hours = total_seconds / 60
    return "%d ore, %d minuti e %d secondi" % (hours, minutes, seconds)

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
	# TODO: evitare le divisioni per 0
	# TODO: la proiezione lineare non funziona... debuggare!
    ratio = score / elapsed
    return begin + datetime.timedelta(seconds=float(target-score)/ratio)

def format_elapsed_time(total_seconds, begin, end):
	return format_time(total_seconds)

def format_remaining_time(total_seconds, end, length, phase):
	if end is not None:
		return "<td colspan=\"2\">La partita &egrave; terminata</td>"
	
	elif phase is None:
		return "<td>Tempo rimanente:</td><td>"+format_time(length - total_seconds)+"</td>"
	
	else:
		return "<td colspan=\"2\">Vantaggi (ai %d)</td>" % phase.advantage

def format_countdown(sched_begin):
	time_diff = (sched_begin - datetime.datetime.now()).total_seconds()
	
	if time_diff < 0:
		return "La partita dovrebbe iniziare a momenti!"
	
	else:
		return "Mancano "+format_time2( time_diff )+" all'inizio della partita..."

def show_player_statistics(player, total_time, participations):
	result = "<table class=\"giocatore\"><col width=\"220\" /><tr><th>" + format_player(player) + "</th></tr><tr><td>"
	result += "Tempo giocato: " + format_time2( int(total_time[ player.id ].total_seconds()) ) + "<br />"
	result += "Partecipazioni: " + str( participations[ player.id ] )
	result += "</td></tr></table>"
	
	return result

class Statistics:

    def __init__(self, match, old_matches, players, old_player_matches, old_events, target_dir):
        self.match = match
        self.old_matches = old_matches
        self.target_dir = target_dir

        self.score = [0, 0]
        self.current_players = [None, None]
        self.partial = [0, 0]
        
        self.current_phase = None
        
        self.total_goals = dict([])	# Map from player.id to the total number of goals ever
        self.num_goals = dict([])	# Map from player.id to the number of goals in this 24-hours tournament
        self.total_time = dict([])	# Map from player.id to the total number of seconds played ever
        self.played_time = dict([])	# Map from player.id to the number of seconds played in this 24-hours tournament
        self.participations = dict([])	# Map from player.id to the number of 24-hours played
        
        # Informazioni sui singoli giocatori...
        for player in players:
        	self.total_goals[ player.id ] = 0
        	self.num_goals[ player.id ] = 0
        	self.total_time[ player.id ] = datetime.timedelta(0,0,0)
        	self.played_time[ player.id ] = datetime.timedelta(0,0,0)
        	self.participations[ player.id ] = 0

        #TODO: aggiornare tutte queste informazioni...
        
        for player_match in old_player_matches:
        	self.participations[ player_match.player_id ] += 1
        
        
        self.goal_sequence = dict([])		# Match id => Team id => Stack of the sequence of player id
        self.current_contestants = dict([])	# Match id => Team id => Pair of player id
        self.last_change = dict([])			# Match id => Team id => Time of last change
        
        for match in old_matches:
        	self.goal_sequence[ match.id ] = dict([ ( match.team_a_id, [] ), ( match.team_b_id, [] ) ])
        	self.current_contestants[ match.id ] = dict([ ( match.team_a_id, [] ), ( match.team_b_id, [] ) ])
        	self.last_change[ match.id ] = dict([ ( match.team_a_id, None ), ( match.team_b_id, None ) ])
        
        #pprint( self.last_change )
        
        for event in old_events:
        	if event.type == Event.EV_TYPE_CHANGE:
        		match_id = event.match_id
        		team_id = event.team_id
        		timestamp = event.timestamp
        		
        		if self.last_change[ match_id ][ team_id ] is not None:
        			# Aggiorno il tempo di gioco dei giocatori che stanno uscendo
        			delta_time = timestamp - self.last_change[ match_id ][ team_id ]
        			self.total_time[ event.player_a_id ] += delta_time
        			self.total_time[ event.player_b_id ] += delta_time
        		
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
        		for c in contestants:
        			self.total_goals[ c ] += 1
        		
        		self.goal_sequence[ match_id ][ team_id ].append( contestants )
        	
        	elif event.type == Event.EV_TYPE_GOAL_UNDO:
        		match_id = event.match_id
        		team_id = event.team_id
        		
        		# Tolgo il gol
        		contestants = self.goal_sequence[ match_id ][ team_id ].pop()
        		for c in contestants:
        			self.total_goals[ c ] -= 1
        

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
            self.current_players[i] = [event.player_a, event.player_b]

        elif event.type == Event.EV_TYPE_GOAL:
            i = self.detect_team(event.team)
            self.score[i] += 1
            self.partial[i] += 1

        elif event.type == Event.EV_TYPE_GOAL_UNDO:
            i = self.detect_team(event.team)
            self.score[i] -= 1
            if self.partial[i] > 0:
                self.partial[i] -= 1
        
        elif event.type == Event.EV_TYPE_ADVANTAGE_PHASE:
        	self.current_phase = event.phase

    def new_player_match(self, player_match):
        print "> Received new player match: %r" % (player_match)
        
        # TODO: verificare (sperare) che questa funzione venga chiamata solo se quel player_match non esisteva ancora
        self.participations[ player_match.player_id ] += 1

    def render_template(self, basename, kwargs):
        template = Template(filename=os.path.join('templates', '%s.mako' % (basename)), output_encoding='utf-8')
        with codecs.open(os.path.join(self.target_dir, '%s.html' % (basename)), 'w', encoding='utf-8') as fout:
            fout.write(template.render_unicode(**kwargs))

    def regenerate(self):
        print "> Regeneration"

        # Prepare mako arguments
        kwargs = {}
        kwargs['sched_begin'] = self.match.sched_begin
        kwargs['begin'] = self.match.begin
        kwargs['end'] = self.match.end
        if self.match.begin is not None:
        	kwargs['elapsed'] = (datetime.datetime.now() - self.match.begin).total_seconds()
        if self.match.end is not None:
        	kwargs['elapsed'] = (self.match.end - self.match.begin).total_seconds()
        kwargs['length'] = (self.match.sched_end - self.match.sched_begin).total_seconds()
        kwargs['score'] = self.score
        kwargs['partial'] = self.partial
        kwargs['current_players'] = self.current_players
        kwargs['teams'] = (self.match.team_a, self.match.team_b)
        kwargs['phase'] = self.current_phase
        
        kwargs['total_time'] = self.total_time
        kwargs['participations'] = self.participations
        
        kwargs['communicate_status'] = communicate_status
        kwargs['format_time'] = format_time
        kwargs['format_time2'] = format_time2
        kwargs['format_player'] = format_player
        kwargs['remount_index'] = remount_index
        kwargs['compute_interesting_score'] = compute_interesting_score
        kwargs['compute_linear_projection'] = compute_linear_projection
        kwargs['format_elapsed_time'] = format_elapsed_time
        kwargs['format_remaining_time'] = format_remaining_time
        kwargs['format_countdown'] = format_countdown
        kwargs['show_player_statistics'] = show_player_statistics

        # Generate stats dir
        try:
            os.mkdir(self.target_dir)
        except OSError:
            pass

        # Render templates
        templates = [ "time", "score", "general_stats", "projection", "fake", "player00", "player01", "player10", "player11" ]
        if self.match.begin is None:
        	templates = [ "fake", "countdown" ]
        
        print "BEGIN: %r" % self.match.begin
        print "END: %r" % self.match.end
        
        for basename in templates:
            try:
                self.render_template(basename, kwargs)
            except Exception:
                print "> Exception when rendering %s" % (basename)
                raise

def listen_match(match_id, target_dir):

    session = Session()

    match = session.query(Match).filter(Match.id == match_id).one()
    old_matches = session.query(Match).filter(Match.id <= 3).all()	# TODO: immagino che un giorno la condizione Match.id <= 3 vada aggiustata...
    players = session.query(Player).all()
    old_player_matches = session.query(PlayerMatch).filter(PlayerMatch.match_id <= 3).all() # TODO: anche qui bisognerà aggiustare la condizione match <= 3
    old_events = session.query(Event).filter(Event.match_id <= 3).all() # TODO: stessa cosa
    
    stats = Statistics(match, old_matches, players, old_player_matches, old_events, target_dir)
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
    listen_match(int(sys.argv[1]), sys.argv[2])
