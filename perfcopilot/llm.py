import sys

import openai
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
