import bpy
import json

from .interfaces import SCG_Cycler_Context_Interface as Context_Interface
from .frame_markers import SCG_Cycler_Frame_Markers
from .constants import FPS_MODES, FPS_MODES_ENUM
from .work import WorkQueue, FPSChangedJob, AnimationLengthChangedJob

###############
#   Timings   #
###############
class SCG_Cycler_Timing(bpy.types.PropertyGroup, Context_Interface):

    def update_fps(self, context):
        job = FPSChangedJob(self.animation_length, bpy.context.scene.render.fps, int(self.fps_mode))
        WorkQueue().add(job)
    fps_mode : bpy.props.EnumProperty(items=FPS_MODES_ENUM, name="FPS Mode", update=update_fps)
    
    def update_animation_length(self, context):
        job = AnimationLengthChangedJob(bpy.context.scene.frame_end/bpy.context.scene.render.fps, self.animation_length, bpy.context.scene.render.fps)
        WorkQueue().add(job)
    animation_length : bpy.props.FloatProperty(name="Animation Length", update=update_animation_length, unit="TIME", subtype="TIME")
    
    frame_markers : bpy.props.PointerProperty(type=SCG_Cycler_Frame_Markers)

    @property
    def json_data(self):
        return {"fps_mode":self.fps_mode, "animation_length":self.animation_length, "frame_markers":self.frame_markers.json_data}
    def load_from_json_data(self, json_data):
        self.fps_mode = json_data["fps_mode"]
        self.animation_length = json_data["animation_length"]
        self.frame_markers.load_from_json_data(json_data["frame_markers"])

######################
#   User Interface   #
######################
class SCG_CYCLER_PT_Timings_Panel(bpy.types.Panel, Context_Interface):
    bl_idname = "SCG_CYCLER_PT_Timings_Panel"
    bl_label = "Timings"
    bl_category = "SCG Cycler"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    @classmethod
    def poll(cls, context):
        return bpy.context.scene.scg_cycler_context.rig_action

    def draw(self, context):
        row = self.layout.row()
        row.prop(self.cycler.rig_action.timings, "fps_mode")
        row = self.layout.row()
        row.prop(self.cycler.rig_action.timings, "animation_length")
        row = self.layout.row()
        box = row.box()
        row = box.row()
        row.operator("scg_cycler.add_frame_marker")
        for index, frame_marker in enumerate(self.cycler.rig_action.timings.frame_markers):
            row = box.row()
            row.prop(frame_marker, "name")
            col = row.column()
            col.prop(frame_marker, "length")
            col = row.column()
            col.label(text="Frame: {0}".format(frame_marker.frame))
            col = row.column()
            remove_op=col.operator("scg_cycler.remove_frame_marker")
            remove_op.index = index


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