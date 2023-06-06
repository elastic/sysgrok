from perfcopilot.llm import print_streamed_llm_response

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
                the suggested programs in a list. For each program, give a summary.
                Suggest at most three programs. Only suggest programs that are confirmed
                to be faster by several sources. For each suggestion, explain what the pros and cons
                are in comparison to the other suggestions. At the end, recommend one of your
                suggestions over the others and explain why. """,
    "library": """What are the fastest and most memory-efficient libraries that provide
                the same functionality as {target}, and can be used to replace it. Specifically
                I am interested in those that use SIMD instructions or are optimized for high
                performance and scalability? Provide a summary of {target}, then output
                the suggested libraries in a list. For each library, give a summary.
                Suggest at most three libraries. Only suggest libraries that are confirmed
                to be faster by several sources. For each suggestion, explain what the pros and cons
                are in comparison to the other suggestions. At the end, recommend one of your
                suggestions over the others and explain why you are recommending it over the other
                suggestions.""",
    "pylibrary": """What are the fastest and most memory-efficient Python libraries that
                provide the same functionality as Python's {target} library, and can be used to replace
                it. Specifically I am interested in those that use SIMD instructions or are optimized
                for high performance and scalability? I'm also interested in any lightweight, low-level
                libraries that may provide better performance than pure-Python libraries. Provide a
                summary of {target}, then output the suggested libraries in a list. For each library,
                give a summary. Suggest at most three libraries. Only suggest libraries are confirmed
                to be faster by several sources. For each suggestion, explain what the pros and cons
                are in comparison to the other suggestions. At the end, recommend one of your
                suggestions over the others and explain why."""
}


def run(args_parser, args):
    target = args.target
    if args.echo_input:
        print(target)

    print_streamed_llm_response(software_type_prompts[args.software_type].format(target=args.target))
    return 0
