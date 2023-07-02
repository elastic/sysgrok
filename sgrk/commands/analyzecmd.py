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

import argparse
import logging
import sys

from sgrk.cmdanalysis import summarise_command
from sgrk.cmdexec import execute_commands_remote


command = "analyzecmd"
help = "Summarise the output of a command, optionally with respect to a problem under investigation"


def add_to_command_parser(subparsers):
    parser = subparsers.add_parser(command, help=help)
    parser.add_argument("-p", "--problem-description", help="Optional description of the problem you are investigating")
    parser.add_argument("-t", "--target-host", required=True,
                        help="The host to connect to via ssh. Otherwise command is run locally.")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="The command to execute and analyze")


def run(args_parser, args):
    if args.chat:
        logging.error(f"Chat not implemented for {command}")
        sys.exit(1)

    if not args.command:
        logging.error("Command not provided")
        sys.exit(1)

    if args.command[0] == '--':
        args.command = args.command[1:]

    args.command = " ".join(args.command)
    logging.debug(f"Analyzing command: {args.command}")

    command_output = execute_commands_remote(args.target_host, [args.command])

    if args.command not in command_output:
        logging.error(f"Failed to execute {args.command}")
        sys.exit(1)

    _, summary = summarise_command(args.command, command_output[args.command],
                                   problem_description=args.problem_description)
    print(summary)
    return 0
