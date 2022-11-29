import bpy

def func():
    cycler = bpy.context.scene.scg_cycler_context
    if not cycler.action:
        return 1
    cycler.update()
    return 1