import os
import toml
from pathlib import Path
from typing import Dict, Set, List, Optional, Union, Any
from install_utils import executable_exists, run_process, PLATFORM


class InstallConfig:
    """Creates and validates config for further use. Check the **install_config.toml**
    for comments and details on implementation along with default values.
    """

    blender_packed: Optional[Path]
    blender_unpack: bool
    blender_overwrite: bool
    blender_path: Path
    blender_python_dir: Path
    blender_python_version: str
    blender_version: str
    addon_path_autodetect: bool
    addon_path_user: bool
    addon_name: str
    addon_path: Path
    addon_create_link: bool
    addon_allowed_paths: Set[Path]
    use_ignore: bool
    use_include: bool

    binaries_precompiled_path: Path
    binaries_path: Path
    binaries_checksum: bool
    binaries_copy: bool
    binaries_compile: bool

    current_folder: Path
    install_pip_script: Optional[Path]
    pip_modules: Optional[str]
    install_activate_script: Optional[Path]
    activate_addons: List[str]
    install_custom_script: Optional[Path]
    install_custom_timeout: float
    install_custom_args: List[str]

    install_include: Optional[Path]
    install_exclude: Optional[Path]

    def __init__(self, cfg_file: Path):
        cfg: Dict[str, Any] = toml.load(cfg_file)
        self.validate_config(cfg)

    def validate_config(self, cfg: Dict[str, Any]):
        """Extracts and validates values from cfg file. Falls back to sane defaults."""
        self.addon_name = cfg.get("blender_install", "blender_install")
        self.addon_path_autodetect = cfg.get("addon_path_autodetect", True)
        self.addon_path_user = cfg.get("addon_path_user", True)
        self.addon_allowed_paths = set(cfg.get("addon_allowed_paths", []))
        self.current_folder = Path(os.getcwd()).resolve(True)
        self.blender_unpack = cfg.get("blender_unpack", True)
        self.blender_packed = cfg.get("blender_packed")
        self.blender_overwrite = cfg.get("blender_overwrite", True)

        self.blender_path = self.get_blender_path(cfg)
        self.binaries_precompiled_path = self.get_binaries_precompiled_path(cfg)
        self.binaries_path = self.get_binaries_path(cfg)

        if not executable_exists(self.blender_path):
            if self.blender_unpack:
                if self.blender_packed is not None:
                    blender_packed = self.resolve_to_path(self.blender_packed)

                    if blender_packed.exists() and blender_packed.is_file():
                        self.blender_packed = blender_packed

                        print(
                            "blender_path is not found, but portable archive is found"
                        )

            else:
                raise OSError("Provided blender_path is not found or not executable")

        self.blender_version = self.get_blender_version(self.blender_path)
        self.blender_python_dir = self.get_blender_python_dir()
        self.blender_python_version = self.get_blender_python_version()
        self.addon_path = self.get_addon_path(cfg)

        # These fields do not require specific methods (yet)
        self.addon_create_link = cfg.get("addon_create_link", True)
        self.use_ignore = cfg.get("use_ignore", True)
        self.use_include = cfg.get("use_include", True)
        self.binaries_copy = cfg.get("binaries_copy", False)
        self.binaries_compile = cfg.get("binaries_compile", False)

        # Get custom scripts for installation of additional components
        install_pip_script = cfg.get("install_pip_script")
        self.pip_modules = cfg.get("pip_modules", [])
        install_activate_script = cfg.get("install_activate_script")
        self.activate_addons = cfg.get("activate_addons", [])
        install_custom_script = cfg.get("install_custom_script")
        self.install_custom_timeout = cfg.get("install_custom_script", 30.0)
        self.install_custom_args = cfg.get("install_custom_args", [])

        # No script provided == step skipped
        for field, script_name in {
            "install_pip_script": install_pip_script,
            "install_activate_script": install_activate_script,
            "install_custom_script": install_custom_script,
        }.items():
            if script_name is not None:
                setattr(self, field, self.get_script_file(cfg, script_name))
            else:
                setattr(self, field, None)

        self.install_include = cfg.get("install_include")
        self.install_exclude = cfg.get("install_exclude")

        if self.install_include is not None:
            self.install_include = Path(self.install_include).resolve(True)

        if self.install_exclude is not None:
            self.install_exclude = Path(self.install_exclude).resolve(True)

    def get_blender_path(self, cfg: Dict[str, Any]) -> Path:
        return Path(
            cfg.get(
                "blender_path",
                Path(
                    Path(__file__).resolve(True),
                    "..",
                    "blender_portable",
                    "blender",
                ),
            )
        ).resolve(True)

    def get_binaries_precompiled_path(self, cfg: Dict[str, Any]) -> Path:
        return Path(
            cfg.get(
                "binaries_precompiled_path",
                Path(Path(__file__).resolve(True), "..", "binaries"),
            ),
        )

    def get_binaries_path(self, cfg: Dict[str, Any]) -> Path:
        return Path(
            cfg.get(
                "binaries_path",
                Path(Path(__file__).resolve(True), "bin"),
            )
        ).resolve(True)

    def get_addon_path(self, cfg: Dict[str, Any]) -> Path:
        default_path: Path
        if PLATFORM in {"Linux", "Darwin"}:
            if self.addon_path_user:
                default_path = Path(
                    Path.home(),
                    ".config",
                    "blender",
                    self.blender_version,
                    "scripts",
                    "addons",
                    self.addon_name,
                )
            else:
                default_path = Path(
                    self.blender_path,
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
                raise Exception(f"Failed to get Blender version: {ec}\n{se}\n{er}")
        else:
            raise Exception(f"Failed to get Blender version: {ec}\n{se}\n{er}")

        # Get "Blender x.x.x" and then convert to "x.x" (major version)
        ver = so[1].split("\n\t")[1].split()[1].split(".")[0:2]
        return ".".join(ver)

    def get_script_file(self, cfg: Dict[str, Any], script_name: str) -> Optional[Path]:
        """Checks that custom install Python script is provided.

        Parameters:
        -----------
        cfg : Dict[str, Any]
            Parsed toml file.
        script_name : str
            Name of the custom file.
        """
        script_file = cfg.get(script_name)

        if script_file is not None:
            script_file = Path(script_file)

            if script_file.is_file():
                return script_file
            elif script_file.is_absolute():
                return script_file
            else:
                # check that just the name of script is provided, so the abspath
                # will include current path
                script_file = Path(self.current_folder, script_file).resolve(True)

                if script_file.exists() and script_file.is_file():
                    return script_file
                else:
                    print(f"User provided {script_name}, but no script file found")

        return None

    def get_blender_python_dir(self) -> Path:
        """Finds the python root dir for blender.

        Returns:
        --------
        Path
            Path to the root of Python directory.
        """
        # Get the blender version if the executable run failed, so return statement
        # is valid, otherwise raise Exception, as it's impossible to work with
        # non-portable release
        if self.blender_version is None:
            files = os.listdir(str(self.blender_path.parent))
            py_found = False

            for file in files:
                if all(
                    (
                        file[0].isdigit(),
                        file[-1].isdigit(),
                        len(file) > 1,
                        os.path.isdir(
                            os.path.join(str(self.blender_path.parent), file)
                        ),
                    )
                ):
                    self.blender_version = file
                    py_found = True
                    break

            if not py_found:
                raise Exception("Blender Python root directory is not found")

        return Path(self.blender_path.parent, self.blender_version, "python").resolve(
            True
        )

    def get_blender_python_version(self) -> str:
        """Using blender python dir find the python version.

        Returns:
        --------
        str
            Blender Python version.
        """
        python_bin_path = Path(self.blender_python_dir, "bin")

        files = os.listdir(str(python_bin_path))
        ver_found = False
        ver = ""

        for file in files:
            if file.startswith("python"):
                ver_found = True
                ver = file.removeprefix("python")

        if not ver_found:
            raise Exception("Python version is not found")

        return ver
