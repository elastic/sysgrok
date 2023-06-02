import json
import sys

import openai

from .shared import get_base_messages, query_yes_no, execute_commands_remote

command = "debughost"
help = "Debug an issue by executing CLI tools and interpreting the output"


def add_to_command_parser(subparsers):
    parser = subparsers.add_parser(command, help=help)
    parser.add_argument("-p", "--problem-description", required=True,
                        help="A description of the problem you are investigating. Be as detailed as possible.")
    parser.add_argument("-t", "--target-host", required=True,
                        help="The host to connect to via ssh. Otherwise commands are run locally.")
    parser.add_argument("--yolo", action="store_true", default=False,
                        help="Run LLM suggested commands without confirmation")


def ask_llm_for_commands(args):
    """Get a list of commands to run to solve the  problem described by args.problem.

    Returns a list of strings, where each entry is a command to run and its arguments.
    """

    prompt = """I am a sysadmin. I am logged onto a machine that is experiencing a
problem. I need you to tell me what Linux commands to run to debug the problem.

Your task is to suggest a list of up to ten Linux commands that I should run
that will provide information I can use to debug this problem.
You should format your output as JSON.

Here is an example. I will specify the problem. You will tell me the commands to run to debug it.

Problem: Applications on the host are running slowly
Commands: ["uptime", "top -n1 -b", "ps -ef", "journalctl -b -p warning --no-pager", "vmstat", "mpstat", "free -m", "dmesg | tail -50"]

Problem: {problem}
Commands:"""

    messages = get_base_messages(args)
    messages.append({
        "role": "user",
        "content": prompt.format(problem=args.problem_description)
    })
    response = openai.ChatCompletion.create(
        model=args.model,
        temperature=args.temperature,
        messages=messages,
    )

    return json.loads(response["choices"][0]["message"]["content"])


def analyse_command_output(args, command_output, problem_description):
    prompt = """I am a sysadmin. I am logged onto a machine that is experiencing a
problem. I have executed several commands to try to debug the problem. Your task is to analyse
the output of these commands and, based on their output, form a hypothesis as to what the root
cause of my problem is, and suggest actions I may take to fix the problem.

I will provide you with the problem description, and then the exit code, stdout, and stderr
from one or more commands.

You will respond with a summary, a hypothesis as to what the problem
is, and a set of recommended actions to fix the problem.

Here is an example:

Problem: The web server has stopped responding
Command output:
exit code for 'systemctl status httpd': 0
stdout for 'systemctl status httpd':
stderr for 'systemctl status httpd': Unit httpd.service could not be found.

exit code for 'journalctl -u httpd --no-pager': 0
stdout for 'journalctl -u httpd --no-pager': -- No entries --

stderr for 'journalctl -u httpd --no-pager':
exit code for 'netstat -tuln': 0
stdout for 'netstat -tuln': Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State
tcp        0      0 127.0.0.53:53           0.0.0.0:*               LISTEN
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN
tcp6       0      0 :::22                   :::*                    LISTEN
udp        0      0 127.0.0.53:53           0.0.0.0:*
udp        0      0 172.31.39.206:68        0.0.0.0:*

stderr for 'netstat -tuln':
exit code for 'ps aux | grep httpd': 0
stdout for 'ps aux | grep httpd': ubuntu     24723  0.0  0.0   7760  3368 ?        Ss   16:43   0:00 bash -c sudo -S -p '[sudo] password: ' ps aux | grep httpd
ubuntu     24725  0.0  0.0   7004  2228 ?        S    16:43   0:00 grep httpd

stderr for 'ps aux | grep httpd':
exit code for 'curl -I localhost': 0
stdout for 'curl -I localhost':
stderr for 'curl -I localhost':   % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
curl: (7) Failed to connect to localhost port 80 after 0 ms: Connection refused

exit code for 'tail -n 50 /var/log/httpd/error_log': 0
stdout for 'tail -n 50 /var/log/httpd/error_log':
stderr for 'tail -n 50 /var/log/httpd/error_log': tail: cannot open '/var/log/httpd/error_log' for reading: No such file or directory

Response:

# Summary
Based on the output of the above commands, it looks like the web server is not running, and
is possibly not installed.

# Reasoning
I believe the web server is not running because:
1. The httpd process does not apepar in the stdout of the 'ps aux | grep httpd' command.
2. The 'curl -I localhost' command fails to connect
3. The 'netstat -tuln' command does not list any open ports which would typically correspond with a web server

I believe the web server may not be installed because:
1. The stderr for the 'systemctl status httpd' command indicates there is no httpd service.
2. The stdout for the 'journalctl -u httpd --no-pager' command indicates there are no log entries for the httpd
service.
3. The failure of the 'tail -n 50 /var/log/httpd/error_log' command suggests there is no error log file
for a httpd server.

# Recommendations
Check to ensure that the httpd service is actually installed on the host and configured to run.

Problem: {problem}
""".format(problem=problem_description)

    tmp_command_output = []
    for command, output in command_output.items():
        tmp_command_output.append(f"exit code for '{command}': {output['exit_code']}")
        tmp_command_output.append(f"stdout for '{command}': {output['stdout']}")
        tmp_command_output.append(f"stderr for '{command}': {output['stderr']}")

    tmp_command_output.append("Response:")
    final_prompt = prompt + "\n".join(tmp_command_output)

    messages = get_base_messages(args)
    messages.append({
        "role": "user",
        "content": final_prompt
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


def run(args_parser, args):
    print("Querying the LLM for commands to run ...")
    commands = ask_llm_for_commands(args)
    if not commands:
        sys.stderr.write("LLM did not return any commands to run")
        return -1

    print("LLM suggested running the following commands: ")
    for command in commands:
        print(f"\t{command}")

    if not args.yolo:
        if not query_yes_no("Allow execution of the above commands with sudo?"):
            print("Permission denied. Exiting.")
            return -1

    print(f"{len(commands)} commands in total to execute ...")

    command_output = execute_commands_remote(args.target_host, commands, args.verbose)
    analyse_command_output(args, command_output, args.problem_description)
