# Licensed to Elasticsearch B.V. under one or more contributor
# license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright
# ownership. Elasticsearch B.V. licenses this file to you under
# the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import logging

from multiprocessing import Pool

from sgrk import llm


def multiproc_wrapper_summarise_command(llm_config, *args):
    """Wrapper around summarise_command for use in multiprocessing scenarios. This is necessary
    as the LLM module makes use of a bunch of environment variables in its configuration, and
    these must be set anew in each multiprocessing process.
    """

    llm.set_config(llm_config)
    return summarise_command(*args)


_summarise_summaries_prompt_with_problem = """I am a systems adminstrator. I have logged onto a Linux machine that
is experiencing the following problem: {problem_description}. I have executed the command
"{command}" to debug that problem.

The full command output (stdout) is too long to give to you, so I have split the output into
chunks and summarised those chunks. I will give you an ordered list of these summaries.

Your task is to create a summary of the entire command output from the chunk summaries. Your
summary should focus on information that is useful in understanding and debugging the problem
'{problem_description}'.

Problem: {problem_description}
Command: {command}
Exit code: {exit_code}
Stderr: {stderr}
Stdout chunk summaries: {chunk_summaries}
Final summary, created from the chunk summaries (must be {summary_max_chars} or fewer characters):"""

_summarise_summaries_prompt_without_problem = """I am a systems adminstrator. I have logged onto a Linux machine
and I have executed the command "{command}".

The full command output (stdout) is too long to give to you, so I have split the output into
chunks and summarised those chunks. I will give you an ordered list of these summaries.

Your task is to create a summary of the entire command output from the chunk summaries. Your
summary should give the user an overview of all notable information found in the output of the
command. Your summary must include any information that points to performance, security, reliability, or
stability issues with the machine or any services running on it.

Command: {command}
Exit code: {exit_code}
Stderr: {stderr}
Stdout chunk summaries: {chunk_summaries}
Final summary, created from the chunk summaries (must be {summary_max_chars} or fewer characters):"""


def _summarise_chunk_summaries(command, command_output, chunk_summaries, summary_max_chars, problem_description):
    """When we encounter command output that is too long to include in a prompt for summarisation
    we split it into chunks and summarise each of those chunks. This function is then called to
    produce the final output summary for that command from these individual output chunk summaries.
    """

    if problem_description:
        logging.debug(
            f"Creating command summary from {len(chunk_summaries)} chunk summaries (max chars: {summary_max_chars}):"
            f" {command}. Problem:'{problem_description}")
        prompt = _summarise_summaries_prompt_with_problem.format(
            problem_description=problem_description,
            command=command,
            summary_max_chars=summary_max_chars,
            exit_code=command_output.exit_code,
            stderr=command_output.stderr,
            chunk_summaries=chunk_summaries)
    else:
        logging.debug(f"Creating command summary from {len(chunk_summaries)} chunk summaries "
                      f" (max chars: {summary_max_chars}): {command}")
        prompt = _summarise_summaries_prompt_without_problem.format(
            command=command,
            summary_max_chars=summary_max_chars,
            exit_code=command_output.exit_code,
            stderr=command_output.stderr,
            chunk_summaries=chunk_summaries)

    summary = llm.get_llm_response(prompt)
    return command, summary


def _split_command_output_into_chunks(command_output, chunk_num_chars):
    lines = command_output.splitlines()
    logging.debug(f"Split command output of len {len(command_output)} into {len(lines)} lines")

    chunks = []
    curr_chunk = []
    curr_chunk_numchars = 0
    for line in lines:
        if curr_chunk_numchars + len(line) <= chunk_num_chars:
            curr_chunk.append(line)
            curr_chunk_numchars += len(line)
            continue

        chunks.append("\n".join(curr_chunk))
        curr_chunk = [line]
        curr_chunk_numchars = len(line)

    chunks.append("\n".join(curr_chunk))
    logging.debug(f"Split command output of len {len(command_output)} into {len(chunks)} chunks"
                  f" with {chunk_num_chars} characters each")
    return chunks


_summarise_chunk_prompt_with_problem = """I am a systems adminstrator. I have logged onto a Linux machine that
is experiencing the following problem: {problem_description}. I have executed the command
"{command}" to debug that problem. Your task is to summarise the output of that command. Your
summary should focus on information that is useful in understanding and debugging the problem
'{problem_description}'. Your summary should also include any information that points to performance,
security, reliability, or stability issues with the machine or any services running on it.

The stdout output of the command is too long for you to process all at once so I will split it
into chunks and provide you with those chunks to summarise one at a time. Your summary of each
chunk must use a maximum of {chunk_summary_max_chars} text characters. Once you have summarised
each chunk I will then ask you to produce a final summary from each of the chunk summaries.
Therefore you should also include in each chunk summary any information that you think would be
useful to you when producing a final summary from the individual chunk summaries. If the output
format of the command "{command}" means that information found in a particular chunk is
necessary to understand a later chunk then you should include that information in your summary.

Problem: {problem_description}
Command: {command}
Stdout (chunk {chunk_number} of {number_of_chunks}): {chunk_data}
Chunk Summary (in {chunk_summary_max_chars} or fewer characters):"""

_summarise_chunk_prompt_without_problem = """I am a sysems adminstrator. I have logged onto a Linux machine and
executed the command "{command}". Your task is to summarise the output of that command. Your summary
should give an overview of any notable information found in the output of the command. In particular,
your summary must include any information that points to performance, security, reliability or stability
issues with the machine or any services running on it.

The stdout output of the command is too long for you to process all at once so I will split it
into chunks and provide you with those chunks to summarise one at a time. Your summary of each
chunk must use a maximum of {chunk_summary_max_chars} text characters. Once you have summarised
each chunk I will then ask you to produce a final summary from each of the chunk summaries.
Therefore you should also include in each chunk summary any information that you think would be
useful to you when producing a final summary from the individual chunk summaries. If the output
format of the command "{command}" means that information found in a particular chunk is
necessary to understand a later chunk then you should include that information in your summary.

Command: {command}
Stdout (chunk {chunk_number} of {number_of_chunks}): {chunk_data}
Chunk Summary (in {chunk_summary_max_chars} or fewer characters):"""


def _summarise_command_chunked(command, command_output, summary_max_chars, problem_description=None):
    """Use the LLM to summarise the output of a command in summary_max_chars or fewer characters.
    This function should be used when the command_output results in a summarisation prompt that
    is too large for the model's context window limit.

    Experimentation is still needed to validate whether or not the approach in this function
    loses information in comparison to the normal summarise_command approach which can fit the
    entire command output in a single call to the LLM.
    """

    # Step 1: Split the input data into chunks
    if problem_description:
        # To split the command output we need to know how long each chunk can be. This depends on the
        # prompt that it will be embedded in, so we need to create that prompt, minus the chunk summary.
        summarise_chunk_dummy_prompt = _summarise_chunk_prompt_with_problem.format(
                problem_description=problem_description,
                command=command,
                chunk_summary_max_chars=100000,
                chunk_data="",
                chunk_number=1000,
                number_of_chunks=1000)
        # We also need to know how long each chunk summary can be. This depends on the prompt that will
        # eventually be used to compute the final summary from the chunk summaries.
        summarise_summaries_dummy_prompt = _summarise_summaries_prompt_with_problem.format(
            problem_description=problem_description,
            command=command,
            summary_max_chars=summary_max_chars,
            exit_code=command_output.exit_code,
            stderr=command_output.stderr,
            chunk_summaries="")
    else:
        summarise_chunk_dummy_prompt = _summarise_chunk_prompt_without_problem.format(
                command=command,
                chunk_summary_max_chars=100000,
                chunk_data="",
                chunk_number=1000,
                number_of_chunks=1000)
        summarise_summaries_dummy_prompt = _summarise_summaries_prompt_without_problem.format(
            command=command,
            summary_max_chars=summary_max_chars,
            exit_code=command_output.exit_code,
            stderr=command_output.stderr,
            chunk_summaries="")

    # Calculate the number of characters that should be in each chunk and then split
    summarise_chunk_dummy_prompt_tokens = llm.get_token_count(summarise_chunk_dummy_prompt)
    chunk_tokens = llm.get_model_max_tokens() - summarise_chunk_dummy_prompt_tokens
    chunk_num_chars = int(chunk_tokens * llm.get_command_char_token_ratio() + 0.5)
    chunks = _split_command_output_into_chunks(command_output.stdout, chunk_num_chars)

    # Calculate the maximum number of characters each chunk summary can use
    summarise_summaries_dummy_prompt_tokens = llm.get_token_count(summarise_summaries_dummy_prompt)
    summary_tokens_available = llm.get_model_max_tokens() - summarise_summaries_dummy_prompt_tokens
    chunk_summary_max_tokens = int(summary_tokens_available / len(chunks) + 0.5)
    chunk_summary_max_chars = int(chunk_summary_max_tokens * llm.get_prose_char_token_ratio())

    # Step 2: Summarise each chunk
    chunk_idx = 0
    chunk_summaries = []
    num_chunks = len(chunks)
    while chunk_idx < num_chunks:
        if problem_description:
            logging.debug(
                f"Summarising command chunk {chunk_idx+1}/{num_chunks} (max chars: {chunk_summary_max_chars}): "
                f"{command}. Problem: '{problem_description}'")
            prompt = _summarise_chunk_prompt_with_problem.format(
                problem_description=problem_description,
                command=command,
                chunk_summary_max_chars=chunk_summary_max_chars,
                chunk_data=chunks[chunk_idx],
                chunk_number=chunk_idx,
                number_of_chunks=num_chunks)
        else:
            logging.debug(f"Summarising command chunk {chunk_idx+1}/{num_chunks} (max chars: "
                          f"{chunk_summary_max_chars}): {command}")
            prompt = _summarise_chunk_prompt_without_problem.format(
                command=command,
                chunk_summary_max_chars=chunk_summary_max_chars,
                chunk_data=chunks[chunk_idx],
                chunk_number=chunk_idx,
                number_of_chunks=num_chunks)

        chunk_summaries.append(llm.get_llm_response(prompt))
        chunk_idx += 1

    # Step 3: Create a final summary from the summaries of each chunk
    return _summarise_chunk_summaries(command, command_output, chunk_summaries, summary_max_chars, problem_description)


def summarise_command(command, command_output, summary_max_chars=None, problem_description=None):
    """Use the LLM to summarise the output of a command.

    Args:
        command (str): The command and its arguments
        command_output (cmdexec.CommandResult): The output of running the command
        summary_max_chars (int): Tell the LLM to limit the summary to this number of characters
        problem_description (str): Description of the problem the user is investigating using
            the command. If provided then the LLM will be asked to summarise the command output
            with respect to this problem description.

    Returns:
        (str, str): A tuple of the command and the summary
    """

    prompt_with_problem = """I am a sysadmin. I am logged onto a Linux machine that is experiencing the
following problem: {problem_description}.
I have executed the command '{command}' to debug that problem. I will provide you with the stdout,
stderr and exit code of the command. I need you to summarise the output
of the command, using a maximum of {summary_max_chars} characters. Your summary must include
information that is useful in understanding and debugging the problem '{problem_description}'. Your summary
should also include any information that points to performance, security, reliability, or
stability issues with the machine or any services running on it.
If there is no information in the exit code, stderr and stdout of the command that is useful in
understanding or debugging the problem say "No useful information".

Problem: {problem_description}
Command: {command}
Exit code: {exit_code}
Stderr: {stderr}
Stdout: {stdout}
Summary (in {summary_max_chars} or fewer characters):
"""

    prompt_without_problem = """I am a sysadmin. I am logged onto a Linux machine and I have executed the
command '{command}'. I will provide you with the stdout, stderr and exit code of the command. I need you to
summarise the output of the command, using a maximum of {summary_max_chars} characters. Your summary should
give the user an overview of any notable information found in the output of the command. In particular,
your summary must include any information that points to performance, security, reliability orstability
issues with the machine or any services running on it.

Command: {command}
Exit code: {exit_code}
Stderr: {stderr}
Stdout: {stdout}
Summary (in {summary_max_chars} or fewer characters):
"""

    summary_tokens = None
    if not summary_max_chars:
        # If no number is given for the summary size then lets say 10% of the available context length
        summary_tokens = int(llm.get_model_max_tokens() * .10)
        summary_max_chars = int(summary_tokens * llm.get_prose_char_token_ratio())
        logging.debug(f"summary_max_characters not specified. Calculated it to be "
                      f"{summary_tokens} tokens, {summary_max_chars} characters.")

    if problem_description:
        logging.debug(
            f"Summarising command (max chars: {summary_max_chars}): {command}. Problem:'{problem_description}")
        prompt = prompt_with_problem.format(
            problem_description=problem_description,
            command=command,
            summary_max_chars=summary_max_chars,
            exit_code=command_output.exit_code,
            stderr=command_output.stderr,
            stdout=command_output.stdout)
    else:
        logging.debug(f"Summarising command (max chars: {summary_max_chars}): {command}")
        prompt = prompt_without_problem.format(
            command=command,
            summary_max_chars=summary_max_chars,
            exit_code=command_output.exit_code,
            stderr=command_output.stderr,
            stdout=command_output.stdout)

    # Check if there is room left for a response
    prompt_tokens = llm.get_token_count(prompt)
    model_max_tokens = llm.get_model_max_tokens()
    # If summary_max_chars was not provided as an argument then we already know how many tokens
    # we want in the summary, as we calculated it above. If summary_max_chars was provided though,
    # then we need to calculate the token limit from it.
    if not summary_tokens:
        summary_tokens = int(summary_max_chars/llm.get_command_char_token_ratio() + 0.5)
    logging.debug(f"Prompt tokens: {prompt_tokens}, model max tokens: {model_max_tokens}"
                  f" summary tokens: {summary_tokens}")
    if prompt_tokens > model_max_tokens - summary_tokens:
        logging.debug("Insufficient room left in context window for summary.")
        return _summarise_command_chunked(command, command_output, summary_max_chars, problem_description)

    summary = llm.get_llm_response(prompt)
    return command, summary


def calculate_max_chars_per_command_summary(prompt, example_response, num_commands):
    """Calculate the maximum number of characters (not tokens) that each command summary can use.

    The prompt should be a string that represents the entire contents of the prompt, without the
    command summaries. The example response should be a string indicative of what the response will
    look like."""

    max_tokens = llm.get_model_max_tokens()

    prompt_tokens = llm.get_token_count(prompt)
    response_tokens = llm.get_token_count(example_response)
    # Allow for a bigger response than the example response
    response_tokens = int(response_tokens * 4)

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


analyse_summaries_prompt_with_problem = """I am a sysadmin. I am logged onto a machine that is experiencing a
problem. I have executed several commands to try to debug the problem. Your task is to analyse
the output of these commands and, based on their output, form a hypothesis as to what the root
cause of my problem is, and suggest actions I may take to fix the problem.

I will provide you with the problem description, and then a summary of the output of one or
more commands.

You will respond with an overall summary, a hypothesis as to what the problem
is, and a set of recommended actions to fix the problem.

Here is an example good response

Response:
{response}

Problem: {problem}
Command summaries:
{command_summaries}
Response:"""

analyse_summaries_prompt_without_problem = """I am a sysadmin. I am logged onto a Linux machine.
I have executed several commands to try to debug the problem. Your task is to analyse
the output of these commands and, based on their output, alert me to any issues on the
machine that may impact the performance or stability of any services running on it.

I will provide you with the exit code, stdout, and stderr from one or more commands. You
will respond with a summary
Here is an example good response

Response:
{response}

Command summaries:
{command_summaries}
Response:"""


def _get_command_summaries(commands_output, problem_description=None):
    """Use the LLM to summarise the provided commands. The summarisation queries
    to the LLM are done in parallel.
    """

    if problem_description:
        max_chars = calculate_max_chars_per_command_summary(
            analyse_summaries_prompt_with_problem.format(response=example_response,
                                                         problem=problem_description,
                                                         command_summaries=""),
            example_response,
            len(commands_output))
    else:
        max_chars = calculate_max_chars_per_command_summary(
            analyse_summaries_prompt_without_problem.format(response=example_response,
                                                            command_summaries=""),
            example_response,
            len(commands_output))

    logging.debug(f"Asking for a maximum of {max_chars} characters per command summary")
    logging.info(f"Summarising {len(commands_output)} commands")

    multiproc_args = [(llm.get_config(), c, o, max_chars, problem_description) for c, o in commands_output.items()]
    with Pool(min(llm.get_max_concurrent_queries(), len(commands_output))) as p:
        command_summaries = p.starmap(multiproc_wrapper_summarise_command, multiproc_args)

    return command_summaries


def analyse_command_output(commands_output: dict, problem_description: str = None, print_each_summary: bool = False):
    """Use the LLM to analyse and summarise the output of one or more commands. The result is
    streamed to stdout.

    Args:
        commands_output: A dict mapping from commands to CommandResult objects for that command.
        problem_description: The problem description to analyse the commands with respect to.
        print_each_summary: If true, then print each command summary.
    """

    # Summarise the output of each of the commands
    command_summaries = _get_command_summaries(commands_output, problem_description)

    # Build a string of the command summaries for inclusion in the prompt
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

    # Ask the LLM to analyse the combination of the summaries and produce recommendations
    if problem_description:
        llm.print_streamed_llm_response(analyse_summaries_prompt_with_problem.format(
            response=example_response, problem=problem_description, command_summaries=cs_str))
    else:
        llm.print_streamed_llm_response(analyse_summaries_prompt_without_problem.format(
            response=example_response, command_summaries=cs_str))
