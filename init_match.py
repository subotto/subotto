#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import datetime

from core import act_init_match


def main():
    name = sys.argv[1]

    sched_begin = datetime.datetime.strptime(sys.argv[2], '%Y-%m-%d %H:%M:%S')
    sched_end = datetime.datetime.strptime(sys.argv[3], '%Y-%m-%d %H:%M:%S')
    match_id = act_init_match(name, "Matematici", "Fisici", sched_begin, sched_end)
    print "> Created match with ID %d" % (match_id)


if __name__ == '__main__':
    main()
