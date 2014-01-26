#! /usr/bin/env python2.7


import sys
import psycopg2
import datetime 
import os
from select import select
now=datetime.datetime.now

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

class SubottoGoal(object):
    def __set__(self, owner_inst, value):
        owner_inst.builder.get_object("points").set_text(str(value))
    def __get__(self, owner_inst, owner_class):
        if owner_inst is not None:
            try:
                return int(owner_inst.builder.get_object("points").get_text())
            except ValueError:
                return 0
        else: 
            return 0
    



class PGSubotto(object):
    def __init__ (self, **connoptions):
        self.conndict={'database' :'subotto', 'user': 'subotto', 'host' : 'roma.uz.sns.it', 'port' : 5432, 'password' : 'iPh6Ool7ee', 'sslmode' : 'require'}
        self.conndict.update(connoptions)
        self.conn=psycopg2.connect(**(self.conndict))
    
    def opencur(self):
        try:
            cur=self.conn.cursor()
        except psycopg2.InterfaceError as err:
            debug(str(err),0)
            debug("Trying to reopen connection",0)
            self.reopen();
        cur=self.conn.cursor()
        return cur
    
    def teamid_get(self, name):
            cur=self.opencur()
            cur.execute("""SELECT id from teams WHERE name = %s""", (name,))
            self.conn.commit()
            return cur.fetchone()[0]
    
    def goal_get(self, teamname):
        teamid=self.teamid_get(teamname)
        cur=self.opencur()
        cur.execute("""SELECT COUNT(1) FROM events WHERE type='goal' AND param= %s""", (str(teamid),))
        fatti=cur.fetchone()[0]        
        cur.execute("""SELECT COUNT(1) FROM events WHERE type='goal_undo' AND param= %s""", (str(teamid),))
        anullati=cur.fetchone()[0]        
        self.conn.commit()
        return fatti-anullati
       
    def goal_add(self, teamname):
        teamid=self.teamid_get(teamname)
        cur=self.opencur()
        cur.execute("""INSERT INTO events (timestamp,type, param) VALUES (%s,'goal', %s)""", (now(), str(teamid)) )
        self.conn.commit()

    def goal_undo(self, teamname):
        teamid=self.teamid_get(teamname)
        cur=self.opencur()
        cur.execute("""INSERT INTO events (timestamp,type, param) VALUES (%s,'goal_undo', %s)""", (now(), str(teamid)) )
        self.conn.commit()
    
    def swap (self, redteam, blueteam):
        redid=self.teamid_get(redteam)
        blueid=self.teamid_get(blueteam)
        cur=self.opencur()
        cur.execute("""INSERT INTO events (timestamp,type, param) VALUES (%s,'swap', %s)""", (now(), str(redid)+","+str(blueid)) )
        self.conn.commit()

    def teamorder_get (self):
        cur=self.opencur()
        cur.execute("""SELECT param FROM events WHERE type='swap' ORDER BY timestamp desc LIMIT 1""")
        order=cur.fetchone()
        self.conn.commit()
        debug("Order: "+ str(order), 100)
        if order is not None:
            order=order[0]
        else:
            return (None,None)
        return tuple(int (s) for s in str(order).split(','))
        
    def change (self, teamname, attplayerid, defplayerid):
        teamid=self.teamid_get(teamname)
        cur=self.opencur()
        cur.execute("""INSERT INTO events (timestamp,type, param) VALUES (%s,'change', %s)""", (now(), str(teamid)+','+str(attplayerid)+','+str(defplayerid)) )
        self.conn.commit()
        
    def currentplayers_get(self, teamname):
        teamid = self.teamid_get(teamname)
        cur = self.opencur()
        cur.execute("""SELECT param FROM events WHERE type='change' AND param LIKE '"""+str(teamid)+""",%' ORDER BY timestamp desc LIMIT 1""")
        self.conn.commit()
        param = cur.fetchone()
        debug("Last change param for team "+teamname+" :  "+ str(param),20)
        if param is not None:
            param=list(int(s) for s in str(param[0]).split(','))
            return param[1:]
        else:
            return [None, None]

    def playername_get(self,playerid):
        cur = self.opencur()
        cur.execute("""SELECT fname, lname FROM players WHERE id= %s""",(playerid,))
        self.conn.commit()
        result = cur.fetchone()
        return {'fname':str(result[0]), 'lname': str(result[1]), 'fullname': str(result[0])+" "+str(result[1])}

    def teamplayersid_get(self,teamname):
        teamid=self.teamid_get(teamname)
        cur = self.opencur()
        cur.execute("""SELECT id, fname, lname FROM players WHERE teamid= %s ORDER BY lname,fname""",(teamid,))
        self.conn.commit()
        result = cur.fetchall()
        return list( 
            {'id': player[0], 'fname': player[1], 'lname': player[2],'fullname': player[1]+" "+player[2]}
            for player in result
            )
        
    def reopen(self):
        if not self.conn.closed:
            self.conn.close()
        self.conn= psycopg2.connect(**(self.conndict))


class SubottoPlayers(object):
    currentplayerids=[]
    def __set__ (self, owner_inst, value):
        currentplayerids=value
        for i in (("name_current_att",0),("name_current_dif",1)):
            owner_inst.builder.get_object(i[0]).set_text(owner_inst.pgs.playername_get(currentplayerids[i[1]])['fullname'])
    def __get__ (self, owner_inst, owner_class):
        return self.currentplayerids

class SquadraSubotto(object):
    gol=SubottoGoal()
    currentplayers=SubottoPlayers()
    players=[]
    name=None
    def __init__ (self,name="Squadra Ignota",file="subotto24.glade"):
        self.name=name
        self.builder=Gtk.Builder()
        self.builder.add_objects_from_file(file,["box_team","im_queue_promote","im_gol_plus","im_gol_minus"])

        self.box=self.builder.get_object("box_team")
        self.name_gtk=self.builder.get_object("name_team")
        self.name_gtk.set_text(self.name)
        self.builder.connect_signals(self)        
        
        self.combo_players=Gtk.ListStore(int,str)
        combo_renderer = Gtk.CellRendererText()
        self.builder.get_object("combo_queue_att").set_model(self.combo_players)
        self.builder.get_object("combo_queue_att").pack_start(combo_renderer, True)
        self.builder.get_object("combo_queue_att").add_attribute(combo_renderer, 'text',1)

        self.builder.get_object("combo_queue_dif").set_model(self.combo_players)
        self.builder.get_object("combo_queue_dif").pack_start(combo_renderer, True)
        self.builder.get_object("combo_queue_dif").add_attribute(combo_renderer, 'text',1)


    def goal_incr(self,owner_inst):
        self.pgs.goal_add(self.name)
        self.update()
        debug(owner_inst.name+": Gol!    Totale: "+str(self.gol),3)

    def goal_decr(self,owner_inst):
        self.pgs.goal_undo(self.name)
        self.update()
        debug(owner_inst.name+": Gol annullato!   Totale: "+str(self.gol),3)

    def goal_update(self):
        self.gol=self.pgs.goal_get(self.name)
    def current_players_update(self):
        debug("Current playerids of team "+self.name+" : "+str(self.pgs.currentplayers_get(self.name)),30)
        self.currentplayers=self.pgs.currentplayers_get(self.name)
    def update_player_list(self):
        self.players = self.pgs.teamplayersid_get(self.name)
        for player in self.players:
            if (player['id'], player['fullname']) not in ( (p[0], p[1]) for p in self.combo_players):
                self.combo_players.append((player['id'], player['fullname']))                
        debug(self.name+" : "+str(self.players),40)
    def promote(self):
        combo=dict()
        player=dict()
        for i in ('att','dif'):
            combo[i]=self.builder.get_object("combo_queue_"+i)
            player[i]=combo[i].get_model()[combo[i].get_active()]
        self.pgs.change(self.name,player['att'][0],player['dif'][0])
        debug(self.name+" promoting : "+ str(player['att'][1]) + " and " + str(player['dif'][1])  ,20)

    def on_btn_gol_plus_clicked (self, widget):
        self.goal_incr(self)
    def on_btn_gol_minus_clicked (self, widget):
        self.goal_decr(self)
    def on_btn_queue_promote_clicked(self, widget):
        self.promote()
    def update(self):
        self.goal_update()
        self.current_players_update()
        self.update_player_list()


class Subotto24GTK(object):
    team=dict()
    team_slot=dict()
    def __init__ (self,file="subotto24.glade"):
        gi.repository.GObject.timeout_add(10000,self.update)
        self.pgs=PGSubotto()
        self.builder=Gtk.Builder()
        self.builder.add_objects_from_file(file,["window_subotto_main","im_team_switch"])

        self.window=self.builder.get_object("window_subotto_main")
        
        self.team_slot["red"]=self.builder.get_object("box_red_slot")
        self.team_slot["blue"]=self.builder.get_object("box_blue_slot")

	#self.fotocellule=open('fotocellule.fifo')
        #gi.repository.GObject.timeout_add(500,self.leggi_fotocellula)

        self.builder.connect_signals(self)

    def select_wrapper(self, fd):
        readable, writable, exeptionable = select([fd], [], [], 0.0)
        return len(readable) == 1
 	0
    def leggi_fotocellula(self):
	print "Leggendo fotocellule: "
        while self.select_wrapper(self.fotocellule):
		line = self.fotocellule.readline()
	#for line in self.fotocellule:
		print "Got line:"
		print repr(line)
		if line=="1\n":
			self.team['blue'].goal_incr(self.team['blue'])
			print "Goal blu"
		if line=="3\n":
			self.team['red'].goal_incr(self.team['red'])
			print "Goal rosso"
		if line=='':
			break 
	return True
    def set_team(self, team, color):
        self.team[color]=team
        self.team[color].pgs=self.pgs
        self.update_teams()

    def switch_teams(self):
        self.pgs.swap(self.team["blue"].name, self.team["red"].name)
        self.update_teams()

    def update_teams(self):
        order=self.pgs.teamorder_get()
        debug("Order from psql: " +str(order), 15)

        team_tmp=dict(self.team)

        
        for i in team_tmp:
            if self.pgs.teamid_get(team_tmp[i].name)==order[0]:
                self.team["red"]=team_tmp[i]
            if self.pgs.teamid_get(team_tmp[i].name)==order[1]:
                self.team["blue"]=team_tmp[i]
        for tname in self.team:
            debug(tname + " : " + self.team[tname].name, 20 )

        for color in self.team.keys():
            if self.team[color].box.get_parent() is None:
                self.team_slot[color].add(self.team[color].box)
            else:
                self.team[color].box.reparent(self.team_slot[color])
            self.team[color].update()
                              
            # self.team_slot[color].add(self.team[color].box)
            
        
            
    def on_window_destroy (self, widget):
        Gtk.main_quit()

    def on_btn_switch_clicked (self, widget):
        debug("Cambio!", 2)
        self.switch_teams()
    def update(self):
        debug("Updating!",20)
        self.update_teams()
        return True

if __name__ == "__main__":

    matematici=SquadraSubotto("Matematici")
    fisici=SquadraSubotto("Fisici")
    
    main_window = Subotto24GTK()

    main_window.set_team(matematici, "red")
    main_window.set_team(fisici, "blue")
    
    Gtk.main()
