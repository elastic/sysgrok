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


def get_token_count(data, model):
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(data))


def get_llm_response(prompt):
    messages = get_base_messages()
    messages.append({
        "role": "user",
        "content": prompt
    })
    response = openai.ChatCompletion.create(
        model=get_model(),
        temperature=get_temperature(),
        messages=messages,
    )

    return response["choices"][0]["message"]["content"]


def print_streamed_llm_response(prompt):
    messages = get_base_messages()
    messages.append({
        "role": "user",
        "content": prompt
    })

    completion = openai.ChatCompletion.create(
        model=get_model(),
        temperature=get_temperature(),
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
