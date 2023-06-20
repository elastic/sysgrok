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
# under the License.import argparse

import argparse
import logging
import sys

from perfcopilot.llm import print_streamed_llm_response, chat


command = "explainprocess"
help = "Explain what a process does and suggest optimisations"


def add_to_command_parser(subparsers):
    parser = subparsers.add_parser(command, help=help)
    parser.add_argument("--no-optimizations", action='store_true', default=False,
                        help="Do not suggest optimizations")
    parser.add_argument("process", nargs=argparse.REMAINDER, help="The process to explain, and its arguments")

# explainprocess is implemented as a two step conversation. First we ask the LLM for an explanation of the
# process. Then, afterwards, if the user has asked for suggested optimisations, we
# continue the conversation (including the response to the explanation request) and ask for those suggestions.


explain_prompt = """I am a software engineer. I am trying to understand what a process running on my
Linux machine does.

Your task is to first describe what the process is and what its general use cases are. If I also provide you
with the arguments to the process you should then explain its arguments and how they influence the behaviour
of the process. If I do not provide any arguments then explain the behaviour of the process when no arguments are
provided.

If you do not recognise the process say "No information available for this process". If I provide an argument
to the process that you do not recognise then say "No information available for this argument" when explaining
that argument.

Here is an example with arguments.
Process: metricbeat -c /etc/metricbeat.yml -d autodiscover,kafka -e -system.hostfs=/hostfs
Explaination: Metricbeat is part of the Elastic Stack. It is a lightweight shipper that you can install on your
servers to periodically collect metrics from the operating system and from services running on the server.
Use cases for Metricbeat generally revolve around infrastructure monitoring. You would typically install
Metricbeat on your servers to collect metrics from your systems and services. These metrics are then
used for performance monitoring, anomaly detection, system status checks, etc.

Here is a breakdown of the arguments used:

* -c /etc/metricbeat.yml: The -c option is used to specify the configuration file for Metricbeat. In
this case, /etc/metricbeat.yml is the configuration file. This file contains configurations for what
metrics to collect and where to send them (e.g., to Elasticsearch or Logstash).

* -d autodiscover,kafka: The -d option is used to enable debug output for selected components. In
this case, debug output is enabled for autodiscover and kafka components. The autodiscover feature
allows Metricbeat to automatically discover services as they get started and stopped in your environment,
and kafka is presumably a monitored service from which Metricbeat collects metrics.

* -e: The -e option is used to log to stderr and disable syslog/file output. This is useful for debugging.

* -system.hostfs=/hostfs: The -system.hostfs option is used to set the mount point of the host’s
filesystem for use in monitoring a host from within a container. In this case, /hostfs is the mount
point. When running Metricbeat inside a container, filesystem metrics would be for the container by
default, but with this option, Metricbeat can get metrics for the host system.

Here is an example without arguments.
Process: metricbeat
Explanation: Metricbeat is part of the Elastic Stack. It is a lightweight shipper that you can install on your
servers to periodically collect metrics from the operating system and from services running on the server.
Use cases for Metricbeat generally revolve around infrastructure monitoring. You would typically install
Metricbeat on your servers to collect metrics from your systems and services. These metrics are then
used for performance monitoring, anomaly detection, system status checks, etc.

Running it without any arguments will start the process with the default configuration file, typically
located at /etc/metricbeat/metricbeat.yml. This file specifies the metrics to be collected and where
to ship them to.

Now explain this process to me.
Process: {process}
Explanation:"""

optimize_prompt = """Assuming the process {process} is consuming significant CPU resources.
Suggest ways to optimize or improve the system that involve the {process}.
Types of improvements that would be useful to me are improvements that result in:

- Higher performance so that the system runs faster or uses less CPU
- Better memory efficient so that the system uses less RAM
- Better storage efficient so that the system stores less data on disk.
- Better network I/O efficiency so that less data is sent over the network
- Better disk I/O efficiency so that less data is read and written from disk

Make up to five suggestions. Your suggestions must meet all of the following criteria:
1. Your suggestions should be detailed, technical and include concrete examples.
2. Your suggestions should be specific to improving performance of a system in which the {process} process is
consuming significant CPU
2. If you suggest replacing the function or library with a more efficient replacement you must suggest at least
one concrete replacement.

If you know of fewer than five ways to improve the performance of a system in which the {process} process
is consuming significant CPU, then provide fewer than five suggestions. If you do not know of any
way in which to improve the performance then say "I do not know how to improve the performance of systems where
this process is consuming a significant amount of CPU".

If you have suggestions, the output format should look as follows:

Here are some suggestions as to how you might optimize your system if {process} is consuming significant
resources:
1. Insert first suggestion
2. Insert second suggestion
etc."""


def run(args_parser, args):
    if not args.process:
        logging.error("Process not provided")
        sys.exit(1)

    if args.process[0] == '--':
        args.process = args.process[1:]

    args.process = " ".join(args.process)
    logging.debug(f"Analyzing command: {args.process}")

    if args.echo_input:
        print(f"{args.process}")

    conversation = print_streamed_llm_response(explain_prompt.format(process=args.process))

    if args.chat:
        chat(conversation)

    if args.no_optimizations:
        return 0

    sys.stdout.write("\n")

    conversation = print_streamed_llm_response(optimize_prompt.format(process=args.process), conversation)
    if args.chat:
        chat(conversation)

    return 0
