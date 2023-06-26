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

from dataclasses import dataclass
import logging

import fabric


@dataclass
class CommandResult:
    """Contains the result of executing a command, including its exit code, stdout and stderr"""

    command: str
    exit_code: int
    stdout: str
    stderr: str


def execute_commands_remote(host: str, commands: list) -> dict:
    """Executes the provided commands on the specified host.

    Args:
        host: The host to connect to. Must be defined in the ssh .config file for the system.
        commands: A list of commands and their arguments.

    Returns:
        command output: A dictionary mapping commands to CommandResults.
    """

    res = {}
    with fabric.Connection(host) as conn:
        for command in commands:
            tries = 0
            success = False
            while not success and tries < 3:
                tries += 1
                logging.debug(f"Executing '{command}' on {host}")

                try:
                    e = conn.sudo(command, hide=True, timeout=20, warn=True)
                    if e.ok:
                        logging.debug(f"stdout from {command}: {e.stdout}")
                    else:
                        logging.error(f"Failed to execute '{command}' on {host}. Non-zero exit code: {e.return_code}.")
                        logging.debug(f"stdout: {e.stdout}")
                        logging.debug(f"stderr: {e.stderr}")

                    res[command] = CommandResult(command, e.return_code, e.stdout, e.stderr)
                    success = True
                except Exception as e:
                    logging.error(f"Failed to execute '{command}' on {host}. Exception: {e}")

            if not success:
                logging.error(f"Failed to execute '{command}' on {host}")

    return res