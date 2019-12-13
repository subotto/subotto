#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

from data import Team
from core import SubottoCore


def main():
    match_id = int(sys.argv[1])
    team_name = sys.argv[2]
    in_filename = sys.argv[3]

    core = SubottoCore(match_id)
    team = core.session.query(Team).filter(Team.name == team_name).one()
    with open(in_filename) as in_file:
        for line in in_file:
            line = line.strip()
            data = [x.strip() for x in line.split(',')]
            if len(data) == 3:
                fname, lname, comment = data
                if comment == '':
                    comment = None
            else:
                fname, lname = data
                comment = None
            core.act_add_player_match_from_name(team, fname, lname, comment, bulk=True)
    core.session.commit()


if __name__ == '__main__':
    main()
