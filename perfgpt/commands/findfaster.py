import openai

command = "findfaster"
help = "Try to find a faster version of the provided library or program"


def add_to_command_parser(subparsers):
    parser = subparsers.add_parser(command)
    parser.add_argument("-t", "--software-type", choices=["program", "library", "pylibrary"], default="library",
                        help="Specify the type of software. Not necessary, but can lead to better results.")
    parser.add_argument("target", help="The program or library to find a faster version of")


software_type_prompts = {
    "program": """What are the fastest and most memory-efficient programs that provide
                the same functionality as {target}, specifically those that use SIMD instructions
                or are optimized for high performance? Output the suggested programs in a list.
                For each program, give a summary.""",
    "library": """What are the fastest and most memory-efficient libraries that provide
                the same functionality as {target}, specifically those that use SIMD instructions
                or are optimized for high performance? Output the suggested libraries in a list.
                For each library, give a summary.""",
    "pylibrary": """What are the fastest and most memory-efficient Python libraries that
                provide the same functionality as Python's {target} library, specifically those that use
                SIMD instructions or are optimized for high performance? I'm also interested in any
                lightweight, low-level libraries that may provide better performance than pure-Python
                libraries. Output the suggested libraries in a list. For each library, give a summary."""
}


def run(args_parser, args):
    target = args.target
    temp = args.temperature

    prompt = software_type_prompts[args.software_type]

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=temp,
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

    result = completion['choices'][0]['message']['content']
    print(result)
    return 0
