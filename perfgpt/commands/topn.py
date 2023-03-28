import argparse
import sys

import openai

command = "topn"
help = "Summarise Top-N output from a profiler and suggest improvements"


def add_to_command_parser(subparsers):
    parser = subparsers.add_parser(command, help=help)
    parser.add_argument(
        'infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin,
        help="The file containing the Top N. Defaults to stdin.")


prompt = """You are assisting me with understanding the top most expensive functions found by a
software profiler, such as pprof or perf record. I will provide you a list of the most expensive
functions and the software libraries that they are in.

First, summarise what the software is doing based on the list of functions,
including an explanation of any bottlenecks or performance issues that are present.
Then suggest actions I may take to fix bottlenecks or performance issues that are
shown in the stack trace. The fixes may include replacing particular software libraries with a
library that provides the same functionality but is optimised to be faster or more memory efficient,
or any other optimisations that you can suggest.

This is the list of most expensive functions and the libraries they are in:

{topn}
"""


def run(args_parser, args):
    topn = args.infile.read()
    temp = args.temperature

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=temp,
        stream=True,
        messages=[
            {
                "role": "system",
                "content": """You are perf-gpt, a helpful assistant."""
            },
            {
                "role": "user",
                "content": prompt.format(topn=topn)
            }
        ]
    )

    wrote_reply = False
    for chunk in completion:
        delta = chunk["choices"][0]["delta"]
        if "content" not in delta:
            continue
        sys.stdout.write((delta["content"]))
        wrote_reply = True

    if wrote_reply:
        sys.stdout.write("\n")
    return 0
