#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import time
import requests, json
import traceback

from listener import Statistics
from data import Session, Team, Player, Match, PlayerMatch, Event, StatsPlayerMatch, Base, AdvantagePhase

SLEEP_TIME = 0.5


with open('passwd_web') as fpasswd:
    PASSWD = fpasswd.read().strip()



def listen_match(match_id, old_matches_id, post_url):

    session = Session()

    match = session.query(Match).filter(Match.id == match_id).one()
    old_matches = session.query(Match).filter(Match.id.in_(old_matches_id)).all()
    players = session.query(Player).all()
    old_player_matches = session.query(PlayerMatch).filter(PlayerMatch.match_id.in_(old_matches_id)).all()
    old_events = session.query(Event).filter(Event.match_id.in_(old_matches_id)).order_by(Event.timestamp).all()
    old_stats_player_matches = session.query(StatsPlayerMatch).filter(StatsPlayerMatch.match_id.in_(old_matches_id)).all()

    stats = Statistics(match, old_matches, players, old_player_matches, old_events, old_stats_player_matches)
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

            # Send data to the web server
            stats.generate_current_data()
            data = stats.data
            headers = {'content-type': 'application/json'}
            json_data = json.dumps({'action': 'set', 'password': PASSWD, 'data': data})
            print json_data

            try:
                r = requests.post(post_url, data=json_data, headers=headers)
                print 'Request done', r.status_code
                print r.text
            except:
                print >> sys.stderr, "Exception caught, continuing..."
                traceback.print_exc()


            time.sleep(SLEEP_TIME)

    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    try:
        post_url = sys.argv[1]
    except IndexError:
        print "Missing POST URL. Maybe it is http://uz.sns.it/24ore/score ??"
        sys.exit(1)
    match_id = 16
    old_matches_id = [1, 2, 3, 4, 7, 8, 10, 12, 14]
    listen_match(match_id, old_matches_id, post_url)
