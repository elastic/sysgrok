import logging
import sys

from multiprocessing import Pool

from perfcopilot import llm


def multiproc_wrapper_summarise_command(llm_config, *args):
    llm.set_config(llm_config)
    return summarise_command(*args)


def summarise_command(command, command_output, summary_max_chars, problem_description):
    """Use the LLM to summarise the output of a command in summary_max_chars or fewer characters.

    command should be the command and its arguments. command_output should be a dict with elements
    exit_code, stderr and stdout.
    """

    prompt_with_problem = """I am a sysadmin. I am logged onto a Linux machine that is experiencing the
following problem: {problem_description}.
I have executed the command '{command}' to debug that problem. I will provide you with the stdout,
stderr and exit code of the command. I need you to summarise the output
of the command, using a maximum of {summary_max_chars} characters. Your summary should only include
information that is useful in understanding and debugging the problem '{problem_description}'.
If there is no information in the exit code, stderr and stdout of the command that is useful in
understanding or debugging the problem say "No useful information".

Problem: {problem_description}
Command: {command}
Exit code: {exit_code}
Stderr: {stderr}
Stdout: {stdout}
Summary (in {summary_max_chars} or fewer):
"""

    prompt_without_problem = """I am a sysadmin. I am logged onto a Linux machine and I have executed the
command '{command}'. I will provide you with the stdout, stderr and exit code of the command. I need you to
summarise the output of the command, using a maximum of {summary_max_chars} characters.

Command: {command}
Exit code: {exit_code}
Stderr: {stderr}
Stdout: {stdout}
Summary (in {summary_max_chars} or fewer):
"""

    if problem_description:
        logging.debug(f"Summarising command (max chars: {summary_max_chars}): {command}. Problem:'{problem_description}")
        prompt = prompt_with_problem.format(
            problem_description=problem_description,
            command=command,
            summary_max_chars=summary_max_chars,
            exit_code=command_output["exit_code"],
            stderr=command_output["stderr"],
            stdout=command_output["stdout"])
    else:
        logging.debug(f"Summarising command (max chars: {summary_max_chars}): {command}")
        prompt = prompt_without_problem.format(
            command=command,
            summary_max_chars=summary_max_chars,
            exit_code=command_output["exit_code"],
            stderr=command_output["stderr"],
            stdout=command_output["stdout"])

    summary = llm.get_llm_response(prompt)
    return command, summary


def calculate_max_chars_per_command_summary(prompt, example_response, num_commands):
    """Calculate the maximum number of characters (not tokens) that each command summary can use.

    The prompt should be a string that represents the entire contents of the prompt, without the
    command summaries. The example response should be a string indicative of what the response will
    look like."""

    model = llm.get_model()

    if model == "gpt-3.5-turbo":
        max_tokens = 4096
    elif model == "gpt-4":
        max_tokens = 8192
    else:
        print(f"Unknown model: {model}")
        sys.exit(-1)

    prompt_tokens = llm.get_token_count(prompt, model)
    response_tokens = llm.get_token_count(example_response, model)
    # Allow for a slightly bigger response than the example response
    response_tokens = int(response_tokens * 1.5)

    # Calculate the number of tokens each command can use by dividing the remaining tokens
    # after we account for the length of the prompt by the number of commands
    tokens_remaining = max_tokens - prompt_tokens
    tokens_per_command = tokens_remaining / num_commands

    # Calculate the char to token ratio using the ratios we got for the prompt and response
    prompt_char_token_ratio = len(prompt) / prompt_tokens
    response_char_token_ratio = len(example_response) / response_tokens
    char_token_ratio = min(prompt_char_token_ratio, response_char_token_ratio)

    chars_per_command = int(tokens_per_command * char_token_ratio)
    return chars_per_command


example_response = """# Summary
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
Check to ensure that the httpd service is actually installed on the host and configured to run."""


analyse_summaries_prompt = """I am a sysadmin. I am logged onto a machine that is experiencing a
problem. I have executed several commands to try to debug the problem. Your task is to analyse
the output of these commands and, based on their output, form a hypothesis as to what the root
cause of my problem is, and suggest actions I may take to fix the problem.

I will provide you with the problem description, and then the exit code, stdout, and stderr
from one or more commands.

You will respond with a summary, a hypothesis as to what the problem
is, and a set of recommended actions to fix the problem.

Here is an example good response

Response:
{response}

Problem: {problem}
Command summaries:
{command_summaries}
Response:"""


def analyse_command_output(commands_output, problem_description, print_each_summary=False):
    max_chars = calculate_max_chars_per_command_summary(
        analyse_summaries_prompt.format(response=example_response,
                                        problem=problem_description,
                                        command_summaries=""),
        example_response,
        len(commands_output))

    logging.debug(f"Asking for a maximum of {max_chars} characters per command summary")
    logging.info(f"Summarising {len(commands_output)} commands")

    multiproc_args = [(llm.get_config(), c, o, max_chars, problem_description) for c, o in commands_output.items()]
    with Pool(min(llm.get_max_concurrent_queries(), len(commands_output))) as p:
        command_summaries = p.starmap(multiproc_wrapper_summarise_command, multiproc_args)

    cs_str_builder = []
    for cs in command_summaries:
        command = cs[0]
        summary = cs[1]
        cs_str_builder.append(f"Summary for '{command}': {summary}")
    cs_str = "\n".join(cs_str_builder)

    if print_each_summary:
        print("# Command Summaries")
        for c, s in command_summaries:
            print(f"## Summary for '{c}'")
            print(s)

    llm.print_streamed_llm_response(analyse_summaries_prompt.format(
        response=example_response, problem=problem_description, command_summaries=cs_str))
