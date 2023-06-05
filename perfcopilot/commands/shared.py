import sys
import subprocess

import openai
import fabric
import invoke
import tiktoken


def get_base_messages(args):
    messages = [
        {
            "role": "system",
            "content": """You are perf-copilot, a helpful assistant for performance analysis and optimisation
            of software. Answer as concisely as possible. """
        }]

    if args.output_markdown:
        messages.append({
            "role": "user",
            "content": "You must format your output as markdown"
        })
    elif args.output_html:
        messages.append({
            "role": "user",
            "content": "You must format your output as HTML"
        })

    return messages


def query_yes_no(question, default="no"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """

    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")


def execute_commands_remote(host, commands, verbose=False):
    """Execute the provided commands on the specified host. The results are return as a dict where
    the key is the command and the value is the output.
    """

    res = {}
    with fabric.Connection(host) as conn:
        for command in commands:
            tries = 0
            success = False
            while not success and tries < 3:
                tries += 1
                print(f"Executing '{command}' on {host} ...")

                try:
                    e = conn.sudo(command, hide=True, timeout=20, warn=True)
                    if verbose:
                        if e.ok:
                            print(e.stdout)
                        else:
                            print(f"Failed to execute '{command}' on {host}. Non-zero exit code: {e.return_code}.")
                            print(f"stdout: {e.stdout}")
                            print(f"stderr: {e.stderr}")

                    res[command] = {"exit_code": e.return_code, "stderr": e.stderr, "stdout": e.stdout}
                    success = True
                except Exception as e:
                    print(f"Failed to execute '{command}' on {host}. Exception: {e}")

            if not success:
                print(f"Failed to execute '{command}' on {host}")

    return res


def get_token_count(data, model):
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(data))


def get_llm_response(args, prompt):
    messages = get_base_messages(args)
    messages.append({
        "role": "user",
        "content": prompt
    })
    response = openai.ChatCompletion.create(
        model=args.model,
        temperature=args.temperature,
        messages=messages,
    )

    return response["choices"][0]["message"]["content"]


def print_streamed_llm_response(args, prompt):
    messages = get_base_messages(args)
    messages.append({
        "role": "user",
        "content": prompt
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