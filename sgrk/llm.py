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

import sys
import logging

from dataclasses import dataclass

import openai
import tiktoken


@dataclass
class LLMConfig:
    model: str
    temperature: float
    max_concurrent_queries: int
    output_format: str


config = None


def set_config(c):
    global config
    logging.debug(f"Setting LLM config to: {c}")
    config = c


def get_config():
    logging.debug(f"Retrieved LLM config: {config}")
    return config


def set_output_format(format):
    global config
    logging.debug(f"Setting output format to {format}")
    config.output_format = format


def get_output_format():
    logging.debug(f"Retrieved output format: {config.output_format}")
    return config.output_format


def set_model(m):
    global config
    logging.debug(f"Setting model to {m}")
    config.model = m


def get_model():
    logging.debug(f"Retrieved model: {config.model}")
    return config.model


def set_temperature(t):
    global config
    logging.debug(f"Setting temperature to {t}")
    config.temperature = t


def get_temperature():
    logging.debug(f"Retrieved temperature: {config.temperature}")
    return config.temperature


def set_max_concurrent_queries(m):
    global config
    logging.debug(f"Setting max concurrent queries to {m}")
    config.max_concurrent_queries = m


def get_max_concurrent_queries():
    logging.debug(f"Retrieved max concurrent queries {config.max_concurrent_queries}")
    return config.max_concurrent_queries


def get_model_max_tokens():
    model = get_model()
    if model == "gpt-3.5-turbo":
        return 4096
    elif model == "gpt-4":
        return 8192
    elif model == "gpt-4-32k":
        return 32768
    else:
        logging.error(f"Unknown model: {model}")
        sys.exit(-1)


def get_base_messages():
    messages = [
        {
            "role": "system",
            "content": """You are sysgrok, a helpful assistant for performance analysis and optimisation
            of software. Answer as concisely as possible. """
        }]

    output_format = get_output_format()
    if output_format:
        messages.append({
            "role": "user",
            "content": f"You must format your output as {output_format}"
        })

    return messages


def get_token_count(data):
    enc = tiktoken.encoding_for_model(get_model())
    return len(enc.encode(data))


# Global record of the character to token ratio for the current model. Allows us to
# calculate it once and then reuse it as necessary.
_command_char_token_ratio = None


def get_command_char_token_ratio():
    """Returns a character:token ratio for output from Linux command line tools. This is
    calculated by applying tiktoken to sample output from the `top` command.
    """

    global _command_char_token_ratio
    if _command_char_token_ratio:
        logging.debug(f"Returning character token ratio for Linux commands: {_command_char_token_ratio}")
        return _command_char_token_ratio

    top_output = """top - 13:23:34 up  3:37,  1 user,  load average: 0.00, 0.00, 0.00
Tasks: 106 total,   1 running, 105 sleeping,   0 stopped,   0 zombie
%Cpu(s):  0.0 us,  3.1 sy,  0.0 ni, 93.8 id,  3.1 wa,  0.0 hi,  0.0 si,  0.0 st
MiB Mem :   3920.5 total,   2199.4 free,    253.8 used,   1467.3 buff/cache
MiB Swap:      0.0 total,      0.0 free,      0.0 used.   3388.5 avail Mem

    PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
      1 root      20   0  166192  11780   8472 S   0.0   0.3   0:07.98 systemd
      2 root      20   0       0      0      0 S   0.0   0.0   0:00.00 kthreadd
      3 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 rcu_gp
      4 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 rcu_par_gp
      5 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 slub_flushwq
      6 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 netns
      8 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 kworker/0:0H-kblockd
     10 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 mm_percpu_wq
     11 root      20   0       0      0      0 I   0.0   0.0   0:00.00 rcu_tasks_rude_kthread
     12 root      20   0       0      0      0 I   0.0   0.0   0:00.00 rcu_tasks_trace_kthread
     13 root      20   0       0      0      0 S   0.0   0.0   0:00.15 ksoftirqd/0
     14 root      20   0       0      0      0 I   0.0   0.0   0:00.31 rcu_sched
     15 root      rt   0       0      0      0 S   0.0   0.0   0:00.08 migration/0
     16 root     -51   0       0      0      0 S   0.0   0.0   0:00.00 idle_inject/0
     18 root      20   0       0      0      0 S   0.0   0.0   0:00.00 cpuhp/0
     19 root      20   0       0      0      0 S   0.0   0.0   0:00.00 cpuhp/1
     20 root     -51   0       0      0      0 S   0.0   0.0   0:00.00 idle_inject/1
     21 root      rt   0       0      0      0 S   0.0   0.0   0:00.44 migration/1
     22 root      20   0       0      0      0 S   0.0   0.0   0:00.13 ksoftirqd/1
     24 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 kworker/1:0H-events_highpri
     25 root      20   0       0      0      0 S   0.0   0.0   0:00.00 kdevtmpfs
     26 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 inet_frag_wq
     27 root      20   0       0      0      0 S   0.0   0.0   0:00.00 kauditd
     28 root      20   0       0      0      0 S   0.0   0.0   0:00.00 khungtaskd
     29 root      20   0       0      0      0 I   0.0   0.0   0:00.20 kworker/u30:1-events_unbound
     31 root      20   0       0      0      0 S   0.0   0.0   0:00.00 oom_reaper
     32 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 writeback
     33 root      20   0       0      0      0 S   0.0   0.0   0:00.52 kcompactd0
     34 root      25   5       0      0      0 S   0.0   0.0   0:00.00 ksmd
     35 root      39  19       0      0      0 S   0.0   0.0   0:00.00 khugepaged
     36 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 kintegrityd
     37 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 kblockd
     38 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 blkcg_punt_bio
     40 root      20   0       0      0      0 S   0.0   0.0   0:00.00 xen-balloon
     41 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 tpm_dev_wq
     42 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 ata_sff
     43 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 md
     44 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 edac-poller"""

    _command_char_token_ratio = len(top_output) / get_token_count(top_output)
    logging.debug(f"Returning character token ratio for Linux commands: {_command_char_token_ratio}")
    return _command_char_token_ratio


# Global record of the character to token ratio for the current model for English prose. Allows us to
# calculate it once and then reuse it as necessary.
_prose_char_token_ratio = None


def get_prose_char_token_ratio():
    """Returns a character:token ratio for English prose. This is calculated by applying tiktoken to
    sample text (which is actually GPT-4 generated text in a command summarisation use case).
    """

    global _prose_char_token_ratio
    if _prose_char_token_ratio:
        logging.debug(f"Returning prose token ratio for English prose: {_prose_char_token_ratio}")
        return _prose_char_token_ratio

    sample_prose = """The system has been up for 5 hours and 15 minutes with 0 users logged in. The load
    average is low (0.09, 0.04, 0.01), indicating that the system is not under heavy load. The CPU usage
    is mostly idle (99.36%), with minimal user (0.17%), system (0.12%), and I/O wait (0.29%) usage. There
    are no significant performance or stability issues detected. Memory usage is also in a healthy state,
    with 1983 MB free out of 3920 MB total, and 3399 MB available. Swap usage is at 0 MB, indicating that
    the system is not under memory pressure. The top processes running on the system include systemd,
    snapd, amazon-ssm-agent, and multipathd, among others. No processes are consuming a significant amount
    of CPU or memory resources. In conclusion, the system is currently stable and not experiencing any
    performance issues."""

    _prose_char_token_ratio = len(sample_prose) / get_token_count(sample_prose)
    logging.debug(f"Returning prose token ratio for Linux commands: {_prose_char_token_ratio}")
    return _prose_char_token_ratio


def get_chat_completion_args(messages, stream=False):
    kwargs = {
        "temperature": get_temperature(),
        "messages": messages,
        "stream": stream
    }

    if openai.api_type == "azure":
        kwargs["deployment_id"] = get_model()
    elif openai.api_type == "open_ai":
        kwargs["model"] = get_model()
    else:
        logging.error(f"Unknown API type: {openai.api_type}")
        sys.exit(1)

    return kwargs


def get_llm_response(prompt):
    messages = get_base_messages()
    messages.append({
        "role": "user",
        "content": prompt
    })
    response = openai.ChatCompletion.create(
        **get_chat_completion_args(messages)
    )

    return response["choices"][0]["message"]["content"]


def print_streamed_llm_response(prompt, conversation=None):
    response = []

    if not conversation:
        conversation = get_base_messages()

    conversation.append({
        "role": "user",
        "content": prompt
    })

    completion = openai.ChatCompletion.create(
        **get_chat_completion_args(conversation, stream=True)
    )

    wrote_reply = False
    for chunk in completion:
        delta = chunk["choices"][0]["delta"]
        if "content" not in delta:
            continue
        content = delta["content"]
        sys.stdout.write(content)
        response.append(content)
        wrote_reply = True

    if wrote_reply:
        sys.stdout.write("\n")

    conversation.append({"role": "assistant", "content": "".join(response)})

    return conversation


def chat(conversation):
    print("--- Start chat with the LLM ---")
    print("Input 'c' to exit the chat and continue operation")
    print("Input 'q' to exit the chat and exit the copilot")
    user_input = ""

    while True:
        user_input = input("chat> ")
        if user_input == "c":
            print("--- End chat with the LLM ---")
            return conversation
        elif user_input == "q":
            print("--- End chat with the LLM ---")
            sys.exit(0)

        conversation = print_streamed_llm_response(user_input, conversation)
