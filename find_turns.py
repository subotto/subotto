# -*- coding: utf-8 -*-
"""Script to create the turns file of a 24h."""

from data import Session, Event, Match, StatsTurn

import sys
import logging
import csv
import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s"
)
logger = logging.getLogger()


class Turn:
    """A single turn, ie. the time between two consecutive swaps."""

    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

    def __init__(self, players, score, begin, end):
        self.players = players[:]
        self.score = score[:]
        self.begin = begin
        self.end = end

    @staticmethod
    def from_csv_line(line):
        """Create a new instance from a csv line.

        The csv should have been created from the tuple representation of a
        Turn object.
        The parameter should be a list with an element for each item of
        the csv line, in the right order
        """
        score = (None, int(line[6]), int(line[7]))
        players = (None,
                   (int(line[2]), int(line[3])),
                   (int(line[4]), int(line[5])))
        return Turn(players, score,
                    datetime.datetime.strptime(line[0], Turn.DATETIME_FORMAT),
                    datetime.datetime.strptime(line[1], Turn.DATETIME_FORMAT))

    def __str__(self):
        return "Turn: {} - {}".format(self.begin, self.end)

    def __repr__(self):
        return ",".join(map(str, self.get_tuple()))

    def duration(self):
        """Compute duration of this turn in seconds."""
        return (self.end - self.begin).total_seconds()

    def get_tuple(self):
        """Get a tuple from this instance.

        The tuple contains (in order) begin timestamp, end timestamp, ids of
        the two team 1 players, ids of the two team 2 players, team 1 score,
        team 2 score.
        """
        return (self.begin.strftime(Turn.DATETIME_FORMAT),
                self.end.strftime(Turn.DATETIME_FORMAT),
                self.players[1][0], self.players[1][1],
                self.players[2][0], self.players[2][1],
                self.score[1], self.score[2])

    def get_stats_turn(self, match_id):
        """Get a DB StatsTurn object for this instance."""
        return StatsTurn(match_id=match_id,
                         p00_id=self.players[1][0], p01_id=self.players[1][1],
                         p10_id=self.players[2][0], p11_id=self.players[2][1],
                         score_a=self.score[1], score_b=self.score[2],
                         begin=self.begin, end=self.end)


class TurnsLoader:
    """Creates the list of turns."""

    def __init__(self, session, match_id, match=None):
        if match is not None:
            self.match = match
        else:
            self.match = session.query(Match).filter_by(id=match_id).one()
        self.load_goals(session)
        self.changes = session.query(Event).filter_by(
            match_id=self.match.id, type="change").order_by(
            Event.timestamp).all()
        self.turns = []
        self.current_players = [None, None, None]
        for _ in range(2):
            self.current_players[self.changes[0].team_id] = (
                self.changes[0].player_a_id, self.changes[0].player_b_id)
            self.changes.pop(0)
        self.goal_idxes = [None, 0, 0]
        self.score = [None, 0, 0]
        self.begin = self.match.begin

    def load_goals(self, session):
        """Get the list of goals of a single match from the DB.

        Set the field goals to a tuple of lists. At indexes 1, 2 (teams' ids)
        there are lists containing timestamps of each goal of that team not
        undone.
        """
        self.goals = (None, [], [])
        events = session.query(Event).filter_by(
            match_id=self.match.id).filter(
            Event.type.in_(("goal", "goal_undo"))).order_by(
            Event.timestamp).all()
        for goal in events:
            if goal.type == "goal":
                self.goals[goal.team_id].append(goal.timestamp)
            elif goal.type == "goal_undo":
                try:
                    self.goals[goal.team_id].pop()
                except IndexError:
                    logger.warning("Annulato goal alla squadra {} che non ne"
                                   " aveva: evento ignorato".format(
                                       goal.team_id))
            else:
                logger.warning("Trovato evento che non è né un goal né un"
                               " goal_undo: evento ignorato")

    def create_next_turn(self, change):
        """Crea il turno successivo, facendolo finire al timestamp passato.

        Questa funzione aggiorna lo stato dell'oggetto.
        """
        for k in (1, 2):
            while (self.goal_idxes[k] < len(self.goals[k])
                    and self.goals[k][self.goal_idxes[k]] < change.timestamp):
                self.score[k] += 1
                self.goal_idxes[k] += 1
        if self.score[1] == 0 and self.score[2] == 0:
            # It isn't a real turn
            self.current_players[change.team_id] = (
                change.player_a_id, change.player_b_id)
        else:
            # It's a real turn
            new_turn = Turn(
                self.current_players, self.score, self.begin, change.timestamp)
            self.begin = change.timestamp
            self.current_players[change.team_id] = (
                change.player_a_id, change.player_b_id)
            self.score = [None, 0, 0]
            return new_turn

    def create_last_turn(self):
        """Crea l'ultimo turno della 24ore."""
        fake_change = Event()
        fake_change.timestamp = self.match.end
        fake_change.team_id = 1
        fake_change.player_a_id = fake_change.player_b_id = 1
        return self.create_next_turn(fake_change)

    @staticmethod
    def append_maybe(l, e):
        """Append element e to list l only if e is not None."""
        if e is not None:
            l.append(e)

    def create_turns_list(self):
        """Crea la lista di tutti i turni di una 24h."""
        turns = []
        for change in self.changes:
            TurnsLoader.append_maybe(turns, self.create_next_turn(change))
        TurnsLoader.append_maybe(turns, self.create_last_turn())
        return turns


def usage():
    """Print usage and exit."""
    print "Usage: {} match_id [filename]".format(sys.argv[0])
    sys.exit(1)


if __name__ == "__main__":
    try:
        match_id = int(sys.argv[1])
    except IndexError, ValueError:
        usage()
    session = Session()
    match = session.query(Match).filter_by(id=match_id).one()

    turns = TurnsLoader(session, match_id, match=match).create_turns_list()

    # Write to csv
    filename = sys.argv[2] if len(sys.argv) > 2 else "turns{}.csv".format(
        match.begin.year)
    with open(filename, "wb") as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=",",
                               quotechar="'", quoting=csv.QUOTE_MINIMAL)
        for turn in turns:
            csvwriter.writerow(turn.get_tuple())
    # It's readonly on the db
    session.rollback()
    session.close()
