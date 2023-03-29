import argparse
import sys
from pprint import pprint
from pathlib import Path
from typing import Optional

from install_utils import (
    try_to_install,
)
from install_config import InstallConfig
from install_platform import PLATFORM, EC
from install_proc_utils import run_process


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
    addon_path = cfg.addon_path

    if addon_path.parts[-1] != addon_name:
        addon_path = Path(addon_path, addon_name)

    print(f"Syncing addon folder\nFr: {path_current}\nTo: {addon_path}")

    try_to_install(cfg)


def install_pip(cfg: InstallConfig) -> Optional[int]:
    """Install pip for instance of Blender3D.

    Parameters:
    -----------
    cfg : InstallConfig
        Parsed and validated config object.

    Returns:
    --------
    Optional[int]
        Propagates run_process exit code.
    """
    if cfg.install_pip_script is None:
        print("No PIP install script provided, skipping")

    cmd = [
        str(cfg.blender_path),
        "-b",
        "-P",
        str(cfg.install_pip_script),
    ]

    if cfg.pip_modules is not None:
        if len(cfg.pip_modules) > 0:
            cmd.extend(["--", "-m", ",".join(m for m in cfg.pip_modules)])

    print("Trying to install PIP")
    ec, so, se, er = run_process(
        cmd, "Failed to install pip or pip modules", 30, print_std=False
    )

    return ec


def activate_addons(cfg: InstallConfig) -> Optional[int]:
    """Setup Blender3D for rendering and also activate addons that are found in
    config.activate_addons list.
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

    if any(
        (
            sc := cfg.setup_compute_devices,
            ad := (len(cfg.activate_addons) > 0),
        )
    ):
        cmd.append("--")

        if sc:
            cmd.append("-g")

        if ad:
            cmd.extend(["-a", ",".join(a for a in cfg.activate_addons)])

    print("Activating addons and components")
    ec, so, se, er = run_process(cmd, "Addon activation failed", 60, print_std=False)

    return ec


def run_custom_script(cfg: InstallConfig) -> Optional[int]:
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
        print("Skipping custom script")
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

    return ec


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
        required=True,
    )

    args = parser.parse_args()

    cfg = (
        InstallConfig(Path(args.config).resolve(True))
        if "config" in args
        else sys.exit(EC.CONFIG_NOT_PROVIDED.value)
    )

    print("Validated config:")
    pprint(vars(cfg))

    if PLATFORM in ("Linux", "Darwin", "Windows"):
        print(f"Installing plugin for platform: {PLATFORM}")
        install_addon(cfg)

        print("Trying to activate addons")
        if (ec := install_pip(cfg)) != 0:
            sys.exit(ec)

        if (ec := activate_addons(cfg)) != 0:
            sys.exit(ec)

        if (ec := run_custom_script(cfg)) != 0:
            sys.exit(ec)

    else:
        print(f"Installation on this OS({PLATFORM}) is not supported.")
        print("Please install addon manually...")
        sys.exit(EC.PLATFORM_NOT_SUPPORTED.value)
