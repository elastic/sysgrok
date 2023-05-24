import os
import sys

import openai

command = "analyzecmd"
help = "Analyze the output of CLI tools to find the root cause of an issue and suggest remediations"


def add_to_command_parser(subparsers):
    parser = subparsers.add_parser(command, help=help)
    parser.add_argument("-p", "--problem-description", help="A description of the problem you are investigating")
    parser.add_argument("-i", "--inputs-directory",
                        help="""The directory containing the outputs of each command. Each file in the directory must
    contain the output of a single command. The name of the file must have the format "cmd.output" where "cmd" is the
    name of the command that produced the output.""")


prompt = """I am a software engineer. I am trying to solve the problem: {problem}. The host experiencing the
problem is running the Linux operating system. I have executed the {cmd} command. Your task is to analyze the
output of the command and then do three things.

1. Output a summary of the command output, focusing on anything that may relate to the problem I am trying to solve.
2. Based on the command output, explain the root cause of my problem.  If there is
insufficient information in the command output to explain the root cause then say "Cannot determine problem root cause
based on command output" and go to step 3. If there are multiple potential root causes indicated
by the command output, then list them all. For each potential root cause, concisely explain what in the command output
indicates that this root cause is likely, then explain how I could resolve the problem if this is the root cause.

The output of the {cmd} is as follows:

{cmd_output}
"""


def analyze_cmd(cmd, cmd_output, args):
    print(f"Analyzing output from {cmd} ...")

    completion = openai.ChatCompletion.create(
        model=args.model,
        temperature=args.temperature,
        stream=True,
        messages=[
            {
                "role": "system",
                "content": """You are perf-copilot, a helpful assistant for performance analysis and optimisation
                of software. Answer as concisely as possible."""
            },
            {
                "role": "user",
                "content": prompt.format(problem=args.problem_description, cmd=cmd, cmd_output=cmd_output)
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


def run(args_parser, args):
    d = args.inputs_directory
    first_iter = True
    for filename in os.listdir(d):
        if not first_iter:
            sys.stdout.write("\n")
            first_iter = False

        cmd = filename.split(".")[0]
        with open(os.path.join(d, filename)) as f:
            cmd_output = f.read()

        analyze_cmd(cmd, cmd_output, args)

    return 0
