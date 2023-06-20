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
# 9
# vmlinux: entry_SYSCALL_64_after_hwframe
# vmlinux+0x100009a
# 8
# libc.so.6
# libc.so.6+0x114991
# 7
# libc.so.6: __GI__IO_file_xsgetn
# ./libio/fileops.c#1341

print("# Index | Process/Library | Function | File")
while i < len(data):
    index = data[i].strip()
    process_func_line = data[i+1].strip().split()
    process = process_func_line[0]

    # Remove training ':' if present in the process name
    if process.endswith(":"):
        process = process[:-1]

    if len(process_func_line) > 1:
        function = " ".join(process_func_line[1:])
    else:
        function = "Unknown function"

    if process == "vmlinux" or data[i+2].find("+0x") != -1:
        file = "Unknown file"
    else:
        file = data[i+2].strip().split('#')[0]

    print(f"{index} | {process} | {function} | {file}")
    i += 3
