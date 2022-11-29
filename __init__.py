bl_info = {
    "name" : "Cycler",
    "author" : "Summoner's Circle Games",
    "description" : "Automatically mirror along keyframes and animation time",
    "version" : (1, 0, 2),
    "blender" : (3, 1, 0),
    "category" : "Animation"
}

import bpy
from . import context, frame_markers, controls, channel, keyframes, bone
from .auto_update import func as auto_update_func

###############################
#   Register and Unregister   #
###############################
modules = (bone, frame_markers, keyframes, channel, controls, context)

@bpy.app.handlers.persistent
def initialise_panels(self):
    bpy.context.scene.scg_cycler_context.update_ui()
    if bpy.context.scene.scg_cycler_context.auto_update:
        bpy.app.timers.register(auto_update_func)

def register():
    for m in modules:
        m.register()
    bpy.app.handlers.load_post.append(initialise_panels)

def unregister():
    for m in reversed(modules):
        m.unregister()
    bpy.app.handlers.load_post.remove(initialise_panels)