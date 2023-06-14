import argparse
import logging
import sys

from perfcopilot import llm
from perfcopilot.cmdanalysis import summarise_command
from perfcopilot.cmdexec import execute_commands_remote


command = "analyzecmd"
help = "Summarise the output of a command, optionally with respect to a problem under investigation"


def add_to_command_parser(subparsers):
    parser = subparsers.add_parser(command, help=help)
    parser.add_argument("-p", "--problem-description", help="Optional description of the problem you are investigating")
    parser.add_argument("-t", "--target-host",
                        help="The host to connect to via ssh. Otherwise command is run locally.")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="The command to execute and analyze")


def get_summary_max_chars():
    model = llm.get_model()
    if model == "gpt-3.5-turbo":
        max_tokens = 4096
    elif model == "gpt-4":
        max_tokens = 8192
    else:
        logging.error(f"Unknown model: {model}")
        sys.exit(-1)

    # Hard code the character to token ratio for now.
    return max_tokens * 2.5


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

    max_chars = get_summary_max_chars()
    _, summary = summarise_command(args.command, command_output[args.command], max_chars, args.problem_description)
    print(summary)
    return 0
