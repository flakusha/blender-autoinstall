import os
import sys
from bpy.utils import register_class, unregister_class
from typing import Tuple, Any

# Register possibility to import files from addon space
# Blender doesn't correctly import modules without it.
# You can see similar initialization in many other addons
# this one tends to be the shortest.
dir_cur = os.path.dirname(__file__)
if dir_cur not in sys.path:
    sys.path.append(dir_cur)

from example.example_operator import ExampleOperator

bl_info = {
    "name": "Blender Install",
    "category": "Object",
    "description": "Installation template for Blender3D plugins",
    "author": "Konstantin Fedotov <zenflak@gmail.com>",
    "version": (0, 1, 0),
    "blender": (3, 3, 0),
    "location": "Everywhere",
    "warning": "",
    "doc_url": "",
    "tracker_url": "https://github.com/flakusha/blender-autoinstall/issues",
    "support": "COMMUNITY",
}

# Add the field of bl_info to get access in any part of project
__version__ = bl_info["version"]
addon_path = __path__
addon_name = __name__


addon_classes: Tuple[Any] = (ExampleOperator,)


def register():
    for cls in addon_classes:
        register_class(cls)


def unregister():
    for cls in addon_classes:
        unregister_class(cls)
