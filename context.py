import bpy

from .interfaces import SCG_Cycler_Context_Interface
from .work import work_tick
from .controls import SCG_Cycler_Controls
from .bone import SCG_Cycler_Bone_Reference
from .timings import SCG_Cycler_Timing

###############
#   Context   #
###############

# Root property inside of the context scene, to hold all our plugin data.
# There is an interface to access this as self.cycler
class SCG_Cycler_Context(bpy.types.PropertyGroup):
    action : bpy.props.PointerProperty(type=bpy.types.Action, name="Action")
    
    # When the armature is changed, we need to update the valid armature bones
    def armature_changed_update(self, context):
        self.update_valid_armature_bones()
        
    armature : bpy.props.PointerProperty(type=bpy.types.Armature, name="Armature", update=armature_changed_update)

    def update_valid_armature_bones(self):
        # Clear the valid armature bones, cause its easier than adding valid ones not there, and removing invalid ones
        self.valid_armature_bones.clear()
        # If there is no armature, then we have no valid armature bones
        if not self.armature:
            return
        for bone in self.armature.bones:
            # Valid bones are mostly found by name, there are still a bunch missing, it would be prefarable to have some kind of whitelist for bones in a rig
            if "ORG" not in bone.name and "DEF" not in bone.name and "MCH" not in bone.name and "_master" not in bone.name and "VIS" not in bone.name and "_target" not in bone.name and bone.name not in [control.bone_name for control in self.controls]:
                # Make a new bone, and set its name
                new_bone = self.valid_armature_bones.add()
                new_bone.name = bone.name
    valid_armature_bones : bpy.props.CollectionProperty(type=SCG_Cycler_Bone_Reference)
    
    controls : bpy.props.PointerProperty(type=SCG_Cycler_Controls)
    auto_update : bpy.props.BoolProperty()
    timings : bpy.props.PointerProperty(type=SCG_Cycler_Timing)
    
    def update_ui(self):
        # Remove invalid panels
        self.controls.remove_panels()
        # Add missing panels
        self.controls.add_panels()

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
            bpy.app.timers.register(work_tick)
        else:
            bpy.app.timers.unregister(work_tick)
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