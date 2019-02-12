# -*- coding: utf-8 -*-
"""Script to update statistics of a 24h."""

from data import Session, Match, StatsPlayerMatch
from find_turns import Turn

import sys
import logging
import csv

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s"
)
logger = logging.getLogger()


class PlayerInfo():
    """Player's informations for this partecipation."""

    def __init__(self, player_id, team):
        self.id = player_id
        self.team = team
        self.pos_goals = 0
        self.neg_goals = 0
        self.seconds = 0
        self.turns = 0

    def __repr__(self):
        return ("("
                + ",".join(map(str, (self.id, self.team, self.pos_goals,
                                     self.neg_goals, self.seconds, self.turns
                                     )))
                + ")")

    def get_player_match(self, match_id):
        """Get a DB StatsPlayerMatch object for this instance."""
        return StatsPlayerMatch(player_id=self.player_id,
                                match_id=match_id,
                                team_id=self.team,
                                pos_goals=self.pos_goals,
                                neg_goals=self.neg_goals,
                                seconds=self.seconds,
                                turns=self.turns)


def usage():
    """Print usage and exit."""
    print "Usage: {} match_id filename".format(sys.argv[0])
    sys.exit(1)


if __name__ == "__main__":
    try:
        match_id = int(sys.argv[1])
        filename = sys.argv[2]
    except IndexError, ValueError:
        usage()
    session = Session()
    players = {}

    # Load turns from csv file
    turns = []
    with open(filename, "rb") as csvfile:
        csvreader = csv.reader(csvfile, delimiter=",", quotechar="'")
        for row in csvreader:
            turn = Turn.from_csv_line(row)
            turns.append(turn)
            for team in (1, 2):
                for player_id in turn.players[team]:
                    if player_id not in players:
                        players[player_id] = PlayerInfo(player_id, team)
    # print(turns)

    # Process turns
    final_score = [None, 0, 0]
    for turn in turns:
        for team in (1, 2):
            other_team = 1 if team == 2 else 2
            final_score[team] += turn.score[team]
            for player_id in turn.players[team]:
                players[player_id].pos_goals += turn.score[team]
                players[player_id].neg_goals += turn.score[other_team]
                players[player_id].turns += 1
                players[player_id].seconds += turn.duration()
    print(players.values())

    # Actual writing on the db
    # session.add_all(map(lambda turn: turn.get_stats_turn(match_id), turns))
    # session.add_all(map(lambda pl: pl.get_player_match(match_id),
    #                     players.values()))

    # It's readonly on the db
    session.rollback()
    session.close()
