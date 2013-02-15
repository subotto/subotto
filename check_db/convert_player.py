#!/usr/bin/python

import sys

from_player_id = sys.argv[1]
to_player_id = sys.argv[2]

print "UPDATE events SET player_a_id = %s WHERE player_a_id = %s;" % (to_player_id, from_player_id)
print "UPDATE events SET player_b_id = %s WHERE player_b_id = %s;" % (to_player_id, from_player_id)

# PlayerMatches have to be fixed manually (particularly, to check they're in the same team)
print "SELECT * FROM player_matches WHERE player_id = %s;" % (to_player_id)
print "SELECT * FROM player_matches WHERE player_id = %s;" % (from_player_id)
