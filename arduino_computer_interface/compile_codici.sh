#!/bin/bash

cat codici | grep -v '^#' | grep -v '^$' | sed -e 's|\([^ ]*\) \([^ ]*\) \([^ ]*\)|\3 = \2|' > opcodes.py
