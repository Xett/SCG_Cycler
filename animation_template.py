import bpy

from .interfaces import SCG_Cycler_Context_Interface as Context_Interface
from .interfaces import SCG_Cycler_Collection_Wrapper as Collection_Wrapper
from .interfaces import SCG_Cycler_Loads_From_JSON as Loads_From_JSON
from .controls import SCG_Cycler_Controls
from .timings import SCG_Cycler_Timing
import os
import json

class SCG_Cycler_Animation_Template_Keyframe(bpy.types.PropertyGroup):
    marker : bpy.props.StringProperty()
    offset : bpy.props.FloatProperty()
    inverted : bpy.props.BoolProperty()

    @property
    def json_data(self):
        return {"marker":self.marker, "offset":self.offset, "inverted":self.inverted}
    def load_from_json_data(self, json_data):
        self.marker = json_data["marker"]
        self.offset = json_data["offset"]
        self.inverted = json_data["inverted"]

class SCG_Cycler_Animation_Template_Keyframes(bpy.types.PropertyGroup, Collection_Wrapper):
    children : bpy.props.CollectionProperty(type=SCG_Cycler_Animation_Template_Keyframe)

    @property
    def json_data(self):
        return {"children":[child.json_data for child in self]}
    def load_from_json_data(self, json_data):
        for keyframe_data in json_data["children"]:
            new_keyframe = self.children.add()
            new_keyframe.load_from_json_data(keyframe_data)

class SCG_Cycler_Animation_Template_Channel(bpy.types.PropertyGroup, Collection_Wrapper):
    type : bpy.props.StringProperty()
    axis : bpy.props.StringProperty()
    parent_name : bpy.props.StringProperty()
    children : bpy.props.PointerProperty(type=SCG_Cycler_Animation_Template_Keyframes)

    @property
    def json_data(self):
        return {"type":self.type, "axis":self.axis, "parent_name":self.parent_name, "children":self.children.json_data}
    def load_from_json_data(self, json_data):
        self.type = json_data["type"]
        self.axis = json_data["axis"]
        self.parent_name = json_data["parent_name"]
        self.children.load_from_json_data(json_data["children"])

class SCG_Cycler_Animation_Template_Channels(bpy.types.PropertyGroup, Collection_Wrapper):
    children : bpy.props.CollectionProperty(type=SCG_Cycler_Animation_Template_Channel)

    @property
    def json_data(self):
        return [child.json_data for child in self]
    def load_from_json_data(self, json_data):
        for index, channel_data in enumerate(json_data):
            new_child = self.children.add()
            new_child.load_from_json_data(channel_data)

class SCG_Cycler_Animation_Template_Control(bpy.types.PropertyGroup, Collection_Wrapper):
    bone_name : bpy.props.StringProperty()
    mirrored : bpy.props.BoolProperty()
    children : bpy.props.PointerProperty(type=SCG_Cycler_Animation_Template_Channels)

    @property
    def json_data(self):
        return {"bone_name":self.bone_name, "mirrored":self.mirrored, "children":self.children.json_data}
    def load_from_json_data(self, json_data):
        self.bone_name = json_data["bone_name"]
        self.mirrored = json_data["mirrored"]
        self.children.load_from_json_data(json_data["children"])

class SCG_Cycler_Animation_Template_Controls(bpy.types.PropertyGroup, Collection_Wrapper):
    children : bpy.props.CollectionProperty(type=SCG_Cycler_Animation_Template_Control)

    @property
    def json_data(self):
        return [control.json_data for control in self]
    def load_from_json_data(self, json_data):
        self.children.clear()
        for control_data in json_data:
            new_control = self.children.add()
            new_control.load_from_json_data(control_data)

class SCG_Cycler_Animation_Template(bpy.types.PropertyGroup):
    name : bpy.props.StringProperty(name="Name")
    controls : bpy.props.PointerProperty(type=SCG_Cycler_Animation_Template_Controls)
    timings : bpy.props.PointerProperty(type=SCG_Cycler_Timing)

    @property
    def json_data(self):
        # Return json data of controls and timings
        return json.dump({"controls":self.controls.json_data, "timings":self.timings.json_data})

class SCG_Cycler_Animation_Template_Path(bpy.types.PropertyGroup):
    path : bpy.props.StringProperty(name="Path", subtype="DIR_PATH")

class SCG_Cycler_Animation_Templates(bpy.types.PropertyGroup, Context_Interface, Loads_From_JSON):
    @property
    def paths(self):
        return bpy.context.preferences.addons[__package__].preferences.animation_template_paths
    @property
    def data_text_name(self):
        return "animation_templates"
    @property
    def json_entries_name(self):
        return "templates"
    @property
    def default_data_string(self):
        return "{\"templates\":{}}"
    children : bpy.props.CollectionProperty(type=SCG_Cycler_Animation_Template)

    current_animation_template_name : bpy.props.StringProperty(name="Animation Template")

    def set_child_from_json_data(self, child, json_data):
        child.timings.load_from_json_data(json_data["timings"])
        child.controls.load_from_json_data(json_data["controls"])

#################
#   Operators   #
#################
class SCG_CYCLER_OT_Refresh_Animation_Templates(bpy.types.Operator, Context_Interface):
    bl_idname = "scg_cycler.refresh_animation_templates"
    bl_label = "Refresh Animation Templates"
    bl_description = "Refreshes the current Animation Templates"

    def execute(self, context):
        self.cycler.animation_templates.search()
        return {"FINISHED"}

class SCG_CYCLER_OT_Save_Animation_Template(bpy.types.Operator, Context_Interface):
    bl_idname = "scg_cycler.save_animation_template"
    bl_label = "Save Animation Template"
    bl_description = "Save Animation Template"

    def execute(self, context):
        if self.cycler.animation_templates.current_animation_template_name == "": return {"CANCELLED"}

        self.cycler.animation_templates.add_to_data(self.cycler.animation_templates.current_animation_template_name, self.cycler.rig_action.json_data)
        return {"FINISHED"}

class SCG_CYCLER_OT_Load_Animation_Template(bpy.types.Operator, Context_Interface):
    bl_idname = "scg_cycler.load_animation_template"
    bl_label = "Load Animation Template"
    bl_description = "Load Animation Template"

    def execute(self, context):
        for animation_template in self.cycler.animation_templates:
            if animation_template.name == self.cycler.animation_templates.current_animation_template_name:
                self.cycler.rig_action.update_from_animation_template(animation_template)
                #self.cycler.update_ui()
        return {"FINISHED"}

class SCG_CYCLER_OT_Add_Animation_Template_Path(bpy.types.Operator):
    bl_idname = "scg_cycler.add_animation_template_path"
    bl_label = "Add Animation Template Path"
    bl_description = "Add a new path to search for animation templates"

    def execute(self, context):
        bpy.context.preferences.addons[__package__].preferences.animation_template_paths.add()
        return {"FINISHED"}

class SCG_CYCLER_OT_Remove_Animation_Template_Path(bpy.types.Operator):
    bl_idname = "scg_cycler.remove_animation_template_path"
    bl_label = "Remove Animation Template Path"
    bl_description = "Remove a path to search for animation templates"

    index : bpy.props.IntProperty()

    def execute(self, context):
        bpy.context.preferences.addons[__package__].preferences.animation_template_paths.remove(self.index)
        return {"FINISHED"}

###############################
#   Register and Unregister   #
###############################
classes = (SCG_Cycler_Animation_Template_Keyframe, SCG_Cycler_Animation_Template_Keyframes, SCG_Cycler_Animation_Template_Channel, SCG_Cycler_Animation_Template_Channels, SCG_Cycler_Animation_Template_Control, SCG_Cycler_Animation_Template_Controls, SCG_Cycler_Animation_Template, SCG_Cycler_Animation_Template_Path, SCG_Cycler_Animation_Templates, SCG_CYCLER_OT_Refresh_Animation_Templates, SCG_CYCLER_OT_Save_Animation_Template, SCG_CYCLER_OT_Load_Animation_Template, SCG_CYCLER_OT_Add_Animation_Template_Path, SCG_CYCLER_OT_Remove_Animation_Template_Path)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    
def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)