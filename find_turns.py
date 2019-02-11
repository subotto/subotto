# -*- coding: utf-8 -*-
"""Script to create the turns file of a 24h

"""

from data import Session, Event, Match #Player
from core import SubottoCore

import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s"
)
logger = logging.getLogger()

class Turn:
    """A single turn, ie. the time between two consecutive swaps"""

    def __init__(self, players, score, begin, end):
        self.players = players
        self.score = score
        self.begin = begin
        self.end = end

    def __str__(self):
        return "Turn: {} - {}".format(self.begin, self.end)

    def toTuple(self):
        """Get a tuple from this instance

        The tuple contains (in order) begin timestamp, end timestamp, ids of
        the two team 1 players, ids of the two team 2 players, team 1 score,
        team 2 score
        """
        pass
        # echo $turn->begin . "," . $turn->end . ", " . $turn->players["1"][0] . "," . $turn->players["1"][1] . "," . $turn->players["2"][0] . "," . $turn->players["2"][1] . "," . $turn->score[1] . "," . $turn->score[2] . "\n";


def load_goals(session, match_id):
    """Get the list of goals of a single match from the DB

    Return a tuple of lists. At indexes 1, 2 (teams' ids) there are lists
    containing timestamps of each goal of that team not undone.
    """
    goals = (None, [], [])
    # SELECT * FROM events WHERE match_id = $i AND type IN ('goal', 'goal_undo') ORDER BY timestamp
    events = session.query(Event).filter_by(match_id=match_id).filter(
        Event.type.in_(("goal", "goal_undo"))).order_by(Event.timestamp).all()
    for goal in events:
        if goal.type == "goal":
            goals[goal.team_id].append(goal.timestamp)
        elif goal.type == "goal_undo":
            try:
                goals[goal.team_id].pop()
            except IndexError:
                logger.warning("Annulato goal alla squadra {} che non ne aveva: evento ignorato".format(
                        goal.team_id))
        else:
            logger.warning("Trovato evento che non è né un goal né un goal_undo: evento ignorato")
    return goals

def usage():
    """Print usage and exit"""
    print "Usage: {} match_id".format(sys.argv[0])
    sys.exit(1)

if __name__ == "__main__":
    try:
        match_id = int(sys.argv[1])
    except IndexError, ValueError:
        usage()
    session = Session()

    match = session.query(Match).filter_by(id=match_id).one()
    goals = load_goals(session, match_id)
    changes = session.query(Event).filter_by(
        match_id=match_id, type="change").order_by(Event.timestamp).all()
    turns = []
    current_players = [None, None, None]
    for j in range(2):
        current_players[changes[j].team_id] = (changes[j].player_a_id, changes[j].player_b_id)
    changes.pop(0)
    changes.pop(0)
    goal_idxes = [None, 0, 0]
    score = [None, 0, 0]
    begin = match.begin

    for change in changes:
        # guardo cosa succede prima di questo cambio
        for k in (1, 2):
            while (goal_idxes[k] < len(goals[k])
                    and goals[k][goal_idxes[k]] < change.timestamp):
                score[k] += 1
                goal_idxes[k] += 1
        if score[1] == 0 and score[2] == 0:
            # It isn't a real turn
            current_players[change.team_id] = (change.player_a_id, change.player_b_id)
        else:
            # It's a real turn
            end = change.timestamp
            turns.append(Turn(current_players, score, begin, end))

            begin = end
            current_players[change.team_id] = (change.player_a_id, change.player_b_id)
            score = [None, 0, 0]
    # Add the last turn
    turns.append(Turn(current_players, score, begin, match.end))
    for turn in turns:
        print(turn)

    session.close()
