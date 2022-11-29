import bpy

class SCG_Cycler_Context_Interface:
    @property
    def cycler(self):
        return bpy.context.scene.scg_cycler_context