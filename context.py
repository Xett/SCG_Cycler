import bpy

from .interfaces import SCG_Cycler_Context_Interface
from .work import work_tick
from .rig_actions import SCG_Cycler_Rig_Actions
from .bone import SCG_Cycler_Rig_Bone_Whitelists

###############
#   Context   #
###############

# Root property inside of the context scene, to hold all our plugin data.
# There is an interface to access this as self.cycler
class SCG_Cycler_Context(bpy.types.PropertyGroup):
    rig_actions : bpy.props.PointerProperty(type=SCG_Cycler_Rig_Actions)    
    auto_update : bpy.props.BoolProperty()
    rig_bone_whitelists : bpy.props.PointerProperty(type=SCG_Cycler_Rig_Bone_Whitelists)

    @property
    def rig_action(self):
        return self.rig_actions.rig_action

    @property
    def action(self):
        if self.rig_action is None:
            return None
        return self.rig_action.action

    @property
    def armature(self):
        if self.rig_action is None:
            return None
        return self.rig_action.armature

    @property
    def timings(self):
        if self.rig_action is None:
            return None
        return self.rig_action.timings

    @property
    def rig_bones(self):
        if self.rig_action is None:
            return None
        return self.rig_action.rig_bones

    def update_ui(self):
        self.rig_actions.update_ui()

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
        self.layout.row().operator("scg_cycler.add_rig_action")
        self.layout.row().prop_search(self.cycler.rig_actions, "current_rig_action_name", self.cycler.rig_actions, "rig_actions")
        if not self.cycler.rig_action is None:
            row = self.layout.row()
            row.prop(self.cycler.rig_action, "action")
        if not self.cycler.rig_action is None:
            row = self.layout.row()
            row.prop(self.cycler.rig_action, "armature")

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