#!/bin/bash

cat ../../arduino_computer_interface/codici | grep -v '^#' | grep -v '^$' | sed -e 's|\([^ ]*\) \([^ ]*\) \([^ ]*\)|#define \3 \2|' > opcodes.h
