import argparse
import sys

import openai

from .shared import get_base_messages

command = "topn"
help = "Summarise Top-N output from a profiler and suggest improvements"


def add_to_command_parser(subparsers):
    parser = subparsers.add_parser(command, help=help)
    parser.add_argument(
        'infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin,
        help="The file containing the Top N. Defaults to stdin.")


prompt = """You are assisting me with understanding the top most expensive functions found by a
software profiler, such as pprof or perf record. I will provide you a list of the most expensive
functions, the amount of CPU time spent in each, and the software libraries or programs that each
function is in. In the following, when I refer to a "libary" I mean library or program.

You have four tasks.

Your first task is to provide a concise, technical summary of what the system is doing based
on the list of libraries and functions.

Your second task is to give a concise, short, technical summary of each library, and
their associated functions. The explanations of the functions associated with each library
should be grouped together under that library. If you do not know what the library or program is,
you must say "I am unsure what this software is". If you do not know what the function does you
must say "I am unsure what this function is". You must give an explanation for every library and
every function. You cannot exclude any functions.

Your third task is to explain any bottlenecks or performance issues that may be present in the system,
based on the list of libraries and functions and the amount of CPU time spent in each.

You fourth task is to then suggest actions the user may take to fix bottlenecks or performance issues that are
shown in the stack trace. The fixes may include replacing particular software libraries with a
library that provides the same functionality but is optimised to be faster or more memory efficient,
or any other optimisations that you can suggest. Be specific, and provide examples if they are relevant.

The template for your output is as follows. You must follow this template.

[BEGIN TEMPLATE]
<First task. Insert concise technical summary of what the system is doing, based on the list of libraries and functions>

<Second task. Repeat the following for each library present. You must include every library in your output.>
<First library name>: <insert concise technical description of first library and what it is used for>. The functions executed in <first library name> are as follows:
Repeat the following for each function associated with the current library. You must include every function in your output.
<insert 4 whitespace characters>* <first function in libary>: <insert concise technical description of the function and what it is used for>

<Third task. Insert explanation for any potential bottlenecks or performance issues that the system
may be facing, based on the list of libraries and functions and the time spent in each>

<Fourth task. Insert a numbered list of up to 5 actions the user may take to improve the performance of the system. Be
precise, use technical language, and give concrete examples. If you suggest using
alternative software, libraries, hardware or architectures then you must give a concrete example of a specific alternative to
support your suggestion. You must never suggest using an alternative algorithm, piece of software, hardware, or architecture
without giving a specific, concrete example of an alternative algorithm, software, hardware or architecture that will perform better. Give concrete examples for all changes that you suggest, or explain why it is
not possible to give an example.>
[END TEMPLATE]

The input format will include one library and function name per line, along with the percentage of CPU that it
is responsible for. The filename in which the function is found may also occur. The order of the items in each line may vary.
If the first line of the input starts with a # then that line is a header, which describes the format of the following lines.

This is the list of most expensive functions and the libraries they are in.

{topn}
"""


def run(args_parser, args):
    topn = args.infile.read()
    if args.echo_input:
        print(topn)

    messages = get_base_messages(args)
    messages.append({
        "role": "user",
        "content": prompt.format(topn=topn)
    })

    completion = openai.ChatCompletion.create(
        model=args.model,
        temperature=args.temperature,
        stream=True,
        messages=messages
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
