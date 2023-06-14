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