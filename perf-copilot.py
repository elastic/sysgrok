#!/usr/bin/env python

# perf-copilot is an experimental tool for performance analysis and optimisation
# using LLMs. Its purpose is to take data from existing profilers and provide
# the user with helpful summaries, advice and direction.
#
# Author: Sean Heelan
# Email: sean@heelan.io

from perfcopilot.llm import LLMConfig, set_config
from perfcopilot.commands import (
    analyzecmd,
    code,
    debughost,
    explainfunction,
    explainprocess,
    findfaster,
    stacktrace,
    topn
)

import argparse
import logging
import os
import sys

import openai

from dotenv import load_dotenv
load_dotenv()

openai.api_key = os.environ["OPENAI_API_KEY"]


ascii_name = """
                  __                       _ _       _
                 / _|                     (_) |     | |
 _ __   ___ _ __| |_ ______ ___ ___  _ __  _| | ___ | |_
| '_ \ / _ \ '__|  _|______/ __/ _ \| '_ \| | |/ _ \| __|
| |_) |  __/ |  | |       | (_| (_) | |_) | | | (_) | |_
| .__/ \___|_|  |_|        \___\___/| .__/|_|_|\___/ \__|
| |                                 | |
|_|                                 |_|

Performance analysis and optimisation with LLMs
"""

if __name__ == "__main__":
    commands = {
        analyzecmd.command: analyzecmd,
        code.command: code,
        explainfunction.command: explainfunction,
        explainprocess.command: explainprocess,
        debughost.command: debughost,
        findfaster.command: findfaster,
        stacktrace.command: stacktrace,
        topn.command: topn
    }

    parser = argparse.ArgumentParser(
        prog=sys.argv[0],
        description=ascii_name,
        epilog="",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-d", "--debug", action="store_true", help="Debug output")
    parser.add_argument("-e", "--echo-input", action="store_true",
                        help="""Echo the input provided to perf-copilot. Useful when input is piped in
    and you want to see what it is""")

    parser.add_argument("--output-format", type=str, help="Specify the output format for the LLM to use")
    parser.add_argument("-m", "--model", default="gpt-3.5-turbo",
                        help="""The OpenAI model to use. Must be one of the chat completion models.
    See https://platform.openai.com/docs/models/model-endpoint-compatibility for valid options.""")
    parser.add_argument("--temperature", type=float, default=0, help="ChatGPT temperature. See OpenAI docs.")
    parser.add_argument("--max-concurrent-queries", type=int, default=4,
                        help="Maximum number of parallel queries to OpenAI")

    subparsers = parser.add_subparsers(help="The sub-command to execute", dest="command")
    for v in commands.values():
        v.add_to_command_parser(subparsers)

    args = parser.parse_args()

    log_format = '%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s'
    log_date_format = '%Y-%m-%d %H:%M:%S'
    log_level = logging.INFO

    if args.debug:
        log_level = logging.DEBUG

    logging.basicConfig(format=log_format, datefmt=log_date_format, level=log_level)

    set_config(LLMConfig(args.model, args.temperature, args.max_concurrent_queries, args.output_format))

    if not args.command:
        parser.print_help(sys.stderr)
        sys.stderr.write("\nNo sub-command selected\n")
        sys.exit(1)

    if args.command not in commands:
        parser.print_help(sys.stderr)
        sys.stderr.write("\nUnknown sub-command\n")
        sys.exit(1)

    sys.exit(commands[args.command].run(parser, args))
