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

from sgrk.ui import query_yes_no
from sgrk.llm import get_llm_response
from sgrk.cmdanalysis import analyse_command_output
from sgrk.cmdexec import execute_commands_remote

command = "debughost"
help = "Debug an issue by executing CLI tools and interpreting the output"


def add_to_command_parser(subparsers):
    parser = subparsers.add_parser(command, help=help)
    parser.add_argument("-p", "--problem-description", required=True,
                        help="A description of the problem you are investigating. Be as detailed as possible.")
    parser.add_argument("-t", "--target-host", required=True,
                        help="The host to connect to via ssh. Otherwise commands are run locally.")
    parser.add_argument("-e", "--explain-commands", action="store_true",
                        help="Print the explanations the LLM gives for each command it suggests")
    parser.add_argument("--print-summaries", action="store_true",
                        help="Include the command summaries in the final report")
    parser.add_argument("--yolo", action="store_true", default=False,
                        help="Run LLM suggested commands without confirmation")


def ask_llm_for_commands(problem_description):
    """Get a list of commands to run to solve the problem described by args.problem_description.

    Returns a list of strings, where each entry is a command to run and its arguments.
    """

    prompt = """I am a sysadmin. I am logged onto a machine that is experiencing a
problem. I need you to tell me what Linux commands to run to debug the problem.

Your task is to suggest a list of up to fifty Linux command line tools that I should run
that will provide information I can use to debug this problem. For each command line tool you must explain
how it will help debug the problem. You should format your output as JSON. Return a JSON dictionary
where the keys are the commands and their arguments and the values are the explanation of how
that command will help debug the problem.

Be aware that there may be more than one process with the same name running on the system, so commands like
pidof may return multiple process IDs.

All commands that you suggest must exit after a maximum of 10 seconds. You must provide the arguments
to the command that will cause it to exit before this time limit.

I must be able to run every command you suggest directly from the command line (e.g. from bash). You must
prefix any command that require elevated privileges with "sudo".

Do not suggest any commands that would start or stop any services or edit the configuration of existing services
running on the host.

I will run the commands you suggest verbatim, so you must never suggest an argument to a command that is a
placeholder that needs to be replaced. If a command line tool requires a port or a process ID then the
command you generate must calculate this value via command substitution or some other mechanism.

Here is an example. I will specify the problem. You will tell me the command line tools to run to debug it. This
example has four command line tools, but you should respond with fifty if you can. It is OK to respond with fewer
if there are fewer than fifty commands that are likely to be useful.

The commands you generate will be put in a JSON string, so ensure they are escaped correctly.

Problem: Applications on the host are running slowly
Command line tools: {{
    "uptime": "This command displays the time the system has been running without a restart, the number of users currently logged in, and the system load averages for the past 1, 5, and 15 minutes. If the load average is higher than your CPU count, it can indicate your system is overloaded which might be causing your application slowdown.",
    "top -n1 -b": "This command provides a dynamic real-time view of the running system. It displays system summary information and a list of tasks currently being managed by the kernel. The '-n1 -b' options make it run only once, in batch mode. This output helps identify processes that are consuming excessive CPU, memory, and other resources, which could be contributing to the slow performance.",
    "ps -ef": "This command provides a snapshot of all current processes. It can help identify any unexpected or resource-intensive processes that could be impacting the performance of your applications.",
    "journalctl -b -p warning --no-pager": "This command fetches and displays system logs from the current boot, with a priority level of warning or higher, and without using a pager (like less or more). It will be useful to check for any system or application warnings or errors that might indicate why the applications are running slow.",
}}

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

    logging.info("LLM suggested running the following commands: ")
    for cmd, reason in commands.items():
        if args.explain_commands:
            logging.info(f"    {cmd} - {reason}")
        else:
            logging.info(f"    {cmd}")
            logging.debug(f"        {reason}")

    if not args.yolo:
        if not query_yes_no("Allow execution of the above commands with sudo?"):
            logging.error("Permission denied. Exiting.")
            return -1

    logging.info(f"{len(commands)} commands in total to execute ...")

    command_output = execute_commands_remote(args.target_host, commands.keys())
    analyse_command_output(command_output, args.problem_description, args.print_summaries)
