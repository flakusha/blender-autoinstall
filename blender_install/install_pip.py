import os
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Optional

# Make it possible to import modules
dircur = os.path.dirname(__file__)
if dircur not in sys.path:
    sys.path.append(os.path.dirname(__file__))

from install_proc_utils import run_process
from install_platform import EC

# Get the data about Python from sys environment
python_blender = str(Path(sys.executable).resolve(True))
python_dir = "python{}.{}".format(sys.version_info.major, sys.version_info.minor)
blend_cwd = str(os.path.dirname(python_blender))
python_target = str(Path(sys.prefix, "lib", python_dir, "site-packages"))


def install_pip() -> Tuple[Optional[int], str, str, Optional[Exception]]:
    """Picks environment of the blender instance that run it and runs ensurepip for
    this environment. Doesn't require any arguments.

    Returns:
    --------
    Tuple[Optional[int], str, str, Optional[Exception]]
        Tuple of run_process results.
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

    Returns:
    --------
    bool
        Installation of pip modules is successful.
    """
    python_target = str(Path(sys.prefix, "lib", python_dir, "site-packages"))
    install_succeed = []

    for module in modules:
        install_succeed.append(install_module(module, python_target))

    res = set(install_succeed)

    if len(res) == 1 and 0 in res:
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

    Returns:
    --------
    Optional[int]
        Exit code for module installation.
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
        f"Could not install pip module: {module}",
        60,
        blend_cwd,
        True,
    )

    return ec


if __name__ == "__main__":
    # Pip will be installed in any case
    ec, so, se, er = install_pip()

    if ec is not None:
        if ec != 0:
            sys.exit(EC.PIP_NOT_INSTALLED.value)
    else:
        sys.exit(EC.PIP_NOT_INSTALLED.value)

    parser = argparse.ArgumentParser(
        description="pip and pip modules install script",
        add_help=True,
    )
    argv = sys.argv

    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        # No additional arguments provided, exiting without error
        sys.exit()

    parser.add_argument(
        "-m",
        "--modules",
        default="",
        type=str,
        help="Comma-separated list of pip modules in format supported by pip",
    )

    args = parser.parse_args(argv)
    pip_modules: List[str] = []

    # Extract comma-separated python modules
    if hasattr(args, "modules"):
        if len(args.modules) > 0:
            pip_modules = args.modules.split(",")
            pip_modules = [m.strip() for m in pip_modules]

        if len(pip_modules) > 0:
            if not install_pip_modules(pip_modules):
                print("All or some pip modules are installed incorrectly")
                sys.exit(EC.PIP_MODULES_NOT_INSTALLED.value)
