#!/usr/bin/env python

# Script for converting from the format you get when you copy/paste from the
# Elastic Universal Profiler Functions page to a more structured format with
# a header that the LLM will have an easier time making sense of.

import sys

with open(sys.argv[1]) as fd:
    data = fd.readlines()

i = 0
lines = []

# Data looks like this
# 3
# JVM/Hotspot: java.lang.String com.fasterxml.jackson.dataformat.cbor.CBORParser._finishShortText(int)
# CBORParser.java#2258
# 2,706,357
# 2.38%
# 2.40%
# 4
# JVM/Hotspot: org.logstash.ackedqueue.SequencedList org.logstash.ackedqueue.io.MmapPageIOV2.read(long, int)
# MmapPageIOV2.java#113
# 2,017,137
# 1.77%
# 2.43%
# 5
# ...
# 7
# vmlinux: __lock_text_start
# vmlinux+0xaf8a54
# 1,717,616
# 1.51%
# 1.51%

print("# Index | Process/Library | Function | File | Self CPU | Self+Children CPU")
while i < len(data):
    index = data[i].strip()
    process_func_line = data[i+1].strip().split()
    process = process_func_line[0][:-1]
    if process == "vmlinux":
        function = " ".join(process_func_line[1:])
        file = ""
    else:
        function = " ".join(process_func_line[2:])
        file = data[i+2].strip()

    self_cpu = data[i+4].strip()
    self_child_cpu = data[i+5].strip()

    print(f"{index} | {process} | {function} | {file} | {self_cpu} | {self_child_cpu}")
    i += 6
