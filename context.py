import bpy

from .interfaces import SCG_Cycler_Context_Interface
from .auto_update import func as auto_update_func
from .frame_markers import SCG_Cycler_Frame_Markers
from .controls import SCG_Cycler_Controls
from .bone import SCG_Cycler_Bone_Reference

###############
#   Context   #
###############
class SCG_Cycler_Context(bpy.types.PropertyGroup):
    def get_num_animated_frames(self):
        return bpy.context.scene.frame_end
    def set_num_animated_frames(self, value):
        bpy.context.scene.frame_start = 1
        bpy.context.scene.frame_end = value
    action : bpy.props.PointerProperty(type=bpy.types.Action, name="Action")
    
    def on_armature_changed(self, context):
        self.valid_armature_bones.clear()
        if not self.armature:
            return
        for bone in self.armature.bones:
            if "ORG" not in bone.name and "DEF" not in bone.name and "MCH" not in bone.name and "_master" not in bone.name and "VIS" not in bone.name and "_target" not in bone.name and bone.name not in [control.bone_name for control in self.controls]:
                new_bone = self.valid_armature_bones.add()
                new_bone.name = bone.name

    def update_valid_armature_bones(self, context):
        self.on_armature_changed(context)
    armature : bpy.props.PointerProperty(type=bpy.types.Armature, name="Armature", update=on_armature_changed)
    valid_armature_bones : bpy.props.CollectionProperty(type=SCG_Cycler_Bone_Reference)

    frame_markers : bpy.props.PointerProperty(type=SCG_Cycler_Frame_Markers)
    num_animated_frames : bpy.props.IntProperty(name="Number of frames", set=set_num_animated_frames, get=get_num_animated_frames)
    controls : bpy.props.PointerProperty(type=SCG_Cycler_Controls)
    auto_update : bpy.props.BoolProperty()
    
    def update_ui(self):
        self.controls.remove_panels()
        self.controls.add_panels()

    def update(self):
        self.controls.update()

    @property
    def half_point(self):
        return round(self.num_animated_frames//2)+1

#################
#   Operators   #
#################
class SCG_CYCLER_OT_Toggle_Auto_Update(bpy.types.Operator, SCG_Cycler_Context_Interface):
    bl_idname = "scg_cycler.toggle_auto_update"
    bl_label = "Update"
    bl_description = "Toggle Auto Update"

    def execute(self, context):
        self.cycler.auto_update = not self.cycler.auto_update
        if self.cycler.auto_update:
            bpy.app.timers.register(auto_update_func)
        else:
            bpy.app.timers.unregister(auto_update_func)
        return {"FINISHED"}

######################
#   User Interface   #
######################
class SCG_CYCLER_PT_Context_Panel(bpy.types.Panel, SCG_Cycler_Context_Interface):
    bl_idname = "SCG_CYCLER_PT_Context_Panel"
    bl_label = "Context"
    bl_category = "SCG Cycler"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        row = self.layout.row()
        row.prop(self.cycler, "action")
        row = self.layout.row()
        row.prop(self.cycler, "armature")
        row = self.layout.row()
        row.prop(self.cycler, "num_animated_frames")

        row = self.layout.row()
        label = "Enabled" if self.cycler.auto_update else "Disabled"
        row.label(text="Auto Update is currently "+label)
        col = row.column()
        button_label = "Disable" if self.cycler.auto_update else "Enable"
        col.operator("scg_cycler.toggle_auto_update", text=button_label)

###############################
#   Register and Unregister   #
###############################
classes = (SCG_Cycler_Context, SCG_CYCLER_OT_Toggle_Auto_Update, SCG_CYCLER_PT_Context_Panel)

def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)
        
    bpy.types.Scene.scg_cycler_context = bpy.props.PointerProperty(type=SCG_Cycler_Context)
    
def unregister():
    from bpy.utils import unregister_class

    del bpy.types.Scene.scg_cycler_context
    for cls in reversed(classes):
        unregister_class(cls)