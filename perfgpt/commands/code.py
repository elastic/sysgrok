import argparse
import sys

import openai

command = "code"
help = "Analyse profiler-annoted code and suggest optimisations"


def add_to_command_parser(subparsers):
    parser = subparsers.add_parser(command)
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin)


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
                "content": prompt.format(code=code)
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
