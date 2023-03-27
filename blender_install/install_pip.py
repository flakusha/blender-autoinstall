import os
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Optional

# Make it possible to import modules
dircur = os.path.dirname(__file__)
if dircur not in sys.path:
    sys.path.append(os.path.dirname(__file__))

from install_utils import run_process

# Get the data about Python from sys environment
python_blender = str(Path(sys.executable).resolve(True))
python_dir = "python{}.{}".format(sys.version_info.major, sys.version_info.minor)
blend_cwd = str(os.path.dirname(python_blender))
python_target = str(Path(sys.prefix, "lib", python_dir, "site-packages"))


def install_pip() -> Tuple[Optional[int], str, str, Optional[Exception]]:
    """Picks environment of the blender instance that run it and runs ensurepip for
    this environment. Doesn't require any arguments.
    """
    blend_py = str(python_blender)

    pip_cmd = [
        blend_py,
        "-m",
        "ensurepip",
        "-U",
    ]

    ec, so, se, er = run_process(
        pip_cmd, "PIP installation failed", 15, blend_cwd, False
    )

    return ec, so, se, er


def install_pip_modules(modules: List[str]) -> bool:
    """Installs all the pip modules provided in the list.

    Parameters:
    -----------
    modules : List[str]
        List of modules' names.
    """
    python_target = str(Path(sys.prefix, "lib", python_dir, "site-packages"))
    install_succeed = []

    for module in modules:
        install_succeed.append(install_module(module, python_target))

    res = set(install_succeed)

    if None not in res and len(res) == 1:
        return True

    return False


def install_module(module: str, target: str) -> Optional[int]:
    """Installs PIP module to the target environment.

    Parameters:
    -----------
    module : str
        Name of the module.
    target : str
        Pip target directory.
    """
    pip_cmd = [
        python_blender,
        "-m",
        "pip",
        "install",
        "-U",
        "--upgrade-strategy",
        "only-if-needed",
        module,
        "-t",
        target,
    ]

    ec, so, se, er = run_process(
        pip_cmd,
        "Could not install module",
        60,
        blend_cwd,
        True,
    )

    return ec


if __name__ == "__main__":
    ec, so, se, er = install_pip()

    argv = sys.argv
    argv = argv[argv.index("--") + 1 :]

    # Extract comma-separated python modules
    if len(argv) > 0:
        if "-m" in argv:
            idxm = argv.index("-m")
            pip_modules: List[str] = argv[argv.index("-m") + 1].split(",")
            pip_modules = [m.strip() for m in pip_modules]

    if ec is not None:
        if ec == 0:
            if len(pip_modules) > 0:
                if install_pip_modules(pip_modules):
                    exit(0)

    exit(1)
