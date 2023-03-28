import sys

import openai

command = "findfaster"
help = "Search for faster alternatives to a provided library or program"


def add_to_command_parser(subparsers):
    parser = subparsers.add_parser(command, help=help)
    parser.add_argument("-t", "--software-type", choices=["program", "library", "pylibrary"], default="library",
                        help="Specify the type of software. Not necessary, but can lead to better results.")
    parser.add_argument("target", help="The program or library to find a faster version of")


software_type_prompts = {
    "program": """What are the fastest and most memory-efficient programs that provide
                the same functionality as {target}, and can be used to replace it? Specifically
                I am interested in those those that use SIMD instructions or are optimized for
                scalability and high performance? Provide a summary of {target}, then output
                the suggested programs in a list. For each program, give a summary.""",
    "library": """What are the fastest and most memory-efficient libraries that provide
                the same functionality as {target}, and can be used to replace it. Specifically
                I am interested in those that use SIMD instructions or are optimized for high
                performance and scalability? Provide a summary of {target}, then output
                the suggested libraries in a list. For each library, give a summary.""",
    "pylibrary": """What are the fastest and most memory-efficient Python libraries that
                provide the same functionality as Python's {target} library, and can be used to replace
                it. Specifically I am interested in those that use SIMD instructions or are optimized
                for high performance and scalability? I'm also interested in any lightweight, low-level
                libraries that may provide better performance than pure-Python libraries. Provide a
                summary of {target}, then output the suggested libraries in a list. For each library,
                give a summary."""
}


def run(args_parser, args):
    target = args.target
    temp = args.temperature

    prompt = software_type_prompts[args.software_type]

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=temp,
        stream=True,
        messages=[
            {
                "role": "system",
                "content": """You are perf-gpt, a helpful assistant for performance analysis and optimisation
                of software. Answer as concisely as possible."""
            },
            {
                "role": "user",
                "content": prompt.format(target=target)
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
