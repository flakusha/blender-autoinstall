import os
import sys
import platform
import argparse
import shutil
from pathlib import Path
from typing import Tuple, Set

# Make it possible to import modules **in** blender environment
# dircur = os.path.dirname(__file__)
# if dircur not in sys.path:
#     sys.path.append(os.path.dirname(__file__))

# Now import is available
from install_utils import (
    executable_exists,
    try_to_install,
    copy_precompiled,
    run_process,
    PLATFORM,
)
from install_config import InstallConfig


def install_addon(cfg: InstallConfig) -> Tuple[bool, Path]:
    """
    Install plugin to specified folder.

    Parameters:
    -----------
    cfg : InstallConfig
        Parsed and validated configuration file object.
    """
    path_current = Path(os.path.dirname(os.path.realpath(__file__)))
    blender_exec = Path(cfg.blender_path).resolve()
    addon_name = cfg.addon_name

    version = cfg.blender_version

    # Now it's possible to select correct folder and config
    addon_path: Path = cfg.addon_path

    if addon_path.parts[-1] != addon_name:
        addon_path = Path(addon_path, addon_name)

    if args.compile_binaries:
        print("Compilation of binaries is not yet supported")
    else:
        copy_precompiled(os.getcwd())

    print("Syncing addon folder")
    print(path_current, "->", addon_path)

    try_to_install(cfg)

    # If it's dry run don't try to activate addons later,
    # so False will be returned
    return inst, addon_path


def activate_addons(cfg: InstallConfig) -> bool:
    """Install pip for instance of Blender3D.
    Activate addons that are found in config.activate_addons list.
    Only addon names are supported.
    Be careful, addon_utils are stabilized, but not documented in Blender3D API.
    For information see sources:
    https://github.com/blender/blender/blob/master/release/scripts/modules/addon_utils.py

    Parameters:
    -----------
    cfg : InstallConfig
        Parsed and validated config object.

    Returns:
    --------
    bool
        PIP activation and addon instllation is successfull.
    """
    if not cfg.activate_addons:
        print("Skipping PIP installation and addon activation")
        return True

    # Install pip
    print("Trying to install PIP")
    install_pip_script = os.path.dirname(Path(__file__))
    install_pip_script = Path(install_pip_script, "install_pip.py")

    install_cmd = [
        args.blender,
        "-b",
        "-P",
        str(install_pip_script),
    ]

    print("Pip activation result:")
    ec, so, se, er = run_process(install_cmd, "Pip is not active", 20, print_std=False)

    if ec != 0:
        return False

    # Assume that previous part of code was successful with
    # blender executable and additional check is not needed
    activate_script = os.path.dirname(Path(__file__))
    activate_script = Path(activate_script, "activate.py")
    update_cmd = [
        args.blender,
        "-b",
        "-P",
        str(activate_script),
    ]

    print("Activation result for addons and other components:")
    ec, so, se, er = run_process(
        update_cmd, "Addon activation failed", 60, print_std=False
    )

    if ec != 0:
        return False

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Automated installer for Blender3D",
        add_help=True,
    )

    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Path to installation config yaml",
        default=Path(Path(__file__).resolve(), "install_config.toml"),
    )

    args = parser.parse_args()

    cfg = InstallConfig(Path(args.config).resolve(True))

    installed = None

    if PLATFORM in ("Linux", "Darwin", "Windows"):
        print(f"Installing plugin for platform: {PLATFORM}")
        installed = install_addon(cfg)
    else:
        print(f"Installation on this OS({PLATFORM}) is not supported.")
        print("Please install addon manually...")

    if installed is not None:
        print("Trying to activate addons")
        activate_addons(cfg)
