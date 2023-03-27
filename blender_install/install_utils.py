import os
import shutil
import platform
from shutil import ignore_patterns, rmtree
from pathlib import Path
from install_config import InstallConfig
from typing import List, Dict, Set, Tuple, Optional, Union
from subprocess import Popen, PIPE
from checksum_file import checksum_and_copy

# Get the platform script is running on
PLATFORM = platform.system()


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


def try_to_install(cfg: InstallConfig):
    """Tries to symlink addon to addon folder, if fails - copies addon's files.

    Parameters:
    -----------
    cfg : InstallConfig
        Object with parsed and verified configuration.
    """
    symlynk_or_copy(cfg)
    manage_binaries(cfg)


def symlynk_or_copy(cfg: InstallConfig):
    """Tries to install addon to specified folder. As the fastest and by far best
    solution tries to symlink the blender_install to addon folder, so upon running
    Blender it just resolves to this folder with an addon. Otherwise tries to copy
    contents of this folder to specified addon path.

    Parameters:
    -----------
    cfg : InstallConfig
        Object with parsed and verified configuration.
    """
    cur_folder = cfg.current_folder
    addon_path = cfg.addon_path

    # Check that symlink already exists or user is able to create it, thus
    # any kind of *heavy* file copying is not needed
    chk_symlink = False

    # Remove release folder if it already exists, just to make sure copytree is
    # ok and runs without errors
    if addon_path.exists():
        if addon_path.is_symlink():
            print("Target folder is symlink, resolving")
            chk = addon_path.resolve(True)

            # Guarantee two Path objects are compared, not some arbitrary data
            if Path(chk) == Path(cur_folder) and cfg.addon_create_link:
                print("Symlink points to current folder, nothing will be done")
                chk_symlink = True
            else:
                print("Either symlink is incorrect, or copy of addon preferred")
                print("Removing symlink")
                os.unlink(addon_path)

        elif addon_path.is_dir():
            print("Target folder is folder")
            if not addon_path.is_symlink():
                print(f"Removing previous folder: {addon_path}")
                shutil.rmtree(addon_path)
            elif addon_path.is_symlink():
                print(f"Removing previous folder symlink: {addon_path}")
                os.unlink(addon_path)

        elif addon_path.is_file():
            print("Target folder is file")
            print(f"Removing 'file': {addon_path}")
            os.unlink(addon_path)
        else:
            raise OSError(f"Addon path is not symlink/directory/file")

    if not chk_symlink:
        create_symlink_or_copy(cfg)


def create_symlink_or_copy(cfg: InstallConfig):
    """Tries to recreate symlink to addon or copy addon files.

    Parameters:
    -----------
    cfg : InstallConfig
        Object with parsed and verified configuration.
    """
    cur_folder = cfg.current_folder
    addon_path = cfg.addon_path

    try:
        if cfg.addon_create_link:
            os.symlink(os.path.abspath(cur_folder), os.path.abspath(addon_path), True)

            if all(
                (
                    addon_path.is_symlink(),
                    Path(addon_path.resolve(True)) == Path(cur_folder),
                )
            ):
                # Symlink creation successful - no need to copy
                print(
                    "Successfully created symlink, no files will be copied "
                    "to Blender3D addon folder"
                )
                chk_symlink = True
        else:
            raise Exception("Preferred to copy the addon, falling back to copy")

    except Exception as e:
        print(f"Trying to copy addon files because:\n{e}")
        try:
            # Copy current folder to the release folder
            ignore_files: List[str] = []

            if cfg.install_exclude is not None:
                with open(cfg.install_exclude, "rt") as ii:
                    ignore_files = [
                        li.replace("/", "") for li in ii.read().splitlines()
                    ]

            shutil.copytree(
                os.getcwd(),
                addon_path,
                ignore=ignore_patterns(*(pat for pat in ignore_files))
                if len(ignore_files) > 0
                else None,
            )

        except Exception as e:
            print(f"All installation methods exausted. Tree copy failed: {e}")


def manage_binaries(cfg: InstallConfig):
    """Copies or compiles binaries - WIP.

    Parameters:
    -----------
    cfg : InstallConfig
        Object with parsed and verified configuration.
    """
    if cfg.binaries_compile:
        print("Compilation of binaries is not yet supported\n")
    else:
        print("Copying binaries in repository workfolder\n")
        copy_precompiled(cfg)


def copy_precompiled(cfg: InstallConfig):
    """
    Copies precompiled binaries to bin/ folder.

    Parameters:
    -----------
    cfg : InstallConfig
        Object with parsed and verified configuration.
    """
    dir_bin_precompiled = cfg.binaries_precompiled_path
    dir_target = cfg.binaries_path

    os.makedirs(dir_target, exist_ok=True)

    # Linux uses either no extension or AppImage or other ways to publish apps
    # Mac uses app format
    # Windows has exe and dlls
    # Sets can be extended in the future
    # Precompiled binary Python modules are pyd
    bin_ext: Dict[str, Set[str]] = {
        "Linux": {"", "so", "d"},
        "Darwin": {
            "app",
        },
        "Windows": {"exe", "dll"},
        "All": {
            "pyd",
        },
    }

    for rt, drs, fls in os.walk(dir_bin_precompiled, topdown=True):
        for fl in fls:
            fp = Path(rt, fl)
            fl_ext = fp.suffixes[-1][1::] if fp.suffixes else ""

            if any(
                (
                    fl_ext in bin_ext[PLATFORM],
                    fl_ext in bin_ext["All"],
                    fl_ext == "",
                )
            ):
                if fp.is_file():
                    checksum_and_copy(fp, dir_target)
                elif fp.is_dir():
                    print("Not checksumming the folder, just copy")
                    print(f"Dir copied to: {shutil.copytree(fp, dir_target)}")
                else:
                    print(f"{Path(rt, fl)} is not file or dir, not copying")

        # Only one level is copied at the moment
        break


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
                rmtree(target, True)
