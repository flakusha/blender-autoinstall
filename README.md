# blender-autoinstall
Blender autoinstallation utility.

The main purpose of this set of scripts is to provide unified automated experience to install and configure Blender
addon with dependencies in form of another addons and PIP libraries.

This script can be used to be run in headless environment to aid in cases where Blender is used as 3D content
tool.

## Requirements
1. Make sure `Python >= 3.8` is installed in your system, if it is not - it's still possible to use Python bundled with
portable Blender installation if it's unpacked prior to using this script set.
2. If you are going to checksum binary files, make sure:
  - checksum files are placed along them in format `<full_name.with.extension.CHEKSUM_ALG>`, e.g.
  `blender.tar.xz` <-> `blender.tar.xz.sha512`
  - `certutil` is available on Windows
  - `md5sum` and `shasum` are available on Linux
3. Provide Blender portable archive in `binaries` folder in compatible format: `*.tar.*` and `*.zip` if it's not
already unpacked to the `blender_portable` folder.

Other than that - only standard Python library is used, so you should be good to go.

## How to use
- Visit `install_config.toml` file and make adjsustments needed for your script to work in your environment.
- Provide source code for your addon. Begin integration using `__init__.py` and grow your ecosystem with use of
libraries that are provided by Pypi or binaries that can be integrated and called with Python.
- Run `python install.py -c install_config.toml` every time you need to copy and overwrite addon, make changes to
external dependencies or other major changes. If script suceeds in making a link to your addon folder, your changes
will be automatically loaded after you restart Blender.

## Important notes
- Avoid installing conflicting versions of PIP packages to Blender Python environment
- Tested on ArchLinux, should work fine on other Linux redistributions
- Docker scripts comming soon
