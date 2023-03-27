#!/usr/bin/env python

# perf-gpt is an experimental tool for performance analysis and optimisation
# using LLMs. Its purpose is to take data from existing profilers and provide
# the user with helpful summaries, advice and direction.
#
# Author: Sean Heelan
# Email: sean@heelan.io

from perfgpt.commands import (
    findfaster,
    topn
)

import argparse
import os
import sys

import openai

from dotenv import load_dotenv
load_dotenv()

openai.api_key = os.environ["OPENAI_API_KEY"]

commands = {
    findfaster.command: findfaster,
    topn.command: topn
}

parser = argparse.ArgumentParser(
    prog=sys.argv[0],
    description="Performance analysis and optimisation with LLMs"
)
parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
parser.add_argument("-d", "--debug", action="store_true", help="Debug output")
parser.add_argument("--temperature", type=float, default=0, help="ChatGPT temperature. See OpenAI docs.")

subparsers = parser.add_subparsers(help="sub-command help", dest="command")
for v in commands.values():
    v.add_to_command_parser(subparsers)

args = parser.parse_args()

if not args.command:
    parser.print_help(sys.stderr)
    sys.stderr.write("\nNo sub-command selected\n")
    sys.exit(1)

if args.command not in commands:
    parser.print_help(sys.stderr)
    sys.stderr.write("\nUnknown sub-command\n")
    sys.exit(1)

sys.exit(commands[args.command].run(parser, args))
