import bpy
import json

from .interfaces import SCG_Cycler_Context_Interface as Context_Interface
from .interfaces import SCG_Cycler_Collection_Wrapper as Collection_Wrapper
from .work import WorkQueue, UpdateKeyframeOffsetJob

################
#   Keyframe   #
################
class SCG_Cycler_Control_Channel_Keyframe(bpy.types.PropertyGroup, Context_Interface):
    def get_frame_marker_enum_items(self, context):
        return [(frame_marker.name.upper(), frame_marker.name, frame_marker.name) for frame_marker in self.cycler.rig_action.timings.frame_markers]
    def frame_marker_update(self, context):
        for frame_marker in self.cycler.rig_action.timings.frame_markers:
            if frame_marker.name.upper() == self.marker.upper():
                self.__frame_marker__ = frame_marker
                return
    marker : bpy.props.EnumProperty(name="Frame Marker", items=get_frame_marker_enum_items, update=frame_marker_update)

    def get_offset(self):
        if not "current_offset" in self:
            self["current_offset"] = 0.0
        return self["current_offset"]
    def set_offset(self, value):
        if value > 50.0:
            value = 50.0
        elif value < 0.0:
            value = 0.0
        if value != self.get_offset():
            self["old_offset"] = self["current_offset"]
            self["current_offset"] = value
            WorkQueue().add(UpdateKeyframeOffsetJob(self, self["old_offset"], self["current_offset"]))

    offset : bpy.props.FloatProperty(name="Offset", default=0.0, min=0.0, max=50.0, subtype="PERCENTAGE", step=10.0, get=get_offset, set=set_offset)
    inverted : bpy.props.BoolProperty(name="Inverted")

    @property
    def frame_marker(self):
        if not hasattr(self, "__frame_marker__"):
            self.frame_marker_update(bpy.context)
        return self.__frame_marker__

    @property
    def old_offset(self):
        if not "old_offset" in self:
            self["old_offset"] = 0.0
        return self["old_offset"]

    @property
    def json_data(self):
        return {"marker":self.marker, "offset":self.offset, "inverted":self.inverted}
    def load_from_json_data(self, json_data):
        self.offset = json_data["offset"]
        self.inverted = json_data["inverted"]

#################
#   Keyframes   #
#################
class SCG_Cycler_Control_Channel_Keyframes(bpy.types.PropertyGroup, Context_Interface, Collection_Wrapper):
    children : bpy.props.CollectionProperty(type=SCG_Cycler_Control_Channel_Keyframe)

    def add(self, marker):
        keyframe = self.children.add()
        keyframe.marker = marker
        return keyframe
    
    def remove(self, index):
        self.children.remove(index)

    def get(self, marker):
        for keyframe in self.children:
            if keyframe.marker == marker:
                return keyframe
        return None

    @property
    def json_data(self):
        return {"children":[child.json_data for child in self]}
    def load_from_json_data(self, json_data):
        self.children.clear()
        for keyframe_data in json_data["children"]:
            new_keyframe = self.add(keyframe_data["marker"])
            new_keyframe.load_from_json_data(keyframe_data)

#################
#   Operators   #
#################
class SCG_CYCLER_OT_Add_Channel_Keyframe(bpy.types.Operator, Context_Interface):
    bl_idname = "scg_cycler.add_channel_keyframe"
    bl_label = "Add Keyframe"
    bl_description = "Add a new Keyframe to the Channel"

    bone_name : bpy.props.StringProperty()
    channel_type : bpy.props.StringProperty()
    channel_axis : bpy.props.StringProperty()

    @property
    def control(self):
        return self.cycler.rig_action.controls.get(self.bone_name)

    @property
    def channel(self):
        return self.control.get(self.channel_type, self.channel_axis)

    def execute(self, context):
        markers = [keyframe.marker for keyframe in self.channel]
        unused_markers = [frame_marker.name.upper() for frame_marker in self.cycler.rig_action.timings.frame_markers if frame_marker.name.upper() not in markers]
        if len(unused_markers)==0: return {"CANCELLED"}
        self.channel.add(unused_markers[0])
        return {"FINISHED"}

class SCG_CYCLER_OT_Remove_Channel_Keyframe(bpy.types.Operator, Context_Interface):
    bl_idname = "scg_cycler.remove_channel_keyframe"
    bl_label = "Remove Control"
    bl_description = "Remove a Control"

    bone_name : bpy.props.StringProperty()
    channel_type : bpy.props.StringProperty()
    channel_axis : bpy.props.StringProperty()

    index : bpy.props.IntProperty(name="Index")

    @property
    def control(self):
        return self.cycler.rig_action.controls.get(self.bone_name)

    @property
    def channel(self):
        return self.control.get(self.channel_type, self.channel_axis)
    
    def execute(self, context):
        self.channel.remove(self.index)
        return {"FINISHED"}

###############################
#   Register and Unregister   #
###############################
classes = (SCG_Cycler_Control_Channel_Keyframe, SCG_Cycler_Control_Channel_Keyframes, SCG_CYCLER_OT_Add_Channel_Keyframe, SCG_CYCLER_OT_Remove_Channel_Keyframe)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    
def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)