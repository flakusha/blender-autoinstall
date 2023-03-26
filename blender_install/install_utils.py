import argparse
import os
import sys
import shutil
import platform
from shutil import ignore_patterns
from pathlib import Path
from install_config import InstallConfig
from typing import List, Dict, Set, Tuple, Optional, Union
from subprocess import Popen, PIPE, TimeoutExpired
from checksum_file import checksum_and_copy

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
            if Path(chk) == Path(cur_folder):
                print(
                    "Symlink points to current folder, no additional "
                    "actions are needed"
                )
                chk_symlink = True
            else:
                print("Symlink path is incorrect, removing it")
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
        try:
            os.symlink(os.path.abspath(cur_folder), os.path.abspath(addon_path), True)

            if all(
                (
                    addon_path.is_symlink(),
                    Path(addon_path.resolve(True)) == Path(cur_folder),
                )
            ):
                # Symlink creation successfull - no need to copy
                print(
                    "Successfully created symlink, no files will be copied "
                    "to Blender3D addon folder"
                )
                chk_symlink = True

        except Exception as e:
            print(f"Symlink creation failed - trying to copy addon files instead:\n{e}")
            try:
                shutil.copytree(cfg.current_folder, cfg.addon_path)
            except Exception as e:
                print(f"All installation methods exausted. Tree copy failed: {e}")


def manage_binaries(cfg: InstallConfig):
    if cfg.binaries_compile:
        if kwargs["compile"]:
            print("Compilation of binaries is not yet supported\n")
        else:
            print("Copying binaries in repository workfolder\n")
            copy_precompiled(cur_folder)

    # Other steps are not needed if symlink was created
    if chk_symlink:
        print("Finished repo setup\n")
        return

    # Copy current folder to the release folder
    ignore_files: List[str] = []

    with open(Path(cur_folder, "install_exclude.txt"), "rt") as ii:
        ignore_files = [li.replace("/", "") for li in ii.read().splitlines()]

    path_addon = shutil.copytree(
        os.getcwd(),
        addon_path,
        ignore=ignore_patterns(*(pat for pat in ignore_files)),
    )

    if isinstance(path_addon, Path):
        print(
            "Copied to: {}, resulting size is: {}".format(
                path_addon, shutil.disk_usage(path_addon)
            )
        )
    else:
        print(f"Copytree returned error: {path_addon}")
        sys.exit(2)

    if "archive" in kw:
        if kwargs["archive"]:
            os.chdir(tgt_folder)
            cur_folder = os.getcwd()  # Update the variable after the cd
            print(f"Changed working directory to: {os.getcwd()}")
            shutil.make_archive(
                addon_path.parts[-1], "zip", tgt_folder, addon_path.parts[-1]
            )

            print("Release zip is ready")
        else:
            print("Release is shipped")


def copy_precompiled(current_folder: Path):
    """
    Copies precompiled binaries to bin/ folder.
    """
    dir_bin_precompiled = Path(current_folder, "bin_precompiled")
    dir_target = Path(current_folder, "bin")
    os.makedirs(dir_target, exist_ok=True)

    # Linux uses either no extension or AppImage or other ways to publish apps
    # Mac uses app format
    # Windows has exe and dlls
    # Sets can be extended in the future
    # Precompiled binary Python modules are pyd
    bin_ext: Dict[str, Set[str]] = {
        "Linux": {"", "so", "d"},
        "Darwin": {"app"},
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

        # Only need the highest one, I know there is listdir, but I have
        # already finished this version
        print()
        break


def run_popen(
    command: List[str], wd=os.getcwd(), stdin=PIPE, stdout=PIPE, stderr=PIPE
) -> Popen:
    """
    Runs the Popen with specified command and working directory.

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
        encoding="utf8",
    )


def comm_popen(
    proc: Popen, error_message: Optional[str], t=360, print_std=True
) -> Tuple[Optional[int], str, str, Optional[Exception]]:
    """
    Similar to communicate_proc, but also tries to extract return code from
    executed app.

    :returns: exit code, stdout, stderr, error message.
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
    """
    Wraps run_proc and communicate_proc_exit_code functions into one.
    Runs Popen, captures logging output and waits for execution for designated
    timeout, if execution is not finished, prints out error message. Can
    optionally print out stdout and stderr.
    """
    return comm_popen(run_popen(command, wd), error_message, timeout, print_std)
