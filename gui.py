#! /usr/bin/env python2.7


import sys
import datetime 
import os
from select import select
now=datetime.datetime.now

from data import Session, Team, Player, Match, PlayerMatch, Event, Base, AdvantagePhase
from core import SubottoCore

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
        self.builder.add_objects_from_file(glade_file,["box_team","im_queue_promote","im_gol_plus","im_gol_minus", "liststore_queue",
                                                       "im_to_queue", "im_swap_up", "im_swap_down"])
        self.core.listeners.append(self)

        self.box=self.builder.get_object("box_team")
        self.name_gtk=self.builder.get_object("name_team")
        self.name_gtk.set_text(self.team.name)
        self.builder.connect_signals(self)        

        self.player_list = []
        self.player_map = {}
        self.combo_players=Gtk.ListStore(int, str)
        combo_renderer = Gtk.CellRendererText()
        self.builder.get_object("combo_queue_att").set_model(self.combo_players)
        self.builder.get_object("combo_queue_att").pack_start(combo_renderer, True)
        self.builder.get_object("combo_queue_att").add_attribute(combo_renderer, 'text',1)
        self.builder.get_object("combo_queue_dif").set_model(self.combo_players)
        self.builder.get_object("combo_queue_dif").pack_start(combo_renderer, True)
        self.builder.get_object("combo_queue_dif").add_attribute(combo_renderer, 'text',1)
        self.combos = [self.builder.get_object("combo_queue_att"),
                       self.builder.get_object("combo_queue_dif")]

        self.treeview_queue = self.builder.get_object("treeview_queue")
        self.treeview_queue.append_column(Gtk.TreeViewColumn("Attaccante", Gtk.CellRendererText(), text=0))
        self.treeview_queue.append_column(Gtk.TreeViewColumn("Difensore", Gtk.CellRendererText(), text=1))
        self.queue_model = self.builder.get_object("liststore_queue")
        self.queue_cache = None

    def goal_incr(self):
        self.core.act_goal(self.team)

    def goal_decr(self):
        self.core.act_goal_undo(self.team)

    def to_queue(self):
        player_a, player_b = map(lambda x: self.player_map[x.get_model()[x.get_active()][0]] if x.get_active() >= 0 else None, self.combos)
        if player_a is None or player_b is None:
            print >> sys.stderr, "> Cannot move to queue when one of the players is not chosen..."
        else:
            #self.core.act_team_change(self.team, player_a, player_b)
            self.core.act_add_to_queue(self.team, player_a, player_b)

    def promote(self):
        #(player_a_id, player_b_id), _ = self.treeview_queue.get_selection().get_selected()
        if len(self.core.queues[self.core.detect_team(self.team)]) == 0:
            print >> sys.stderr, "> Cannot promote when queue is empty"
        else:
            player_a, player_b = self.core.queues[self.core.detect_team(self.team)][0]
            self.core.act_team_change(self.team, player_a, player_b)
            self.core.act_remove_from_queue(self.team, 0)

    def swap(self, first, second):
        length = len(self.queue_model)
        if first >= 0 and second >= 0 and first < length and second < length:
            self.core.act_swap_queue(self.team, first, second)

    def swap_up(self):
        sel = self.get_selection_index()
        if sel is None:
            print >> sys.stderr, "> Error: no selection when swapping queue"
        else:
            self.swap(sel, sel-1)

    def swap_down(self):
        sel = self.get_selection_index()
        if sel is None:
            print >> sys.stderr, "> Error: no selection when swapping queue"
        else:
            self.swap(sel, sel+1)

    def on_btn_gol_plus_clicked (self, widget):
        self.goal_incr()

    def on_btn_gol_minus_clicked (self, widget):
        self.goal_decr()

    def on_btn_to_queue_clicked(self, widget):
        self.to_queue()

    def on_btn_queue_promote_clicked(self, widget):
        self.promote()

    def on_btn_swap_up_clicked(self, widget):
        self.swap_up()

    def on_btn_swap_down_clicked(self, widget):
        self.swap_down()

    def get_selection_index(self):
        selection = self.treeview_queue.get_selection()
        for i in xrange(len(self.queue_model)):
            if selection.iter_is_selected(self.treeview_queue.get_model().get_iter(Gtk.TreePath(i))):
                return i

    def regenerate(self):
        # Write score
        self.builder.get_object("points").set_text("%d" % (self.core.score[self.core.detect_team(self.team)]))

        # Write active players
        players = self.core.players[self.core.detect_team(self.team)]
        if players != [None, None]:
            for i in (("name_current_att",0),("name_current_dif",1)):
                self.builder.get_object(i[0]).set_text(players[i[1]].format_name())

        # Write queue
        if self.queue_cache != self.core.queues[self.core.detect_team(self.team)]:
            self.queue_cache = self.core.queues[self.core.detect_team(self.team)]
            self.queue_model.clear()
            for queue_element in self.core.queues[self.core.detect_team(self.team)]:
                self.queue_model.append(tuple(map(lambda x: x.id, queue_element)))

    def new_player_match(self, player_match):
        # Update player combo boxes
        if player_match.team == self.team:
            player = player_match.player
            # TODO - Bad hack, because I can't work out how to keep
            # the list sorted in a nicer way
            self.player_list.append((player.format_name(), player.id))
            self.player_list.sort()
            self.player_map[player.id] = player
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
        self.core.close()
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

if __name__ == "__main__":

    match_id = 4
    core = SubottoCore(match_id)
    main_window = Subotto24GTK(core)

    core.update()
    gi.repository.GObject.timeout_add(1000, core.update)

    Gtk.main()
