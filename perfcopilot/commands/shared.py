import sys
import subprocess

import fabric
import invoke


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
            if verbose:
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

                res[command] = {"exit_code": 0, "stderr": e.stderr, "stdout": e.stdout}
            except Exception as e:
                print(f"Failed to execute '{command}' on {host}. Exception: {e}")
                sys.exit(-1)

    return res
