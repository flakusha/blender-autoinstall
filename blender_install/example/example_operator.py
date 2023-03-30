from bpy.types import Operator, Context


class ExampleOperator(Operator):
    """Register script example."""

    bl_idname = "bl_install.example_operator"
    bl_label = "Example Operator"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        print("Example Operator is run!")
        return {"FINISHED"}
