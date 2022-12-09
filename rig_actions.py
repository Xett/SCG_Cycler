import bpy

from .interfaces import SCG_Cycler_Context_Interface as Context_Interface
from .controls import SCG_Cycler_Controls
from .bone import SCG_Cycler_Rig_Bones
from .timings import SCG_Cycler_Timing

class SCG_Cycler_Rig_Action(bpy.types.PropertyGroup, Context_Interface):
    name : bpy.props.StringProperty(name="Name")
    def action_update(self, context):
        self.name = "{0}:{1}".format(self.action.name if not self.action is None else "", self.armature.name if not self.armature is None else "")
        self.cycler.rig_actions.current_rig_action_name = self.name

    action : bpy.props.PointerProperty(type=bpy.types.Action, name="Action", update=action_update)
    
    # When the armature is changed, we need to update the valid armature bones
    def armature_changed_update(self, context):
        self.rig_bones.armature_changed()    
        self.name = "{0}:{1}".format(self.action.name if not self.action is None else "", self.armature.name if not self.armature is None else "")  
        self.cycler.rig_actions.current_rig_action_name = self.name  
    armature : bpy.props.PointerProperty(type=bpy.types.Armature, name="Armature", update=armature_changed_update)

    controls : bpy.props.PointerProperty(type=SCG_Cycler_Controls)
    timings : bpy.props.PointerProperty(type=SCG_Cycler_Timing)
    rig_bones : bpy.props.PointerProperty(type=SCG_Cycler_Rig_Bones)

class SCG_Cycler_Rig_Actions(bpy.types.PropertyGroup):
    def current_rig_action_name_changed(self, context):
        for index, rig_action in enumerate(self.rig_actions):
            if self.current_rig_action_name == rig_action.name:
                self.current_rig_action = index
    current_rig_action : bpy.props.IntProperty()
    current_rig_action_name : bpy.props.StringProperty(name="Rig Action", update=current_rig_action_name_changed)
    rig_actions : bpy.props.CollectionProperty(type=SCG_Cycler_Rig_Action)

    @property
    def rig_action(self):
        if len(self.rig_actions) == 0 or self.current_rig_action > len(self.rig_actions)-1:
            return None
        return self.rig_actions[self.current_rig_action]
    
    def update_ui(self):
        if not self.rig_action is None:
            # Remove invalid panels
            self.rig_action.controls.remove_panels()
            # Add missing panels
            self.rig_action.controls.add_panels()

#################
#   Operators   #
#################
class SCG_CYCLER_OT_Add_Rig_Action(bpy.types.Operator, Context_Interface):
    bl_idname = "scg_cycler.add_rig_action"
    bl_label = "Add Rig Action"
    bl_description = "Add Rig Action"

    def execute(self, context):
        self.cycler.rig_actions.rig_actions.add()
        return {"FINISHED"}

class SCG_CYCLER_OT_Remove_Rig_Action(bpy.types.Operator, Context_Interface):
    bl_idname = "scg_cycler.remove_rig_action"
    bl_label = "Remove Rig Action"
    bl_description = "Remove Rig Action"

    index : bpy.props.IntProperty()

    def execute(self, context):
        self.cycler.rig_actions.rig_actions.remove(self.index)
        return {"FINISHED"}

###############################
#   Register and Unregister   #
###############################
classes = (SCG_Cycler_Rig_Action, SCG_Cycler_Rig_Actions, SCG_CYCLER_OT_Add_Rig_Action, SCG_CYCLER_OT_Remove_Rig_Action)

def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)
    
def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)