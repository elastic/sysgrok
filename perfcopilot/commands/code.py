import argparse
import sys

from perfcopilot.llm import print_streamed_llm_response, chat

command = "code"
help = "Summarise profiler-annoted code and suggest optimisations"


def add_to_command_parser(subparsers):
    parser = subparsers.add_parser(command, help=help)
    parser.add_argument(
        'infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin,
        help="The file containing the annotated code. Defaults to stdin.")


prompt = """You are assisting me with optimising code to make it faster or more
memory efficient. I will provide you with source code. Each line of code
is annoted by a profiler to indicate how frequently that line of code has executed.

First, summarise the function and describe what parts of it are hot, based on the profiling annotations.

Then suggest actions I may take to fix bottlenecks or performance issues that are shown in the code.

The code is as follows:

{code}
"""


def run(args_parser, args):
    code = args.infile.read()
    if args.echo_input:
        print(code)

    conversation = print_streamed_llm_response(args, prompt.format(code=code))
    if args.chat:
        chat(conversation)

    return 0
