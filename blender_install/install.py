import os
import argparse
from pathlib import Path
from typing import Tuple, Set

# Make it possible to import modules **in** blender environment
# dircur = os.path.dirname(__file__)
# if dircur not in sys.path:
#     sys.path.append(os.path.dirname(__file__))

# Now import is available
from install_utils import (
    try_to_install,
    copy_precompiled,
    run_process,
    PLATFORM,
)
from install_config import InstallConfig


def install_addon(cfg: InstallConfig):
    """
    Install plugin to specified folder.

    Parameters:
    -----------
    cfg : InstallConfig
        Parsed and validated configuration file object.
    """
    path_current = cfg.current_folder
    addon_name = cfg.addon_name

    # Now it's possible to select correct folder and config
    addon_path: Path = cfg.addon_path

    if addon_path.parts[-1] != addon_name:
        addon_path = Path(addon_path, addon_name)

    print(f"Syncing addon folder\nFr: {path_current}\nTo: {addon_path}")

    try_to_install(cfg)


def install_pip(cfg: InstallConfig) -> bool:
    """Install pip for instance of Blender3D.

    Parameters:
    -----------
    cfg : InstallConfig
        Parsed and validated config object.

    Returns:
    --------
    bool
        PIP activation is successfull.
    """
    if cfg.install_pip_script is None:
        print("No PIP install script provided, skipping")

    # Install pip
    print("Trying to install PIP")
    install_pip_script = cfg.install_pip_script

    install_cmd = [
        args.blender,
        "-b",
        "-P",
        str(install_pip_script),
    ]

    ec, so, se, er = run_process(
        install_cmd, "Failed to install pip", 30, print_std=False
    )

    if ec != 0:
        return False

    return True


def activate_addons(cfg: InstallConfig) -> bool:
    """
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
        Addon activation is successfull.
    """

    if len(cfg.activate_addons) == 0:
        print("Skipping addon activation")
        return True

    if cfg.install_activate_script is None:
        print("No activation script provided, but activation is requested, aborting")
        return False

    inst_act_script = Path(os.path.dirname(Path(__file__)), "install_activate.py")

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
        install_addon(cfg)

        print("Trying to activate addons")
        if not install_pip(cfg):
            exit(1)

        if not activate_addons(cfg):
            exit(1)

        if not install_custom(cfg):
            exit(1)
    else:
        print(f"Installation on this OS({PLATFORM}) is not supported.")
        print("Please install addon manually...")
