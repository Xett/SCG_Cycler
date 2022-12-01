import bpy

from .interfaces import SCG_Cycler_Context_Interface as Context_Interface
from .frame_markers import SCG_Cycler_Frame_Markers
from .constants import FPS_MODES, FPS_MODES_ENUM

###############
#   Timings   #
###############
class SCG_Cycler_Timing(bpy.types.PropertyGroup, Context_Interface):

    def update_timings(self, context):
        old_fps_mode = bpy.context.scene.render.fps
        new_fps_mode = int(self.fps_mode)
        fps_changed = old_fps_mode != new_fps_mode

        old_animation_length = bpy.context.scene.frame_end / old_fps_mode
        new_animation_length = self.animation_length * new_fps_mode
        animation_length_changed = old_animation_length != new_animation_length

        if fps_changed:
            bpy.context.scene.render.fps = new_fps_mode

        if fps_changed or animation_length_changed:
            bpy.context.scene.frame_start = 0
            bpy.context.scene.frame_end = self.animation_length * new_fps_mode
            self.frame_markers.update_fcurves(old_animation_length, old_fps_mode)

    frame_markers : bpy.props.PointerProperty(type=SCG_Cycler_Frame_Markers)

    fps_mode : bpy.props.EnumProperty(items=FPS_MODES_ENUM, name="FPS Mode", update=update_timings)
    animation_length : bpy.props.FloatProperty(name="Animation Length", update=update_timings, unit="TIME", subtype="TIME")

######################
#   User Interface   #
######################
class SCG_CYCLER_PT_Timings_Panel(bpy.types.Panel, Context_Interface):
    bl_idname = "SCG_CYCLER_PT_Timings_Panel"
    bl_label = "Timings"
    bl_category = "SCG Cycler"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        row = self.layout.row()
        row.prop(self.cycler.timings, "fps_mode")
        row = self.layout.row()
        row.prop(self.cycler.timings, "animation_length")


###############################
#   Register and Unregister   #
###############################
classes = (SCG_Cycler_Timing, SCG_CYCLER_PT_Timings_Panel)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    
def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)