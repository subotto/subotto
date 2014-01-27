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

from numpy import arange
import matplotlib.pyplot
import matplotlib.pylab
import matplotlib.dates

from mako.template import Template

from data import Session, Team, Player, Match, PlayerMatch, Event, StatsPlayerMatch, Base, AdvantagePhase

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

def format_time3(total_seconds):
    seconds = total_seconds % 60
    total_seconds = total_seconds / 60
    minutes = total_seconds % 60
    hours = total_seconds / 60
    return "%dh %dm" % (hours, minutes)

def format_time2(total_seconds, abbr):
    # Return value: [ str, k ], where str is the formatted time, and k is 0 for "plural" and 1 for "singular"
    total_seconds = int(total_seconds)
    
    seconds = total_seconds % 60
    total_seconds = total_seconds / 60
    minutes = total_seconds % 60
    hours = total_seconds / 60
    
    result = ""
    
    if abbr == 0:
        if hours == 1:
            result += "1 ora, "
        elif hours > 1:
            result += "%d ore, " % hours
        
        if minutes > 0 or hours > 0:
            # Printing minutes...
            if minutes == 1:
                result += "1 minuto e "
            elif minutes > 1:
                result += "%d minuti e " % minutes
        
        #print seconds
        
        if seconds == 1:
            result += "1 secondo"
        else:
            result += "%d secondi" % seconds
        
        singular = 0
        if seconds == 1 and minutes == 0 and hours == 0:
            singular = 1
        
        #print [ result, singular ]
        
        return [ result, singular ]
    
    
    if abbr == 1:
        if hours == 1:
            result += "1 ora"
        elif hours > 1:
            result += "%d ore" % hours
        
        if hours > 0 and minutes > 0:
            result += " e "
        
        if minutes == 1:
            result += "1 minuto"
        elif minutes > 1:
            result += "%d minuti" % minutes
        
        singular = 0
        if ( hours == 1 and minutes == 0 ) or ( hours == 0 and minutes == 1 ):
            singular = 1
        
        #result += " %d sec" % seconds
        
        return [ result, singular ]


def format_player(player):
    return "%s %s" % (player.fname, player.lname)


def compute_extimated_score(score, elapsed, length):
    if elapsed <= 0.1:
        return "-"
    elif length - elapsed <= 1:
        return "%d - %d" % (score[0], score[1])
    else:
        return "%d - %d" % ( int(score[0]*length/elapsed), int(score[1]*length/elapsed) )

def remount_index(score, elapsed, length):
    to_go = length - elapsed
    if to_go <= 0.0:
        return u"&infin;"
    else:
        return u"%0.8f" % (float(abs(score[0] - score[1])) / to_go * 60.0 * 60.0)

def remount_index_description(score, teams):
    if score[0] == score[1]:
        return "gol in pi&ugrave; all'ora che deve segnare la squadra in svantaggio per recuperare"
    else:
        ordered_teams = [ teams[1].name, teams[0].name ]
        if score[0] < score[1]:
            ordered_teams = [ teams[0].name, teams[1].name ]
        return "gol in pi&ugrave; all'ora che devono segnare<br /> i " + ordered_teams[0] + " per recuperare i " + ordered_teams[1]

def compute_interesting_score(score):
    idx = map(lambda x: x > score, INTERESTING_SCORES).index(True)
    return INTERESTING_SCORES[idx]

def compute_linear_projection(score, target, elapsed, begin):
    # print "Score: %d. Target: %d. Elapsed: %d." % (score, target, elapsed)
    
    if elapsed <= 0.1:
        return "-"
    if score == 0:
        return "&infin;"
    
    ratio = score / elapsed
    
    # pprint( begin + datetime.timedelta(seconds=float(target-score)/ratio) )
    
    return ( begin + datetime.timedelta(seconds=float(target)/ratio) ).strftime("%H:%M:%S")

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
        r = format_time2( time_diff, 0 )
        res = ""
        
        if r[1] == 0:
            res += "Mancano "
        else:
            res += "Manca "
        
        res += r[0] + " all'inizio della partita..."
        return res

def show_player_statistics(player, total_time, played_time, total_goals, num_goals, participations):
    result = '<table class="player_stats">'
    result += '<tr><td>Partecipazioni</td><td>' + str( participations[ player.id ] ) + '</td></tr>'
    result += '<tr><td>Tempo di gioco</td><td>' + format_time3( int(played_time[ player.id ].total_seconds()) ) + '</td></tr>'
    result += '<tr class="all_matches"><td>in tutte le edizioni</td><td>' + format_time3( int(total_time[ player.id ].total_seconds()) ) + '</td></tr>'
    result += '<tr><td>Gol fatti</td><td>' + str( num_goals[ player.id ] ) + '</td></tr>'
    result += '<tr class="all_matches"><td>in tutte le edizioni</td><td>' + str( total_goals[ player.id ] ) + '</td></tr>'
    result += '</table>'
    
    return result

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

    def render_template(self, basename, kwargs):
        template = Template(filename=os.path.join('templates', '%s.mako' % (basename)), output_encoding='utf-8')
        with codecs.open(os.path.join(self.target_dir, '%s.html' % (basename)), 'w', encoding='utf-8') as fout:
            fout.write(template.render_unicode(**kwargs))

    def regenerate(self):
        print >> sys.stderr, "> Regeneration"

        now = datetime.datetime.now()
        if self.match.begin is not None:
            elapsed_time = (now - self.match.begin).total_seconds()
        if self.match.end is not None:
            elapsed_time = (self.match.end - self.match.begin).total_seconds()

        # Prepare mako arguments
        kwargs = {}
        kwargs['sched_begin'] = self.match.sched_begin
        kwargs['begin'] = self.match.begin
        kwargs['end'] = self.match.end
        kwargs['elapsed'] = elapsed_time
        kwargs['length'] = (self.match.sched_end - self.match.sched_begin).total_seconds()
        kwargs['score'] = self.score
        kwargs['partial'] = self.partial
        kwargs['current_players'] = self.current_players
        kwargs['teams'] = (self.match.team_a, self.match.team_b)
        kwargs['phase'] = self.current_phase
        
        teams = (self.match.team_a, self.match.team_b)
        teams_id2pos = { self.match.team_a.id: 0, self.match.team_b.id: 1 }
        teams_col2pos = [ teams_id2pos[ self.rev_colors[0] ], teams_id2pos[ self.rev_colors[1] ] ]
        rev_teams = [ teams[ teams_col2pos[0] ], teams[ teams_col2pos[1] ] ]
        
        kwargs['teams_col2pos'] = teams_col2pos    # 0 => red_team_index, 1 => blue_team_index
        kwargs['rev_teams'] = rev_teams    # 0 => red_team, 1 => blue_team
        
        # Il tempo di gioco dei current players va aggiornato a mano (anche dopo la fine)!
        
        # Saving the status of current players
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
                print >> "QUALCOSA NON VA!"
            
            delta_time = t - s
        
            for player_id in self.current_contestants[ self.match.id ][ team_id ]:
                self.total_time[ player_id ] += delta_time
                self.played_time[ player_id ] += delta_time
        
        kwargs['total_time'] = self.total_time
        kwargs['played_time'] = self.played_time
        kwargs['total_goals'] = self.total_goals
        kwargs['num_goals'] = self.num_goals
        kwargs['participations'] = self.participations
        
        turn_end = datetime.datetime.now()
        if self.match.end is not None:
            turn_end = self.match.end
        kwargs['turn_duration'] = turn_end - self.turn_begin
        
        kwargs['communicate_status'] = communicate_status
        kwargs['format_time'] = format_time
        kwargs['format_time2'] = format_time2
        kwargs['format_player'] = format_player
        kwargs['compute_extimated_score'] = compute_extimated_score
        kwargs['remount_index'] = remount_index
        kwargs['remount_index_description'] = remount_index_description
        
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
        templates = [ "time", "statistics", "fake", "red_team", "blue_team", "red_score", "blue_score", "red_defender", "red_attacker", "blue_defender", "blue_attacker", "red_defender_stats", "red_attacker_stats", "blue_defender_stats", "blue_attacker_stats", "player00", "player01", "player10", "player11", "player00_stats", "player01_stats", "player10_stats", "player11_stats", "team0", "team1", "score0", "score1" ]
        if self.match.begin is None:
            templates = [ "fake", "countdown" ]
        
        #print >> sys.stderr, "> BEGIN: %r" % self.match.begin
        #print >> sys.stderr, "> END: %r" % self.match.end
        
        for basename in templates:
            try:
                self.render_template(basename, kwargs)
            except Exception:
                print >> sys.stderr, "> Exception when rendering %s" % (basename)
                raise
        
        
        # Restoring previous status of current players
        for team_id in [ self.match.team_a_id, self.match.team_b_id ]:
            for player_id in self.current_contestants[ self.match.id ][ team_id ]:
                self.total_time[ player_id ] = old_total_time[ player_id ]
                self.played_time[ player_id ] = old_played_time[ player_id ]
        
        # Draw the score plot
        if self.match.begin is not None:
            for plot_scope in ['all', 'last']:
                output_dpi = 72.0
                output_pixels = (440, 330)
                output_inches = (float(output_pixels[0]) / output_dpi, float(output_pixels[1]) / output_dpi)
                fig = matplotlib.pyplot.figure(figsize=output_inches)
                ax = fig.add_axes([0.1, 0.1, 0.85, 0.85])
                ax.grid(True)

                # Set algorithms to draw ticks and labels on axes
                if plot_scope == 'all':
                    ax.xaxis.set_major_locator(matplotlib.dates.HourLocator())
                    if elapsed_time < 6 * 3600:
                        ax.xaxis.set_minor_locator(matplotlib.dates.MinuteLocator(interval=15))
                    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%H"))
                elif plot_scope == 'last':
                    ax.xaxis.set_major_locator(matplotlib.dates.MinuteLocator(interval=5))
                    ax.xaxis.set_minor_locator(matplotlib.dates.MinuteLocator(interval=1))
                    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%H:%M"))

                # Set limits (not sure how to make it work...)
                #print ax.get_xlim()
                #print ax.get_ylim()
                #ax.set_xlim(xmin=0)
                #ax.set_ylim(ymin=0)

                COLORS = ['g', 'b']
                for i in [0, 1]:
                    self.score_plot[i][0].append(now if self.match.end is None else self.match.end)
                    self.score_plot[i][1].append(self.score_plot[i][1][-1])
                    if plot_scope == 'all':
                        ax.plot(self.score_plot[i][0], self.score_plot[i][1], '-%s' % (COLORS[i]))
                    else:
                        this_score_plot = [None, None]
                        this_score_plot[0] = [x for x in self.score_plot[i][0] if x > (now if self.match.end is None else self.match.end) - datetime.timedelta(minutes=30)]
                        this_score_plot[1] = self.score_plot[i][1][-len(this_score_plot[0]):]
                        ax.plot(this_score_plot[0], this_score_plot[1], '-%s' % (COLORS[i]))
                    self.score_plot[i][0].pop()
                    self.score_plot[i][1].pop()
                if plot_scope == 'all':
                    for i in [0, 1]:
                        threshold = 0
                        for j in self.last_score_plot[i][0]:
                            if j < now:
                                threshold += 1
                            else:
                                break
                        ax.plot(self.last_score_plot[i][0][:threshold], self.last_score_plot[i][1][:threshold], '--%s' % (COLORS[i]))

                fig.savefig(os.path.join(self.target_dir, "score_plot_%s.png" % (plot_scope)), dpi=output_dpi)
                matplotlib.pylab.close(fig)
                #fig.show()

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
            stats.regenerate()

            time.sleep(SLEEP_TIME)

    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    match_id = int(sys.argv[1])
    target_dir = sys.argv[2]
    old_matches_id = [1, 2, 3]
    listen_match(match_id, target_dir, old_matches_id)
