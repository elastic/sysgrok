#!/usr/bin/env python

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

# sysgrok is an experimental tool for performance analysis and optimisation
# using LLMs. Its purpose is to take data from existing profilers and provide
# the user with helpful summaries, advice and direction.
#
# Author: Sean Heelan
# Email: sean.heelan@elastic.co


from sgrk.llm import LLMConfig, set_config
from sgrk.commands import (
    analyzecmd,
    code,
    debughost,
    explainfunction,
    explainprocess,
    findfaster,
    stacktrace,
    topn
)

import argparse
import logging
import os
import sys

import openai

from dotenv import load_dotenv
load_dotenv()

api_type = api_key = api_base = api_version = None

try:
    api_type = os.environ["GAI_API_TYPE"]
    api_key = os.environ["GAI_API_KEY"]
    api_base = os.environ["GAI_API_BASE"]
    api_version = os.environ["GAI_API_VERSION"]
except KeyError:
    pass

if not api_key or not api_type:
    sys.stderr.write("You must set the GAI API type and key\n")
    sys.exit(1)

openai.api_key = api_key
openai.api_type = api_type

if api_type == "azure":
    if not (api_base and api_version):
        sys.stderr.write("Azure requires the API base and version to be set")
        sys.exit(1)
    openai.api_base = api_base
    openai.api_version = api_version
elif api_type == "open_ai":
    if api_base or api_version:
        sys.stderr.write("You must not to set the GAI_API_BASE or GAI_API_VERSION for the open_ai GAI_API_TYPE")
        sys.exit(1)
else:
    sys.stderr.write(f"Invalid GAI_API_TYPE value: '{api_type}'. Must be azure or open_ai.")
    sys.exit(1)


ascii_name = """
                               _
 ___ _   _ ___  __ _ _ __ ___ | | __
/ __| | | / __|/ _` | '__/ _ \| |/ /
\__ \ |_| \__ \ (_| | | | (_) |   <
|___/\__, |___/\__, |_|  \___/|_|\_\

     |___/     |___/

System analysis and optimisation with LLMs
"""

if __name__ == "__main__":
    commands = {
        analyzecmd.command: analyzecmd,
        code.command: code,
        explainfunction.command: explainfunction,
        explainprocess.command: explainprocess,
        debughost.command: debughost,
        findfaster.command: findfaster,
        stacktrace.command: stacktrace,
        topn.command: topn
    }

    parser = argparse.ArgumentParser(
        prog=sys.argv[0],
        description=ascii_name,
        epilog="",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-d", "--debug", action="store_true", help="Debug output")
    parser.add_argument("-e", "--echo-input", action="store_true",
                        help="""Echo the input provided to sysgrok. Useful when input is piped in
    and you want to see what it is""")
    parser.add_argument("-c", "--chat", action="store_true",
                        help="Enable interactive chat after each LLM response")
    parser.add_argument("--output-format", type=str, help="Specify the output format for the LLM to use")
    parser.add_argument("-m", "--model-or-deployment-id", dest="model", default="gpt-3.5-turbo",
                        help="""The OpenAI model, or Azure deployment ID, to use.""")
    parser.add_argument("--temperature", type=float, default=0, help="ChatGPT temperature. See OpenAI docs.")
    parser.add_argument("--max-concurrent-queries", type=int, default=4,
                        help="Maximum number of parallel queries to OpenAI")

    subparsers = parser.add_subparsers(help="The sub-command to execute", dest="sub_command")
    for v in commands.values():
        v.add_to_command_parser(subparsers)

    args = parser.parse_args()

    log_format = '%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s'
    log_date_format = '%Y-%m-%d %H:%M:%S'
    log_level = logging.INFO

    if args.debug:
        log_level = logging.DEBUG

    logging.basicConfig(format=log_format, datefmt=log_date_format, level=log_level)

    set_config(LLMConfig(args.model, args.temperature, args.max_concurrent_queries, args.output_format))

    if not args.sub_command:
        parser.print_help(sys.stderr)
        sys.stderr.write("\nNo sub-command selected\n")
        sys.exit(1)

    if args.sub_command not in commands:
        parser.print_help(sys.stderr)
        sys.stderr.write("\nUnknown sub-command\n")
        sys.exit(1)

    sys.exit(commands[args.sub_command].run(parser, args))
