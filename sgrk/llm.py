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
            "content": """You are perf-copilot, a helpful assistant for performance analysis and optimisation
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
