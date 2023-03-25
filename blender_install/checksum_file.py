import os
import shutil
from pathlib import Path
from typing import Optional, List
from install_utils import run_process, PLATFORM

CHK_FMTS = {"md5", "sha1", "sha256", "sha384", "sha512"}


def checksum_and_copy(fp: Path, target: Path):
    """
    Runs checksum on specified file and copies file to target dir if everything
    is fine.

    Parameters:
    -----------
    fp : Path
        Path to file to run checksum for.
    target : Path
        Path to folder to copy checksummed file.
    """
    print(f"Checking integrity of: {fp}")
    fp_checksum = [f"{str(fp)}.{i}" for i in CHK_FMTS]

    for i in fp_checksum:
        if os.path.exists(i):
            if os.path.isfile(i):
                if checksum_file(Path(i)):
                    print(f"Copied to: {shutil.copy2(fp, target)}")
                    return

    print("File was not copied - no checksum file found")


def checksum_file(checksum_file: Path) -> bool:
    """
    Uses os software to run checksum algorithm on file.

    Parameters:
    -----------
    checksum_file : Path
        Path to file that has hashfile.
    """
    checksum_fstr = str(checksum_file)
    # Dicts of (platform) -> (type of sum) -> command
    supported_chk_algos_win = {
        "md5": [
            "certutil",
            "-hashfile",
            checksum_fstr,
            "MD5",
        ],
        "sha1": [
            "certutil",
            "-hashfile",
            checksum_fstr,
            "SHA1",
        ],
        "sha256": [
            "certutil",
            "-hashfile",
            checksum_fstr,
            "SHA256",
        ],
        "sha384": [
            "certutil",
            "-hashfile",
            checksum_fstr,
            "SHA384",
        ],
        "sha512": [
            "certutil",
            "-hashfile",
            checksum_fstr,
            "SHA512",
        ],
    }
    supported_chk_algos_linux_mac = {
        "md5": [
            "md5sum",
            "-c",
        ],
        "sha1": [
            "shasum",
            "-a",
            "1",
            "-c",
        ],
        "sha256": [
            "shasum",
            "-a",
            "256",
            "-c",
        ],
        "sha384": [
            "shasum",
            "-a",
            "384",
            "-c",
        ],
        "sha512": [
            "shasum",
            "-a",
            "512",
            "-c",
        ],
    }
    supported_chk_plf = {
        "Linux": supported_chk_algos_linux_mac,
        "Darwin": supported_chk_algos_linux_mac,
        "Windows": supported_chk_algos_win,
    }

    command: Optional[List[str]] = None

    if checksum_file.suffixes[-1][1::] in supported_chk_plf[PLATFORM]:
        command = supported_chk_plf[PLATFORM][checksum_file.suffixes[-1][1::]]

        if PLATFORM in {"Linux", "Darwin"}:
            command.append(checksum_fstr)

    if command is None:
        print(
            "Could not construct checksum command: "
            "provided checksum file either not checksum or not supported"
        )
        return False

    print(f"Checksum command: {command}")

    ec, so, se, er = run_process(
        command,
        "Could not run checksum program on your OS, check that "
        "certutil is available on Windows and md5sum/shasum is available on "
        "Linux/Mac",
        5,
        wd=checksum_file.parent,
        print_std=True,
    )

    if ec != 0:
        print(f"Checksum failed with code: {ec} for file: {checksum_fstr}")
        return False

    return True
