import bpy

from .interfaces import SCG_Cycler_Context_Interface as Context_Interface
from .panel import Panel_Factory
from .constants import *
from .keyframes import SCG_Cycler_Control_Channel_Keyframes

###############
#   Channel   #
###############
class SCG_Cycler_Control_Channel(bpy.types.PropertyGroup, Context_Interface):
    def update_fcurve(self):
        for fcurve in self.cycler.action.fcurves:
            if self.data_path == fcurve.data_path and self.array_index == fcurve.array_index:
                self.__fcurve__ = fcurve
                return

    def update_mirror_fcurve(self):
        if self.mirror_channel is None:
            return
        for fcurve in self.cycler.action.fcurves:
            if self.mirror_channel.data_path in fcurve.data_path:
                self.__mirror_fcurve__ = fcurve
                return

    def type_update(self, context):
        self.update_mirror_channel()
        self.update_fcurve()
        self.update_mirror_fcurve()
    type : bpy.props.EnumProperty(name="Type", items=TYPES_ENUM_ITEMS, update=type_update)

    def update_array_index(self):
        self.__array_index__ = "XYZ".index(self.axis.upper())

    def axis_update(self, context):
        self.update_array_index()
        self.update_mirror_channel()
        self.update_fcurve()
        self.update_mirror_fcurve()
    axis : bpy.props.EnumProperty(name="Axis", items=AXIS_ENUM_ITEMS, update=axis_update)

    def update_control(self):
        control = self.cycler.controls.get(self.parent_name)
        if control is None:
            return
        self.__control__ = control

    def update_mirror_control(self):
        if self.control is not None:
            mirror_control = self.cycler.controls.get(self.control.mirror_name)
            if mirror_control is not None:
                self.__mirror_control__ = mirror_control

    def update_mirror_channel(self):
        if self.mirror_control is not None:
            mirror_channel = self.mirror_control.get(self.type, self.axis)
            if mirror_channel is not None:
                self.__mirror_channel__ = mirror_channel
    
    def parent_name_update(self, context):
        self.update_control()
        self.update_mirror_control()
        self.update_mirror_channel()
        self.update_fcurve()
        self.update_mirror_fcurve()

    parent_name : bpy.props.StringProperty(update=parent_name_update)

    def get_name(self):
        return "{0}_{1}_{2}".format(self.parent_name.upper().replace(".", "_").replace("-", "_"), self.type.upper(), self.axis.upper())

    keyframes : bpy.props.PointerProperty(type=SCG_Cycler_Control_Channel_Keyframes)

    def __iter__(self):
        return self.keyframes.__iter__()

    def __len__(self):
        return len(self.keyframes)

    def add(self, marker):
        return self.keyframes.add(marker)

    def remove(self, index):
        self.keyframes.remove(index)

    def get(self, marker):
        return self.keyframes.get(marker)

    @property
    def control(self):
        if not hasattr(self, "__control__"):
            self.update_control()
        return self.__control__ if hasattr(self, "__control__") else None

    @property
    def mirror_control(self):
        if not hasattr(self, "__mirror_control__"):
            self.update_mirror_control()
        return self.__mirror_control__ if hasattr(self, "__mirror_control__") else None

    @property
    def mirror_channel(self):
        if not hasattr(self, "__mirror_channel__"):
            self.update_mirror_channel()
        return self.__mirror_channel__ if hasattr(self, "__mirror_channel__") else None

    @property
    def data_path(self):
        return "{0}.{1}".format(self.control.data_path, self.type.lower()) if self.control is not None else ""

    @property
    def array_index(self):
        if not hasattr(self, "__array_index__"):
            self.update_array_index()
        return self.__array_index__

    @property
    def fcurve(self):
        if not hasattr(self, "__fcurve__"):
            self.update_fcurve()
        return self.__fcurve__ if hasattr(self, "__fcurve__") else None

    @property
    def mirror_fcurve(self):
        if not hasattr(self, "__mirror_fcurve__"):
            self.update_mirror_fcurve()
        return self.__mirror_fcurve__ if hasattr(self, "__mirror_fcurve__") else None

    @property
    def expected_keyframes(self):
        expected_keyframes = {}
        fcurve = self.fcurve
        for keyframe in self.keyframes:
            frame = keyframe.frame_marker.frame + keyframe.offset
            if fcurve is not None:
                for keyframe_point in fcurve.keyframe_points:
                    if keyframe_point.co[0] == frame:
                        expected_keyframes[frame] = (keyframe_point.co[1], keyframe_point, frame, False)
                        if not self.control.mirrored:
                            expected_keyframes[frame+self.cycler.half_point] = (-keyframe_point.co[1] if keyframe.inverted else keyframe_point.co[1], keyframe_point, frame, keyframe.inverted)
                        if frame==self.cycler.frame_markers.markers[0].frame+keyframe.offset:
                            expected_keyframes[frame+self.cycler.num_animated_frames] = (keyframe_point.co[1], keyframe_point, frame, False)
                        else:
                            for modifier in fcurve.modifiers:
                                if modifier.type=="CYCLES" and not len(expected_keyframes)%2:
                                    expected_keyframes[frame+self.cycler.num_animated_frames] = (fcurve.keyframe_points[0].co[1], keyframe_point, frame, False)
        if self.control.mirrored:
            if self.mirror_channel is not None:
                for keyframe in self.mirror_channel.keyframes:
                    frame = keyframe.frame_marker.frame + keyframe.offset
                    if self.mirror_channel.fcurve is not None and fcurve is not None:
                        for keyframe_point in self.mirror_channel.fcurve.keyframe_points:
                            if keyframe_point.co[0] == frame:
                                if self.type == "LOCATION":
                                    expected_keyframes[frame+self.cycler.half_point] = (-keyframe_point.co[1] if self.axis == "X" else keyframe_point.co[1], keyframe_point, frame, False)
                                elif self.type == "ROTATION_EULER":
                                    expected_keyframes[frame+self.cycler.half_point] = (-keyframe_point.co[1] if self.axis in "YZ" else keyframe_point.co[1], keyframe_point, frame, False)
                                else:
                                    expected_keyframes[frame+self.cycler.half_point] = (keyframe_point.co[1], keyframe_point, frame, False)
            
        return expected_keyframes

    def update(self):
        expected_keyframes = self.expected_keyframes
        fcurve = self.fcurve
        if fcurve is None:
            return

        # Insert a new frame if it doesn't exist, but we expect it to. Change values if it does already exist
        current_keyframes = [keyframe_point.co[0] for keyframe_point in fcurve.keyframe_points]
        for frame, value in expected_keyframes.items():
            if frame not in current_keyframes:
                new_keyframe_point = fcurve.keyframe_points.insert(frame, value[0])
                new_keyframe_point.amplitude = value[1].amplitude
                new_keyframe_point.back = value[1].back
                new_keyframe_point.easing = value[1].easing
                new_keyframe_point.handle_left_type = value[1].handle_left_type
                new_keyframe_point.handle_right_type = value[1].handle_right_type
                new_keyframe_point.handle_left[0] = (value[1].handle_left[0]-value[2])+frame
                new_keyframe_point.handle_left[1] = value[1].handle_left[1]
                new_keyframe_point.handle_right[0] = (value[1].handle_right[0]-value[2])+frame
                new_keyframe_point.handle_right[1] = value[1].handle_right[1]
                new_keyframe_point.interpolation = value[1].interpolation
                new_keyframe_point.period = value[1].period
                new_keyframe_point.type = value[1].type
            else:
                for keyframe_point in fcurve.keyframe_points:
                    if keyframe_point.co[0] == frame:
                        keyframe_point.co[1] = value[0]
                        keyframe_point.amplitude = value[1].amplitude
                        keyframe_point.back = value[1].back
                        keyframe_point.easing = value[1].easing
                        if self.control.mirrored:
                            if self.type == "LOCATION" and self.axis=="X":
                                keyframe_point.handle_left_type = value[1].handle_right_type
                                keyframe_point.handle_right_type = value[1].handle_left_type
                                keyframe_point.handle_left[0] = (value[1].handle_right[0]-value[2])+frame
                                keyframe_point.handle_left[1] = -value[1].handle_right[1]
                                keyframe_point.handle_right[0] = (value[1].handle_left[0]-value[2])+frame
                                keyframe_point.handle_right[1] = -value[1].handle_left[1]
                            elif self.type=="ROTATION_EULER" and self.axis in "YZ":
                                keyframe_point.handle_left_type = value[1].handle_right_type
                                keyframe_point.handle_right_type = value[1].handle_left_type
                                keyframe_point.handle_left[0] = (value[1].handle_right[0]-value[2])+frame
                                keyframe_point.handle_left[1] = -value[1].handle_right[1]
                                keyframe_point.handle_right[0] = (value[1].handle_left[0]-value[2])+frame
                                keyframe_point.handle_right[1] = -value[1].handle_left[1]
                        else:
                            if value[3]:
                                keyframe_point.handle_left_type = value[1].handle_left_type
                                keyframe_point.handle_right_type = value[1].handle_right_type
                                keyframe_point.handle_left[0] = (value[1].handle_left[0]-value[2])+frame
                                keyframe_point.handle_left[1] = -value[1].handle_left[1]
                                keyframe_point.handle_right[0] = (value[1].handle_right[0]-value[2])+frame
                                keyframe_point.handle_right[1] = -value[1].handle_right[1]
                            else:
                                keyframe_point.handle_left_type = value[1].handle_left_type
                                keyframe_point.handle_right_type = value[1].handle_right_type
                                keyframe_point.handle_left[0] = (value[1].handle_left[0]-value[2])+frame
                                keyframe_point.handle_left[1] = value[1].handle_left[1]
                                keyframe_point.handle_right[0] = (value[1].handle_right[0]-value[2])+frame
                                keyframe_point.handle_right[1] = value[1].handle_right[1]
                        keyframe_point.interpolation = value[1].interpolation
                        keyframe_point.period = value[1].period
                        keyframe_point.type = value[1].type
                        break
                fcurve.update()

        # Iterate through the keyframes to delete, find the keyframe, remove it and break out of finding it
        keyframes_to_delete = [keyframe_point for keyframe_point in fcurve.keyframe_points if keyframe_point.co[0] not in expected_keyframes]
        for keyframe_point in keyframes_to_delete:
            fcurve.keyframe_points.remove(keyframe_point)
                    

################
#   Channels   #
################
class SCG_Cycler_Control_Channels(bpy.types.PropertyGroup, Context_Interface):
    channels : bpy.props.CollectionProperty(type=SCG_Cycler_Control_Channel)

    def __iter__(self):
        return self.channels.__iter__()

    def __len__(self):
        return len(self.channels)

    def add(self, type, axis, parent_name):
        channel = self.channels.add()
        channel.type = type
        channel.axis = axis
        channel.parent_name = parent_name
        return channel
    
    def remove(self, type, axis):
        for index, channel in enumerate(self.channels):
            if channel.type == type and channel.axis == axis:
                self.channels.remove(index)
                return

    def get(self, type, axis):
        for channel in self.channels:
            if channel.type == type and channel.axis == axis:
                return channel
        return None

###############################
#   Register and Unregister   #
###############################
classes = (SCG_Cycler_Control_Channel, SCG_Cycler_Control_Channels)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    
def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)