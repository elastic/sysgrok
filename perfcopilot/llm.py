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


def get_chat_completion_args(messages, stream=False):
    kwargs = {
        "temperature": get_temperature(),
        "messages": messages,
        "stream": stream
    }

    if openai.api_type == "azure":
        kwargs["deployment_id"] = get_model()
    elif openai.api_type == "openai":
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
    print("Input 'continue' or 'c' to exit the chat and continue operation")
    print("Input 'quit' or 'q' to exit the chat and exit the copilot")
    user_input = ""

    while True:
        user_input = input("chat> ")
        if user_input == "c" or user_input == "continue":
            print("--- End chat with the LLM ---")
            return conversation
        elif user_input == "q" or user_input == "quit":
            print("--- End chat with the LLM ---")
            sys.exit(0)

        conversation = print_streamed_llm_response(user_input, conversation)
