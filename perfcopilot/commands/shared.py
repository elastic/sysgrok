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
