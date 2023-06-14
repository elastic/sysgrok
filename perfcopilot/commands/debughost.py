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

    logging.info("LLM suggested running the following commands: ")
    for c in commands:
        logging.info(f"    {c}")

    if not args.yolo:
        if not query_yes_no("Allow execution of the above commands with sudo?"):
            logging.error("Permission denied. Exiting.")
            return -1

    logging.info(f"{len(commands)} commands in total to execute ...")

    command_output = execute_commands_remote(args.target_host, commands)
    analyse_command_output(command_output, args.problem_description, args.print_summaries)
