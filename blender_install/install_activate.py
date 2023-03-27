import os
import sys
import bpy
import addon_utils
from typing import List

# Make it possible to import modules
dircur = os.path.dirname(__file__)
if dircur not in sys.path:
    sys.path.append(os.path.dirname(__file__))

from install_utils import run_process

python_dir = "python{}.{}".format(sys.version_info.major, sys.version_info.minor)


def activate_addons(addons: List[str]):
    """Tries to activate all selected addons and saves user configuration.

    Parameters:
    -----------
    addons : List[str]
        Names of addons.
    """
    for a in addons:
        try_activate(a, True)

    bpy.ops.wm.save_userpref()


def try_activate(addon: str, activate: bool):
    """Activates or deactivates addon. Prints message in case of failure.

    Parameters:
    -----------
    addon : str
        Name of the addon.
    activate : bool
        Activate addon.
    """
    try:
        if activate:
            addon_utils.enable(
                addon,
                default_set=activate,
                persistent=True,
                handle_error=None,
            )
        else:
            addon_utils.disable(
                addon,
                default_set=activate,
                handle_error=None,
            )

    except Exception as e:
        if activate:
            print(f"Could not activate: {addon}: {e}")
        else:
            print(f"Could not deactivate: {addon}: {e}")


def setup_compute_devices():
    """
    If system has compatible GPU, setup this GPU support.
    Selects the most performant option out of the list.
    """
    # Update devices first, sometimes the list is incorrect/ empty
    context = bpy.context
    cycles_pref = context.preferences.addons["cycles"].preferences
    # Blender detects devices itself, it's needed to pick the most
    # performant option out of all, just calculate number of devices
    dev_info = {}

    for dev_type in cycles_pref.get_device_types(context):
        dev_info[dev_type[0]] = 0

    for dev_type in dev_info.keys():
        cycles_pref.compute_device = dev_type
        devs = cycles_pref.get_devices_for_type(dev_type)
        if devs is not None:
            dev_info[dev_type] += len(devs)

    print("Detected compute devices:")
    print(dev_info)
    no_devices_found = True

    for k, v in dev_info.items():
        if v > 0:
            no_devices_found = False
            break

    if no_devices_found:
        print("No GPUs found, skipping further setup")
        return

    # In case CUDA devices selected and OptiX is available
    # prefer OptiX, other devices are automatially set to
    # compatible framework, in other cases it should pick the right one,
    # e.g. ONEAPI (Intel) or HIP (AMD)
    dev_priority = "NONE"
    dev_max = 0

    for k, v in dev_info.items():
        if v > dev_max:
            dev_max = v
            dev_priority = k

    if dev_priority == "CUDA":
        if "OPTIX" in dev_info.keys():
            dev_priority = "OPTIX"
        else:
            dev_priority = "CUDA"
    elif dev_priority == "CPU":
        dev_priority = "NONE"

    # Don't change anything if device is already set
    print(f"Setting compute device: {dev_priority}")
    # Don't set up anything if only CPU is available
    # Blender picks CPU as default device anyway
    if dev_priority == "NONE":
        print("Only CPU is available, no compute devices will be configured")
        bpy.ops.wm.save_userpref()
        return

    if cycles_pref.compute_device_type != dev_priority:
        cycles_pref.compute_device_type = dev_priority

    print("Activating all available compatible devices")
    for d in cycles_pref.get_devices_for_type(dev_priority):
        try:
            if d.type == dev_priority or d.type == "CPU":
                d.use = True
        except Exception as e:
            print(f"Could not activate compute device: {d.type}: {d.name}")

    # Report about successful activation, update the variable
    cycles_pref = bpy.context.preferences.addons["cycles"].preferences
    devs = [d for d in cycles_pref.devices]
    print("Compute devices activation result:")
    [print(f"{str(d.use):5}: {d.type:10}: {d.name}") for d in devs]

    bpy.ops.wm.save_userpref()


if __name__ == "__main__":
    setup_compute_devices()

    argv = sys.argv

    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        # No additional arguments provided, exiting without error
        sys.exit()

    # Extract comma-separated addon names
    if len(argv) > 0:
        if "-a" in argv:
            idxm = argv.index("-a")
            addons: List[str] = argv[argv.index("-a") + 1].split(",")
            addons = [a.strip() for a in addons]

    if len(addons) > 0:
        activate_addons(addons)

    print("Finished addon configuration")
