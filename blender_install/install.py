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

    print("Trying to install PIP")

    cmd = [
        str(cfg.blender_path),
        "-b",
        "-P",
        str(cfg.install_pip_script),
    ]

    if cfg.pip_modules is not None:
        if len(cfg.pip_modules) > 0:
            cmd.extend(["--", "-m", ",".join(m for m in cfg.pip_modules)])

    ec, so, se, er = run_process(cmd, "Failed to install pip", 30, print_std=False)

    return ec == 0


def activate_addons(cfg: InstallConfig) -> bool:
    """
    Activate addons that are found in config.activate_addons list.
    Only addon names are supported.
    addon_utils are stabilized, but not documented in Blender3D API.
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

    if cfg.install_activate_script is None:
        print("No activation script provided, but activation is requested, aborting")
        return False

    cmd = [
        str(cfg.blender_path),
        "-b",
        "-P",
        str(cfg.install_activate_script),
    ]

    if len(cfg.activate_addons) > 0:
        cmd.extend(["--", "-a", ",".join(a for a in cfg.activate_addons)])

    print("Activating addons and components")
    ec, so, se, er = run_process(cmd, "Addon activation failed", 60, print_std=False)

    return ec == 0


def run_custom_script(cfg: InstallConfig) -> bool:
    """Run custom script which is needed to set up additional components for the addon.
    If no script is provided, this stage will be skipped.

    Parameters:
    -----------
    cfg : InstallConfig
        Parsed and validated config object.

    Returns:
    --------
    bool
        Script run successfully.
    """
    if cfg.install_custom_script is None:
        print("skipping custom script")
        return True

    cmd = [
        str(cfg.blender_path),
        "-b",
        "-P",
        str(cfg.install_custom_script),
    ]

    if len(cfg.install_custom_args) > 0:
        cmd.append("--")
        cmd.extend(cfg.install_custom_args)

    print("Running custom script:")
    ec, so, se, er = run_process(
        cmd, "Custom script run failed", cfg.install_custom_timeout, print_std=False
    )

    return ec == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Automated installer for Blender3D",
        add_help=True,
    )

    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Path to installation config toml",
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

        if not run_custom_script(cfg):
            exit(1)

    else:
        print(f"Installation on this OS({PLATFORM}) is not supported.")
        print("Please install addon manually...")
