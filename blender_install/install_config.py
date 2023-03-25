import toml
import platform
from collections.abc import MutableMapping
from pathlib import Path
from typing import Dict, Optional, Union, List, Any
from install_utils import executable_exists, run_process

PLATFORM = platform.system()


class InstallConfig:
    """Creates and validates config for further use. Check the **install_config.toml**
    for comments and details on implementation along with default values.
    """

    blender_path: Path
    blender_version: str
    addon_path_autodetect: bool
    addon_name: str
    addon_path: Path
    addon_create_link: bool
    use_ignore: bool
    use_include: bool
    activate_addons: List[str]
    binaries_checksum: bool
    binaries_copy: bool
    binaries_compile: bool

    def __init__(self, cfg_file: Path):
        cfg: Dict[str, Any] = toml.load(cfg_file)
        self.validate_config(cfg)

    def validate_config(self, cfg: Dict[str, Any]):
        """Extracts and validates values from cfg file. Falls back to sane defaults."""
        self.addon_name = cfg.get("blender_install", "blender_install")
        self.addon_path_autodetect = cfg.get("addon_path_autodetect", True)

        self.blender_path = Path(
            cfg.get(
                "blender_path",
                Path(
                    Path(__file__).resolve(True),
                    "..",
                    "..",
                    "blender_portable",
                    "blender",
                ).resolve(True),
            )
        ).resolve(True)

        if not executable_exists(self.blender_path):
            raise OSError("Provided blender_path doesn't exist or is not executable")

        self.blender_version = self.get_blender_version(self.blender_path)
        self.addon_path = self.get_addon_path(cfg)

        # These fields do not require specific methods (yet)
        self.addon_create_link = cfg.get("addon_create_link", True)
        self.use_ignore = cfg.get("use_ignore", True)
        self.use_include = cfg.get("use_include", True)
        self.activate_addons = cfg.get("activate_addons", [])
        self.binaries_copy = cfg.get("binaries_copy", False)
        self.binaries_compile = cfg.get("binaries_compile", False)

    def get_addon_path(self, cfg: Dict[str, Any]) -> Path:
        default_path: Path
        if PLATFORM in {"Linux", "Darwin"}:
            default_path = Path(
                Path.home(),
                ".config",
                "blender",
                self.blender_version,
                "scripts",
                "addons",
                self.addon_name,
            )
        elif PLATFORM == "Windows":
            default_path = Path(
                Path.home(),
                "AppData",
                "Roaming",
                "Blender Foundation",
                "Blender",
                self.blender_version,
                "scripts",
                "addons",
                self.addon_name,
            )
        else:
            raise Exception(f"Platform: {PLATFORM} is not supported")

        # Detect addon path automatically if nothing is set
        if self.addon_path_autodetect:
            return self.resolve_to_path(default_path)
        else:
            return self.resolve_to_path(cfg.get("addon_path", default_path))

    def resolve_to_path(self, path: Union[str, Path]) -> Path:
        if isinstance(path, str):
            if path.startswith("~/"):
                return Path(Path.home(), path[2::]).resolve(True)
            else:
                return Path(path).resolve(True)
        else:
            return path.resolve(True)

    def get_blender_version(self, path: Path) -> str:
        """Runs provided Blender executable and gets version."""
        ec, so, se, er = run_process(
            [str(self.blender_path), "--version"], "Failed to get Blender version", 2
        )

        if ec is not None:
            if ec != 0:
                raise Exception(f"{ec}")
        else:
            raise Exception(f"{ec}")

        # Get "Blender x.x.x" and then convert to "x.x" (major version)
        ver = so[1].split("\n\t")[1].split()[1].split(".")[0:2]
        return ".".join(ver)
