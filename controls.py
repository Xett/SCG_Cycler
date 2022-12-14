import bpy
import json

from .interfaces import SCG_Cycler_Context_Interface as Context_Interface
from .interfaces import SCG_Cycler_Collection_Wrapper as Collection_Wrapper
from .panel import Children_Have_Panels
from .channel import SCG_Cycler_Control_Channels
from .constants import *

################
#   Control   #
################
class SCG_Cycler_Control(bpy.types.PropertyGroup, Context_Interface, Collection_Wrapper, Children_Have_Panels):    
    def control_bone_get(self):
        if "bone_name" not in self:
            return ""
        return self["bone_name"]
    def control_bone_set(self, value):
        if value in [control.bone_name for control in self.cycler.rig_action.controls if self.bone_name != value]: return
        self["bone_name"] = value
    def control_bone_update(self, context):
        for channel in self:
            channel.parent_name = self.bone_name
        self.cycler.rig_action.controls.remove_panels()
        self.cycler.rig_action.controls.add_panels()

    bone_name : bpy.props.StringProperty(name="Bone", update=control_bone_update, set=control_bone_set, get=control_bone_get)
    children : bpy.props.PointerProperty(type=SCG_Cycler_Control_Channels)
    mirrored : bpy.props.BoolProperty(name="Use mirror control")

    def add(self, type, axis):
        return self.children.add(type.upper(), axis.upper(), self.bone_name)
    
    def remove(self, type, axis):
        self.children.remove(type.upper(), axis.upper())

    def get(self, type, axis):
        return self.children.get(type.upper(), axis.upper())

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
                if len(self.cycler.rig_action.timings.frame_markers) > len(self.channel):
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

    @property
    def json_data(self):
        return {"bone_name":self.bone_name, "mirrored":self.mirrored, "children":self.children.json_data}
    def load_from_json_data(self, json_data):
        self.mirrored = json_data["mirrored"]
        self.children.load_from_json_data(json_data["children"])


################
#   Controls   #
################
class SCG_Cycler_Controls(bpy.types.PropertyGroup, Context_Interface, Collection_Wrapper, Children_Have_Panels):
    children : bpy.props.CollectionProperty(type=SCG_Cycler_Control)

    def add(self, name=None):
        control = self.children.add()
        if name is None:
            current_bone_names = [control.bone_name for control in self]
            for bone in self.cycler.rig_action.armature.bones:
                if bone.name not in current_bone_names:
                    control.bone_name = bone.name
                    break
        else:
            control.bone_name = name
        for type in TYPES:
            for axis in AXIS:
                control.add(type.upper(), axis.upper())
        self.add_panels()
        return control

    def remove(self, index):
        self.children.remove(index)
        self.remove_panels()
        self.add_panels()

    def get(self, bone_name):
        for control in self.children:
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
                row.prop_search(self.control, "bone_name", self.cycler.rig_action.rig_bones, "whitelist")
                if self.control.mirrors:
                    row.column().prop(self.control, "mirrored")
                remove = row.column().operator("scg_cycler.remove_control")
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

    @property
    def json_data(self):
        return [control.json_data for control in self]
    def load_from_json_data(self, json_data):
        self.children.clear()
        for control_data in json_data:
            new_control = self.add(control_data["bone_name"])
            new_control.load_from_json_data(control_data)

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
        return context.scene.scg_cycler_context.rig_action and context.scene.scg_cycler_context.rig_action.armature

    def draw(self, context):
        self.layout.row().operator("scg_cycler.refresh_animation_templates")
        row = self.layout.row()
        row.prop_search(self.cycler.animation_templates, "current_animation_template_name", self.cycler.animation_templates, "children")
        row.column().operator("scg_cycler.load_animation_template")
        row = self.layout.row()
        row.prop(self.cycler.animation_templates, "current_animation_template_name")
        row.column().operator("scg_cycler.save_animation_template")
        self.layout.row().operator("scg_cycler.add_control")
        
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

    index : bpy.props.IntProperty()

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