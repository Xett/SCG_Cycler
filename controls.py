import bpy

from .interfaces import SCG_Cycler_Context_Interface as Context_Interface
from .panel import Panel_Factory, Children_Have_Panels
from .channel import SCG_Cycler_Control_Channels
from .constants import *

################
#   Control   #
################
class SCG_Cycler_Control(bpy.types.PropertyGroup, Context_Interface, Children_Have_Panels):    
    def control_bone_get(self):
        if "bone_name" not in self:
            return ""
        return self["bone_name"]
    def control_bone_set(self, value):
        if "ORG" in value: return
        elif "DEF" in value: return
        elif "MCH" in value: return
        elif "f_" == value[:2]: return
        elif "_master" in value: return
        elif value in [control.bone_name for control in self.cycler.rig_action.controls if self.bone_name != value]: return
        self["bone_name"] = value
    def control_bone_update(self, context):
        for channel in self:
            channel.parent_name = self.bone_name
        self.cycler.rig_action.controls.remove_panels()
        self.cycler.rig_action.controls.add_panels()
        #self.cycler.update_valid_armature_bones()

    bone_name : bpy.props.StringProperty(name="Bone", update=control_bone_update, set=control_bone_set, get=control_bone_get)
    channels : bpy.props.PointerProperty(type=SCG_Cycler_Control_Channels)
    mirrored : bpy.props.BoolProperty(name="Use mirror control")

    def __iter__(self):
        return self.channels.__iter__()

    def __len__(self):
        return len(self.channels)

    def add(self, type, axis):
        return self.channels.add(type.upper(), axis.upper(), self.bone_name)
    
    def remove(self, type, axis):
        self.channels.remove(type.upper(), axis.upper())

    def get(self, type, axis):
        return self.channels.get(type.upper(), axis.upper())

    @property
    def mirrors(self):
        return ".L" in self.bone_name or ".R" in self.bone_name or "_l" in self.bone_name or "_r" in self.bone_name

    @property
    def mirror_name(self):
        if ".L" in self.bone_name:
            return self.bone_name.replace(".L", ".R")
        elif ".R" in self.bone_name:
            return self.bone_name.replace(".R", ".L")
        return self.bone_name

    @property
    def data_path(self):
        return "pose.bones[\"{0}\"]".format(self.bone_name)

    @property
    def panel_ids(self):
        return [(channel.type, channel.axis) for channel in self]

    def create_panel_class(self, **kwargs):
        if len(kwargs)==0: return
        if "channel_type" not in kwargs or "channel_axis" not in kwargs: return
        new_channel_type = kwargs["channel_type"]
        new_channel_axis = kwargs["channel_axis"]

        label = ""
        for index, word in enumerate((new_channel_type+"_"+new_channel_axis).split("_")):
            label += word[0].upper() + word[1:].lower()
            label += " "
        id_name = "SCG_CYCLER_PT_{0}_{1}_{2}_Channel_Panel".format(self.bone_name.upper().replace(".", "_").replace("-", "_"), new_channel_type.upper(), new_channel_axis.upper())
        parent_id = "SCG_CYCLER_PT_{0}_Control_Panel".format(self.bone_name.upper().replace(".", "_").replace("-", "_"))
        class ChannelPanel(bpy.types.Panel, Context_Interface):
            bl_idname = id_name
            bl_label = label
            bl_category = "SCG Cycler"
            bl_space_type = "VIEW_3D"
            bl_region_type = "UI"
            bl_parent_id = parent_id
            bl_options = {"DEFAULT_CLOSED"}

            bone_name = self.bone_name
            channel_type = new_channel_type
            channel_axis = new_channel_axis

            @property
            def control(self):
                return self.cycler.rig_action.controls.get(self.bone_name)

            @property
            def channel(self):
                return self.control.get(self.channel_type, self.channel_axis)

            def draw(self, context):
                row = self.layout.row()
                if len(self.cycler.timings.frame_markers) > len(self.channel):
                    add_operator = row.operator("scg_cycler.add_channel_keyframe")
                    add_operator.bone_name = self.bone_name
                    add_operator.channel_type = self.channel_type
                    add_operator.channel_axis = self.channel_axis
                for index, keyframe in enumerate(self.channel):
                    row = self.layout.row()
                    row.prop(keyframe, "marker")
                    col = row.column()
                    col.prop(keyframe, "offset")
                    if not self.control.mirrored:
                        col = row.column()
                        col.prop(keyframe, "inverted")
                    col = row.column()
                    remove_operator = col.operator("scg_cycler.remove_channel_keyframe")
                    remove_operator.bone_name = self.bone_name
                    remove_operator.channel_type = self.channel_type
                    remove_operator.channel_axis = self.channel_axis
                    remove_operator.index = index

        return ChannelPanel

    def add_panels(self):
        for type, axis in self.panel_ids:
            panel_id = "{0}_{1}_{2}".format(self.bone_name.upper().replace(".", "_").replace("-", "_"), type.upper(), axis.upper())
            if panel_id not in self.panel_factory.panels:
                new_class = self.create_panel_class(channel_type=type, channel_axis=axis)
                self.panel_factory.register_new_panel(panel_id, new_class)

################
#   Controls   #
################
class SCG_Cycler_Controls(bpy.types.PropertyGroup, Context_Interface, Children_Have_Panels):
    controls : bpy.props.CollectionProperty(type=SCG_Cycler_Control)

    def __iter__(self):
        return self.controls.__iter__()

    def __len__(self):
        return len(self.controls)

    def add(self):
        control = self.controls.add()
        current_bone_names = [control.bone_name for control in self]
        for bone in self.cycler.armature.bones:
            # Only adding valid bones, via the name, this kinda needs to be done as a whitelist, and this is implemented in other places too, which is kinda bad lol
            if bone.name not in current_bone_names and "ORG" not in bone.name and "DEF" not in bone.name and "MCH" not in bone.name and "f_" != bone.name[:2] and "_master" not in bone.name:
                control.bone_name = bone.name
                break
        for type in TYPES:
            for axis in AXIS:
                control.add(type.upper(), axis.upper())
        self.add_panels()
        return control

    def remove(self, index):
        self.controls.remove(index)
        self.remove_panels()
        self.add_panels()

    def get(self, bone_name):
        for control in self.controls:
            if control.bone_name == bone_name:
                return control
        return None

    @property
    def panel_ids(self):
        return [control.bone_name for control in self]

    def create_panel_class(self, **kwargs):
        if len(kwargs)==0: return
        if "panel_id" not in kwargs: return
        name = kwargs["panel_id"]
        
        class ControlPanel(bpy.types.Panel, Context_Interface):
            bl_idname = "SCG_CYCLER_PT_{0}_Control_Panel".format(name.upper().replace(".", "_").replace("-", "_"))
            bl_label = name
            bl_category = "SCG Cycler"
            bl_space_type = "VIEW_3D"
            bl_region_type = "UI"
            bl_parent_id = "SCG_CYCLER_PT_Controls_Panel"
            bl_options = {"DEFAULT_CLOSED"}

            bone_name = name

            @property
            def control(self):
                return self.cycler.rig_action.controls.get(self.bone_name)

            @property
            def index(self):
                for index, control in enumerate(self.cycler.rig_action.controls):
                    if control.bone_name == self.bone_name:
                        return index
                return None

            def draw(self, context):
                row = self.layout.row()
                if self.control is None:
                    return
                row.prop_search(self.control, "bone_name", self.cycler.rig_bones, "whitelist")
                if self.control.mirrors:
                    col = row.column()
                    col.prop(self.control, "mirrored")
                col = row.column()
                remove = col.operator("scg_cycler.remove_control")
                remove.index = self.index
        return ControlPanel

    # Handles adding missing panels
    def add_panels(self):
        super().add_panels()
        for control in self:
            control.add_panels()

    # Remove invalid panels
    def remove_panels(self):
        super().remove_panels()
        for control in self:
            control.remove_panels()

######################
#   User Interface   #
######################
class SCG_CYCLER_PT_Controls_Panel(bpy.types.Panel, Context_Interface):
    bl_idname = "SCG_CYCLER_PT_Controls_Panel"
    bl_label = "Controls"
    bl_category = "SCG Cycler"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    @classmethod
    def poll(cls, context):
        return context.scene.scg_cycler_context.armature

    def draw(self, context):
        row = self.layout.row()
        row.operator("scg_cycler.add_control")            

#################
#   Operators   #
#################
class SCG_CYCLER_OT_Add_Control(bpy.types.Operator, Context_Interface):
    bl_idname = "scg_cycler.add_control"
    bl_label = "Add Control"
    bl_description = "Add a new Control"

    def execute(self, context):
        self.cycler.rig_action.controls.add()
        return {"FINISHED"}

class SCG_CYCLER_OT_Remove_Control(bpy.types.Operator, Context_Interface):
    bl_idname = "scg_cycler.remove_control"
    bl_label = "Remove Control"
    bl_description = "Remove a Control"

    index : bpy.props.IntProperty(name="Index")

    def execute(self, context):
        self.cycler.rig_action.controls.remove(self.index)
        return {"FINISHED"}

###############################
#   Register and Unregister   #
###############################
classes = (SCG_Cycler_Control, SCG_Cycler_Controls, SCG_CYCLER_PT_Controls_Panel, SCG_CYCLER_OT_Add_Control, SCG_CYCLER_OT_Remove_Control)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    
def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)