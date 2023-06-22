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


def execute_commands_remote(host, commands):
    """Execute the provided commands on the specified host. The results are return as a dict where
    the key is the command and the value is the output.
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

                    res[command] = {"exit_code": e.return_code, "stderr": e.stderr, "stdout": e.stdout}
                    success = True
                except Exception as e:
                    logging.error(f"Failed to execute '{command}' on {host}. Exception: {e}")

            if not success:
                logging.error(f"Failed to execute '{command}' on {host}")

    return res