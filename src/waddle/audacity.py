import os
import sys
import logging
from typing import TextIO
from contextlib import contextmanager
import time


logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)


class AudacityClient:
    def __init__(self, to_file: TextIO, from_file: TextIO, eof: str):
        self.to_file = to_file
        self.from_file = from_file
        self.eof = eof

    @staticmethod
    @contextmanager
    def new():
        match sys.platform:
            case "win32":
                to_name = "\\\\.\\pipe\\ToSrvPipe"
                from_name = "\\\\.\\pipe\\FromSrvPipe"
                eof = "\r\n\0"
            case "darwin":
                to_name = "/tmp/audacity_script_pipe.to." + str(os.getuid())
                from_name = "/tmp/audacity_script_pipe.from." + str(os.getuid())
                eof = "\n"

                # delete the pipe files if they exist
                for name in [to_name, from_name]:
                    if os.path.exists(name):
                        os.unlink(name)

                # restart Audacity
                os.system("killall -9 'Audacity' 2>/dev/null")
                if os.system("open -a Audacity") != 0:
                    raise RuntimeError("Audacity failed to start")
                time.sleep(2)
            case _:
                to_name = "/tmp/audacity_script_pipe.to." + str(os.getuid())
                from_name = "/tmp/audacity_script_pipe.from." + str(os.getuid())
                eof = "\n"
        if not os.path.exists(to_name) or not os.path.exists(from_name):
            raise FileNotFoundError(
                "Audacity script pipe not found. Please ensure Audacity is running."
            )
        logger.debug(f"Connecting to Audacity: {to_name}, {from_name}")
        with open(to_name, "w") as to_file, open(from_name, "rt") as from_file:
            logger.debug("Connected to Audacity")
            yield AudacityClient(to_file, from_file, eof)

    def _send(self, message: str):
        logger.debug(f"Sending message: {message}")
        self.to_file.write(message + self.eof)
        self.to_file.flush()

    def _receive(self) -> str:
        msg = ""
        line = ""
        while True:
            msg += line
            line = self.from_file.readline()
            if line == self.eof and len(msg) > 0:
                break
        return msg

    def _do_command(self, command: str) -> str:
        self._send(command)
        # TODO(shumbo): Implement a timeout
        response = self._receive()
        time.sleep(1)
        return response

    def new_project(self) -> None:
        self._do_command("New:")

    def import2(self, path: str) -> None:
        self._do_command(f"Import2: Filename={path}")
        return None

    def save_project2(self, path: str) -> None:
        self._do_command(f"SaveProject2: Filename={path}")
        return None

    def close(self) -> None:
        self._do_command("Close:")

    def select_all(self) -> None:
        self._do_command("SelectAll:")

    def truncate_silence(self, threshold: float, truncate=0.5):
        self._do_command(f"TruncateSilence: Threshold={threshold} Truncate={truncate}")
