import bpy

from .interfaces import SCG_Cycler_Context_Interface as Context_Interface
from .panel import Panel_Factory
from .constants import *
from .keyframes import SCG_Cycler_Control_Channel_Keyframes

###############
#   Channel   #
###############

# Defines a Channel in a Control of a type (Location, Rotation, Scale) along an axis (X, Y, Z)
class SCG_Cycler_Control_Channel(bpy.types.PropertyGroup, Context_Interface):   

    # Update properties to respond to type change
    def type_update(self, context):
        self.update_mirror_channel()
        self.update_fcurve()
        self.update_mirror_fcurve()
    type : bpy.props.EnumProperty(name="Type", items=TYPES_ENUM_ITEMS, update=type_update)
    
    # Update properties to respond to type change
    def axis_update(self, context):
        self.update_array_index()
        self.update_mirror_channel()
        self.update_fcurve()
        self.update_mirror_fcurve()
    axis : bpy.props.EnumProperty(name="Axis", items=AXIS_ENUM_ITEMS, update=axis_update)
    
    # Update properties to respond to type change
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

    ###############
    #   Control   #
    ###############
    def update_control(self):
        control = self.cycler.rig_action.controls.get(self.parent_name)
        if control is None:
            return
        self.__control__ = control
    @property
    def control(self):
        if not hasattr(self, "__control__"):
            self.update_control()
        return self.__control__ if hasattr(self, "__control__") else None

    ######################
    #   Mirror Control   #
    ######################
    def update_mirror_control(self):
        if self.control is not None:
            mirror_control = self.cycler.rig_action.controls.get(self.control.mirror_name)
            if mirror_control is not None:
                self.__mirror_control__ = mirror_control
    @property
    def mirror_control(self):
        if not hasattr(self, "__mirror_control__"):
            self.update_mirror_control()
        return self.__mirror_control__ if hasattr(self, "__mirror_control__") else None

    ######################
    #   Mirror Channel   #
    ######################
    def update_mirror_channel(self):
        if self.mirror_control is not None:
            mirror_channel = self.mirror_control.get(self.type, self.axis)
            if mirror_channel is not None:
                self.__mirror_channel__ = mirror_channel
    @property
    def mirror_channel(self):
        if not hasattr(self, "__mirror_channel__"):
            self.update_mirror_channel()
        return self.__mirror_channel__ if hasattr(self, "__mirror_channel__") else None

    #################
    #   Data Path   #
    #################
    @property
    def data_path(self):
        return "{0}.{1}".format(self.control.data_path, self.type.lower()) if self.control is not None else ""

    ###################
    #   Array Index   #
    ###################
    def update_array_index(self):
        self.__array_index__ = "XYZ".index(self.axis.upper())
    @property
    def array_index(self):
        if not hasattr(self, "__array_index__"):
            self.update_array_index()
        return self.__array_index__

    ##############
    #   FCurve   #
    ##############
    def update_fcurve(self):
        for fcurve in self.cycler.action.fcurves:
            if self.data_path == fcurve.data_path and self.array_index == fcurve.array_index:
                self.__fcurve__ = fcurve
                return
    @property
    def fcurve(self):
        if not hasattr(self, "__fcurve__"):
            self.update_fcurve()
        return self.__fcurve__ if hasattr(self, "__fcurve__") else None

    #####################
    #   Mirror FCurve   #
    #####################
    def update_mirror_fcurve(self):
        if self.mirror_channel is None:
            return
        for fcurve in self.cycler.action.fcurves:
            if self.mirror_channel.data_path == fcurve.data_path and self.array_index == fcurve.array_index:
                self.__mirror_fcurve__ = fcurve
                return
    @property
    def mirror_fcurve(self):
        if not hasattr(self, "__mirror_fcurve__"):
            self.update_mirror_fcurve()
        return self.__mirror_fcurve__ if hasattr(self, "__mirror_fcurve__") else None        

################
#   Channels   #
################

# Channel Collection Property Wrapper
# Handles adding, removing, getting, length and iteration
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