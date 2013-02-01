#! /usr/bin/env python2.7


import sys
import psycopg2
import datetime 
import os
from select import select
now=datetime.datetime.now

from data import Session, Team, Player, Match, PlayerMatch, Event, Base, AdvantagePhase

#try:
import gi
# make sure you use gtk+-2.0
from gi.repository import Gtk
#except:
#    print "Could not load GTK2 packages"
#    sys.exit()
debuglevel=0
def debug(string, level):
    if debuglevel >= level:
        print string


class SquadraSubotto(object):

    def __init__ (self, team, core, glade_file="subotto24.glade"):
        self.team = team
        self.core = core
        self.builder=Gtk.Builder()
        self.builder.add_objects_from_file(glade_file,["box_team","im_queue_promote","im_gol_plus","im_gol_minus"])
        self.core.listeners.append(self)

        self.box=self.builder.get_object("box_team")
        self.name_gtk=self.builder.get_object("name_team")
        self.name_gtk.set_text(self.team.name)
        self.builder.connect_signals(self)        

        self.player_list = []
        self.combo_players=Gtk.ListStore(int,str)
        combo_renderer = Gtk.CellRendererText()
        self.builder.get_object("combo_queue_att").set_model(self.combo_players)
        self.builder.get_object("combo_queue_att").pack_start(combo_renderer, True)
        self.builder.get_object("combo_queue_att").add_attribute(combo_renderer, 'text',1)
        self.builder.get_object("combo_queue_dif").set_model(self.combo_players)
        self.builder.get_object("combo_queue_dif").pack_start(combo_renderer, True)
        self.builder.get_object("combo_queue_dif").add_attribute(combo_renderer, 'text',1)

    def goal_incr(self):
        self.core.act_goal(self.team)

    def goal_decr(self):
        self.core.act_goal_undo(self.team)

    def promote(self):
        # FIXME
        combo=dict()
        player=dict()
        for i in ('att','dif'):
            combo[i]=self.builder.get_object("combo_queue_"+i)
            player[i]=combo[i].get_model()[combo[i].get_active()]
        self.pgs.change(self.name,player['att'][0],player['dif'][0])
        debug(self.name+" promoting : "+ str(player['att'][1]) + " and " + str(player['dif'][1])  ,20)

    def on_btn_gol_plus_clicked (self, widget):
        self.goal_incr()

    def on_btn_gol_minus_clicked (self, widget):
        self.goal_decr()

    def on_btn_queue_promote_clicked(self, widget):
        self.promote()

    def regenerate(self):
        # Write score
        self.builder.get_object("points").set_text("%d" % (self.core.score[self.core.detect_team(self.team)]))

        # Write active players
        players = self.core.players[self.core.detect_team(self.team)]
        if players != [None, None]:
            for i in (("name_current_att",0),("name_current_dif",1)):
                self.builder.get_object(i[0]).set_text(players[i[1]].format_name())

    def new_player_match(self, player_match):
        # Update player combo boxes
        if player_match.team == self.team:
            player = player_match.player
            # TODO - Bad hack, because I can't work out how to keep
            # the list sorted in a nicer way
            self.player_list.append((player.format_name(), player.id))
            self.player_list.sort()
            self.combo_players.clear()
            for i, j in self.player_list:
                self.combo_players.append((j, i))

    def new_event(self, event):
        pass


class Subotto24GTK(object):

    team=dict()
    team_slot=dict()

    def __init__ (self, core, glade_file="subotto24.glade"):
        self.builder=Gtk.Builder()
        self.builder.add_objects_from_file(glade_file,["window_subotto_main","im_team_switch"])
        self.core = core
        self.core.listeners.append(self)

        self.window=self.builder.get_object("window_subotto_main")
        
        self.team_slot = [self.builder.get_object("box_red_slot"),
                          self.builder.get_object("box_blue_slot")]
        self.teams = [SquadraSubotto(self.core.match.team_a, core),
                      SquadraSubotto(self.core.match.team_b, core)]
        self.order = [None, None]

        self.builder.connect_signals(self)

    def switch_teams(self):
        self.core.act_switch_teams()
        self.update_teams()

    def update_teams(self):
        # Update our internal copy of order
        if self.core.order == [None, None]:
            self.order = [None, None]
        else:
            if self.core.order[0] == self.core.teams[0]:
                self.order = [self.teams[0], self.teams[1]]
            else:
                self.order = [self.teams[1], self.teams[0]]

            # Update GUI and teams
            for i in [0, 1]:
                if self.order[i].box.get_parent() is None:
                    self.team_slot[i].add(self.order[i].box)
                else:
                    self.order[i].box.reparent(self.team_slot[i])
            
    def on_window_destroy (self, widget):
        Gtk.main_quit()

    def on_btn_switch_clicked (self, widget):
        debug("Cambio!", 2)
        self.switch_teams()

    def regenerate(self):
        debug("Updating!",20)
        self.update_teams()

    def new_player_match(self, player_match):
        pass

    def new_event(self, event):
        pass

class SubottoCore:

    def __init__(self, match_id):
        self.session = Session()
        self.match = self.session.query(Match).filter(Match.id == match_id).one()
        self.teams = [self.match.team_a, self.match.team_b]
        self.order = [None, None]
        self.score = [0, 0]
        self.players = [[None, None], [None, None]]
        self.listeners = []

        self.last_event_id = 0
        self.last_player_match_id = 0
        self.last_timestamp = None

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
            print >> sys.stderr, "> Sending bad event...\n"
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

if __name__ == "__main__":

    match_id = 4
    core = SubottoCore(match_id)
    main_window = Subotto24GTK(core)

    core.update()
    gi.repository.GObject.timeout_add(1000, core.update)

    Gtk.main()
