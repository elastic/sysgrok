import argparse
import sys

import openai

command = "stacktrace"
help = "Summarise a stack trace and suggest changes to optimise the software"


def add_to_command_parser(subparsers):
    parser = subparsers.add_parser(command)
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin)


prompt = """You are assisting me with understanding the output of a software profiler, such
as pprof, perf, or another profiler. I will provide you with the stack trace that consumes
the most CPU. My goal is to optimise the software so that it runs faster and is memory efficient.
First summarise the stack trace and explain to me what the software is doing. Then suggest actions I
may take to optimise the software.

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
                "content": """You are perf-gpt, a helpful assistant for performance analysis and software
                optimisation."""
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
