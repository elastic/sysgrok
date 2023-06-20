#!/usr/bin/env python

# Licensed to Elasticsearch B.V. under one or more contributor
# license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright
# ownership. Elasticsearch B.V. licenses this file to you under
# the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

# Script for converting from the format you get when you copy/paste from the
# Elastic Universal Profiler Functions page to a more structured format with
# a header that the LLM will have an easier time making sense of.

import sys

with open(sys.argv[1]) as fd:
    data = fd.readlines()

i = 0
lines = []

# Data looks like this
# 1
# libc.so.6: _int_malloc
# ./malloc/malloc.c#4299
# 78
# 0.89%
# 1.20%
# ~0.00 lbs / ~0.00 kg
# ~0.00$
# show_more_information
# 2
# cc1: bitmap_set_bit(bitmap_head*, int)
# ../../src/gcc/bitmap.c#969
# 72
# 0.82%
# 0.83%
# ~0.00 lbs / ~0.00 kg
# ~0.00$
# show_more_information
# 3
# vmlinux: clear_page_erms
# vmlinux+0x778936
# 67
# 0.76%
# 0.76%
# ~0.00 lbs / ~0.00 kg
# ~0.00$
# show_more_information

print("# Index | Process/Library | Function | File | Self CPU | Self+Children CPU")
while i < len(data):
    index = data[i].strip()
    process_func_line = data[i+1].strip().split()
    process = process_func_line[0][:-1]
    if process == "vmlinux":
        function = " ".join(process_func_line[1:])
        file = ""
    else:
        function = " ".join(process_func_line[1:])
        file = data[i+2].strip()

    self_cpu = data[i+4].strip()
    self_child_cpu = data[i+5].strip()

    print(f"{index} | {process} | {function} | {file} | {self_cpu} | {self_child_cpu}")
    i += 9
