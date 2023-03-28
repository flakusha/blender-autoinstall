import os
import shutil
from subprocess import Popen, PIPE
from pathlib import Path
from typing import List, Tuple, Union, Set, Optional
from install_platform import PLATFORM


def executable_exists(name: Union[str, Path]) -> bool:
    """
    Check that program is installed.

    Parameters:
    -----------
    name : Union[str, Path]
        Name/path of executable.

    Returns:
    --------
    bool
        Executable exists.
    """
    return shutil.which(str(name), mode=os.X_OK) is not None


def run_popen(
    command: List[str], wd=os.getcwd(), stdin=PIPE, stdout=PIPE, stderr=PIPE
) -> Popen:
    """Runs the Popen with specified command and working directory.

    Parameters:
    -----------
    command : List[str]
        Command list to execute, e.g. ["echo", "Hello there"].
    wd : str
        Working directory for execution.
    stdin : PIPE
        Pipe for stdin.
    stdout : PIPE
        Pipe for stdout.
    stderr : PIPE
        Pipe for stderr.

    Returns:
    --------
    Popen
        Popen instance.
    """
    return Popen(
        args=command,
        cwd=wd,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
        encoding="utf8" if PLATFORM in {"Linux", "Darwin"} else os.device_encoding(0),
    )


def comm_popen(
    proc: Popen, error_message: Optional[str], t=360, print_std=True
) -> Tuple[Optional[int], str, str, Optional[Exception]]:
    """Similar to communicate_proc, but also tries to extract return code from
    executed app.

    Parameters:
    -----------
    proc : Popen
        Instance of Popen process.
    error_message : Optional[str]
        String to print in case of process failure/timeout.
    t : float
        Timeout.
    print_std : bool
        Option to print all the data transferred during the run.

    Returns:
    --------
    exit_code : Optional[int]
        Exit code of the process.
    stdout : str
        Stdout of the process.
    stderr : str
        Stderr of the process.
    exception : Optional[Exception]
        Exception that occured during the run.
    """
    exit_code = None
    outs = ("", "")
    error = None

    if error_message is None:
        error_message = f"Failed to execute: {proc}"

    try:
        outs = proc.communicate(timeout=t)
        exit_code = proc.wait(timeout=t)

    except Exception as e:
        proc.kill()
        outs = proc.communicate(timeout=0.01)
        exit_code = proc.poll()
        print(error_message)
        error = e

    finally:
        if print_std:
            print(f"EXIT: {exit_code}")

            if len(outs[0]) > 0:
                print(f"STDOUT:\n{outs[0]}")
            if len(outs[1]) > 0:
                print(f"STDERR:\n{outs[1]}")

            if error is not None:
                print(f"ERROR: {error}")

        return (
            int(exit_code) if exit_code is not None else None,
            outs[0],
            outs[1],
            error,
        )


def run_process(
    command: List[str],
    error_message="Could not run program",
    timeout=360,
    wd=os.getcwd(),
    print_std=True,
) -> Tuple[Optional[int], str, str, Optional[Exception]]:
    """Wraps run_proc and communicate_proc_exit_code functions into one.
    Runs Popen, captures logging output and waits for execution for designated
    timeout, if execution is not finished, prints out error message. Can
    optionally print out stdout and stderr.

    Parameters:
    -----------
    command : List[str]
        Terminal command to run.
    error_message : Optional[str]
        String to print in case of process failure/timeout.
    t : float
        Timeout.
    wd : str
        Working directory to start process in.
    print_std : bool
        Option to print all the data transferred during the run.

    Returns:
    --------
    exit_code : Optional[int]
        Exit code of the process.
    stdout : str
        Stdout of the process.
    stderr : str
        Stderr of the process.
    exception : Optional[Exception]
        Exception that occured during the run.
    """
    return comm_popen(run_popen(command, wd), error_message, timeout, print_std)


def rmtree_protected(target: Path, allowed_paths: Set[Path]):
    """Removes directory in case it's in allowed set of directories.

    Parameters:
    -----------
    target : Path
        Directory to remove.
    allowed_paths : Set[Path]
        Set of Paths with allowed operations on them.
    """
    if target.exists():
        if target.is_dir():
            if len(set(target.parents).intersection(allowed_paths)) > 0:
                shutil.rmtree(target, True)
