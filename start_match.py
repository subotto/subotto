#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

from core import SubottoCore


def main():
    if len(sys.argv) != 3:
        print "Usage: {} match_id [start|end]".format(sys.argv[0])
        sys.exit(1)
    match_id = int(sys.argv[1])
    action = sys.argv[2]

    core = SubottoCore(match_id)
    if action == "start":
        core.act_begin_match()
    elif action == "end":
        core.act_end_match()
    else:
        print "Usage: {} match_id [start|end]".format(sys.argv[0])
        sys.exit(1)


if __name__ == '__main__':
    main()
