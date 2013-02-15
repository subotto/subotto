#!/usr/bin/python

import sys

player_id = sys.argv[1]

print "SELECT * FROM players WHERE id = %s;" % (player_id)
print "SELECT * FROM player_matches WHERE player_id = %s;" % (player_id)
print "SELECT * FROM events WHERE player_a_id = %s or player_b_id = %s;" % (player_id, player_id)
