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

import sys
import argparse

from sgrk.llm import print_streamed_llm_response, chat


command = "stacktrace"
help = "Summarise a stack trace and suggest changes to optimise the software"


def add_to_command_parser(subparsers):
    parser = subparsers.add_parser(command, help=help)
    parser.add_argument(
        'infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin,
        help="The file containing the stack trace. Defaults to stdin.")


prompt = """You are assisting me with understanding a stack trace from a software profiler, such
as pprof or perf record. My goal is to improve the software so that it runs faster and is more
efficient. A stack trace is a call stack, showing a list of functions that call each other. The
stack trace is in reverse order.

I will provide you with a stack trace which is reported by the profiler as consuming a
significant amount of CPU.

Assuming this stack trace is the most common stack trace encountered by a profiler,
suggest ways to optimize or improve the system to make it more efficient. Types of
improvements that would be useful to me are improvements that result in:

- Higher performance so that the system runs faster or uses less CPU
- Better memory efficient so that the system uses less RAM
- Better storage efficient so that the system stores less data on disk.
- Better network I/O efficiency so that less data is sent over the network
- Better disk I/O efficiency so that less data is read and written from disk

Make a maximum of five suggestions. Favour providing a small number of accurate, concise,
concrete, technically correct and actionable suggestions, over a larger number of ones that do
not have these properties.

Your suggestions must meet all of the following criteria:
1. Your suggestions should detailed, accurate, technical and include concrete examples.
2. Your suggestions should be specific to the provided stack trace. Only make suggestions which
are directly inspired by the content of the stack trace. Do not make generic suggestions.
3. If you suggest replacing the function or library with a more efficient replacement you must
suggest at least one concrete replacement.
4. If you suggest making code changes, then show a code snippet as an example of what you mean,
and explain why it is helpful.
5. Do not suggest making changes to functions that are in large public libraries, like libc, or
the Linux kernel.

If you know of fewer than five ways to improve the performance the system, then provide fewer
than five suggestions. If you do not know of any way in which to improve the performance then
say "No optimisation suggestions available".

Do not suggest to use a CPU profiler or to profile the code. I have already profiled the code
using a CPU profiler. You should favour stopping making suggestions over suggesting profiling
the code with a CPU profiler.

This is the stack trace:

{stacktrace}
"""


def run(args_parser, args):
    stacktrace = args.infile.read()
    if args.echo_input:
        print(stacktrace)

    conversation = print_streamed_llm_response(prompt.format(stacktrace=stacktrace))
    if args.chat:
        chat(conversation)
    return 0
