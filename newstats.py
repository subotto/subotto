#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import time

import core
from data import Event

MATCH_ID = 12

class Statistics:

    def __init__(self):
        self.players = {}
        self.current = []  # (current_a, current_b), where current_a = (player_a_id, player_b_id) and current_b is similar
        self.swapped = None
        self.turns = []    # (team_a, team_b, swapped, score), where team_a = (player_a_id, player_b_id), team_b is similar and score = (score_a, score_b)

    def new_player_match(self, player_match):
        self.players[player_match.player_id] = player_match.player

    def new_event(self, event):
        if event.type == Event.EV_TYPE_SWAP:
            if self.swapped is None:
                self.swapped = False
            else:
                self.swapped = not self.swapped

        elif event.type == Event.EV_TYPE_CHANGE:
            pass

        elif event.type == Event.EV_TYPE_GOAL:
            pass

        elif event.type == Event.EV_TYPE_GOAL_UNDO:
            pass

        elif event.type == Event.EV_TYPE_ADVANTAGE_PHASE:
            pass

        else:
            raise Exception("Wrong event type")

    def regenerate(self):
        pass

def main():
    match_id = MATCH_ID
    subcore = core.SubottoCore(match_id)
    stats = Statistics()
    subcore.listeners.append(stats)

    while True:
        time.sleep(1.0)
        subcore.update()

if __name__ == '__main__':
    main()

