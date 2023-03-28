import argparse
import sys

import openai

command = "stacktrace"
help = "Summarise a stack trace and suggest changes to optimise the software"


def add_to_command_parser(subparsers):
    parser = subparsers.add_parser(command)
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin)


prompt = """You are assisting me with understanding a stack trace from a software profiler, such
as pprof or perf record. I will provide you with the stack trace that consumes
the most CPU. A stack trace is a call stack, showing a list of functions that call each other.
It is in reverse order.

First, summarise what the software is doing based on the stacktrace,
including an explanation of any bottlenecks or performance issues that are present.
Then suggest actions I may take to fix bottlenecks or performance issues that are
shown in the stack trace.

This is the stack trace:

{stacktrace}
"""


def run(args_parser, args):
    stacktrace = args.infile.read()
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
                "content": prompt.format(stacktrace=stacktrace)
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
