import sys

import openai

from perfcopilot.llm import get_base_messages


command = "explainfunction"
help = "Explain what a function does and suggest optimisations"


def add_to_command_parser(subparsers):
    parser = subparsers.add_parser(command, help=help)
    parser.add_argument("--no-optimisations", action='store_true', default=False,
                        help="Do not suggest optimisations")
    parser.add_argument("library", help="The library or program containing the function")
    parser.add_argument("function", help="The name of the function, or the full function signature")

# explainfunction is implemented as a two step conversation. First we ask the LLM for an explanation of the
# library and the function. Then, afterwards, if the user has asked for suggested optimisations, we
# continue the conversation (including the response to the explanation request) and ask for those suggestions.


explain_prompt = """I am a software engineer. I am trying to understand what a function in a particular
software library does.

The library is: {library}
The function is: {function}

Your task is to desribe what the library is and what its use cases are, and to describe what the function
does. The output format should look as follows:

Library description: Provide a concise description of the library
Library use-cases: Provide a concise description of what the library is typically used for.
Function description: Provide a concise, technical, description of what the function does.
"""

optimize_prompt = """Assuming the function {function} from the library {library} is consuming significant CPU resources.
Suggest ways to optimize or improve the system that involve the {function} function from the
{library} library. Types of improvements that would be useful to me are improvements that result in:

- Higher performance so that the system runs faster or uses less CPU
- Better memory efficient so that the system uses less RAM
- Better storage efficient so that the system stores less data on disk.
- Better network I/O efficiency so that less data is sent over the network
- Better disk I/O efficiency so that less data is read and written from disk

Make up to five suggestions. Your suggestions must meet all of the following criteria:
1. Your suggestions should detailed, technical and include concrete examples.
2. Your suggestions should be specific to improving performance of a system in which the {function} function from
the {library} library is consuming significant CPU.
2. If you suggest replacing the function or library with a more efficient replacement you must suggest at least
one concrete replacement.

If you know of fewer than five ways to improve the performance of a system in which the {function} function from the
{library} library is consuming significant CPU, then provide fewer than five suggestions. If you do not know of any
way in which to improve the performance then say "I do not know how to improve the performance of systems where
this function is consuming a significant amount of CPU".

If you have suggestions, the output format should look as follows:

Here are some suggestions as to how you might optimize your system if {function} in {library} is consuming
significant CPU resources:
1. Insert first suggestion
2. Insert second suggestion
etc.
"""


def run(args_parser, args):
    if args.echo_input:
        print(f"{args.lib} {args.func}")

    messages = get_base_messages()
    messages.append({
        "role": "user",
        "content": explain_prompt.format(library=args.library, function=args.function)
    })

    completion = openai.ChatCompletion.create(
        model=args.model,
        temperature=args.temperature,
        stream=True,
        messages=messages,
    )

    explanation = []
    for chunk in completion:
        delta = chunk["choices"][0]["delta"]
        if "content" not in delta:
            continue
        content = delta["content"]
        explanation.append(content)
        sys.stdout.write(content)

    if explanation:
        sys.stdout.write("\n")

    if args.no_optimisations:
        return 0

    messages.extend([
        {
            "role": "assistant",
            "content": "".join(explanation)
        },
        {
            "role": "user",
            "content": optimize_prompt.format(library=args.library, function=args.function)
        }])

    completion = openai.ChatCompletion.create(
        model=args.model,
        temperature=args.temperature,
        stream=True,
        messages=messages,
    )

    wrote_reply = False
    first_iter = True
    for chunk in completion:
        delta = chunk["choices"][0]["delta"]
        if "content" not in delta:
            continue
        wrote_reply = True
        if first_iter:
            sys.stdout.write("\n")
            first_iter = False
        sys.stdout.write(delta["content"])

    if wrote_reply:
        sys.stdout.write("\n")

    return 0
