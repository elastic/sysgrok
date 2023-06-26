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

import json
import logging
import sys

from perfcopilot.ui import query_yes_no
from perfcopilot.llm import get_llm_response
from perfcopilot.cmdanalysis import analyse_command_output
from perfcopilot.cmdexec import execute_commands_remote

command = "debughost"
help = "Debug an issue by executing CLI tools and interpreting the output"


def add_to_command_parser(subparsers):
    parser = subparsers.add_parser(command, help=help)
    parser.add_argument("-p", "--problem-description", required=True,
                        help="A description of the problem you are investigating. Be as detailed as possible.")
    parser.add_argument("-t", "--target-host", required=True,
                        help="The host to connect to via ssh. Otherwise commands are run locally.")
    parser.add_argument("--print-summaries", action="store_true",
                        help="Include the command summaries in the final report")
    parser.add_argument("--yolo", action="store_true", default=False,
                        help="Run LLM suggested commands without confirmation")


def ask_llm_for_commands(problem_description):
    """Get a list of commands to run to solve the  problem described by args.problem_description.

    Returns a list of strings, where each entry is a command to run and its arguments.
    """

    prompt = """I am a sysadmin. I am logged onto a machine that is experiencing a
problem. I need you to tell me what Linux commands to run to debug the problem.

Your task is to suggest a list of up to ten Linux commands that I should run
that will provide information I can use to debug this problem.
You should format your output as JSON.

You must never suggest a command that has a placeholder for a port or pid. e.g. <port> or <pid> must
never appear in the suggested command, or any other placeholder.

All commands that you suggest must exit after a maximum of 10 seconds. You must provide the arguments
to the command that will cause it to exit before this time limit.

Here is an example. I will specify the problem. You will tell me the commands to run to debug it.

Problem: Applications on the host are running slowly
Commands: ["uptime", "top -n1 -b", "ps -ef", "journalctl -b -p warning --no-pager", "vmstat", "mpstat",
"free -m", "dmesg | tail -50"]

Problem: {problem}
Commands:"""

    return json.loads(get_llm_response(prompt.format(problem=problem_description)))


def run(args_parser, args):
    if args.chat:
        logging.error(f"Chat not implemented for {command}")
        sys.exit(1)

    logging.info("Querying the LLM for commands to run ...")
    commands = ask_llm_for_commands(args.problem_description)
    if not commands:
        sys.stderr.write("LLM did not return any commands to run")
        return -1

    for cmd, reason in commands.items():
        logging.debug(f"{cmd} - {reason}")

    logging.info("LLM suggested running the following commands: ")
    for cmd in commands:
        logging.info(f"    {cmd}")

    if not args.yolo:
        if not query_yes_no("Allow execution of the above commands with sudo?"):
            logging.error("Permission denied. Exiting.")
            return -1

    logging.info(f"{len(commands)} commands in total to execute ...")

    command_output = execute_commands_remote(args.target_host, commands.keys())
    analyse_command_output(command_output, args.problem_description, args.print_summaries)
