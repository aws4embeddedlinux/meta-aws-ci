"""Helpers for running processes."""
import asyncio
import logging
from asyncio.subprocess import PIPE
from typing import Callable, Optional, Tuple

logger = logging.getLogger(__name__)

# Some light reading for this:
# https://docs.python.org/3.8/library/asyncio-subprocess.html
# https://kevinmccarthy.org/2016/07/25/streaming-subprocess-stdin-and-stdout-with-asyncio-in-python/


def run(cmd: str) -> Tuple[str, str, int]:
    """
    Run a command in the shell.

    This function runs commands while both capturing and logging the
    stderr and stdout.

    Parameters
    ------
    cmd : str
        The command to run.

    Returns
    -------
    (str, str, int)
        A tuple consisting of the stdout, stderr, and return code of
        the command.
    """
    stdout = list()
    stderr = list()

    def _read_stdout(line: str) -> None:
        logger.info(f"STDOUT> {line}")
        stdout.append(line)

    def _read_stderr(line: str) -> None:
        logger.info(f"STDERR> {line}")
        stderr.append(line)

    logger.info(f"running command {cmd}")
    ret_code = asyncio.run(_run(cmd, _read_stdout, _read_stderr))
    logger.debug(f"command {cmd} exited with return code {ret_code}")

    return ("\n".join(stdout), "\n".join(stderr), ret_code)


async def _run(cmd: str, stdout_cb: Callable[[str], None], stderr_cb: Callable[[str], None]) -> int:
    proc = await asyncio.create_subprocess_shell(cmd, stdout=PIPE, stderr=PIPE)
    await asyncio.wait(
        [
            _read_stream(proc.stdout, stdout_cb),
            _read_stream(proc.stderr, stderr_cb),
        ]
    )
    return await proc.wait()


async def _read_stream(stream: Optional[asyncio.StreamReader], cb: Callable[[str], None]) -> None:
    assert stream
    while True:
        line = await stream.readline()
        if line:
            cb(line.decode("utf-8").rstrip())
        else:
            break
