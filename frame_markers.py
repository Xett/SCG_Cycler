import bpy

from .interfaces import SCG_Cycler_Context_Interface as Context_Interface
from .work import WorkQueue, UpdateMarkerLengthJob

####################
#   Frame Marker   #
####################
class SCG_Cycler_Frame_Marker(bpy.types.PropertyGroup, Context_Interface):
    def update_frame_marker(self, context):
        WorkQueue().add(UpdateMarkerLengthJob())
    # Displayed props
    name : bpy.props.StringProperty(name="Name", update=update_frame_marker)


    def get_length(self):
        if "current_length" in self:
            return self["current_length"]
        else:
            return 0.0
    def set_length(self, value):
        #bpy.context.scene.frame_end
        self["old_length"] = self.length
        self["current_length"] = value
        WorkQueue().add(UpdateMarkerLengthJob())

    length : bpy.props.FloatProperty(name="Marker Length", get=get_length, set=set_length, default=0.0, min=0.0, max=50.0, subtype="PERCENTAGE", step=10.0)
    
    # Displayed as a string, not editable in the ui
    def get_frame(self):
        if "current_frame" in self:
            return self["current_frame"]
        else:
            return 0.0
    def set_frame(self, value):
        self["old_frame"] = self.frame
        self["current_frame"] = value
    frame : bpy.props.FloatProperty(get=get_frame, set=set_frame)

    @property
    def old_frame(self):
        if "old_frame" in self:
            return self["old_frame"]
        return 0.0

#########################
#   Container Wrapper   #
#########################
class SCG_Cycler_Frame_Markers(bpy.types.PropertyGroup, Context_Interface):
    markers : bpy.props.CollectionProperty(type=SCG_Cycler_Frame_Marker)

    def __iter__(self):
        return self.markers.__iter__()

    def __len__(self):
        return len(self.markers)

    def add(self):
        marker = self.markers.add()
        self.update()
        return marker

    def remove(self, index):
        self.markers.remove(index)
        self.update()

#################
#   Operators   #
#################
class SCG_CYCLER_OT_Add_Frame_Marker(bpy.types.Operator, Context_Interface):
    bl_idname = "scg_cycler.add_frame_marker"
    bl_label = "Add Marker"
    bl_description = "Add a new Frame Marker"

    def execute(self, context):
        self.cycler.timings.frame_markers.add()
        return {"FINISHED"}

class SCG_CYCLER_OT_Remove_Frame_Marker(bpy.types.Operator, Context_Interface):
    bl_idname = "scg_cycler.remove_frame_marker"
    bl_label = "Remove Marker"
    bl_description = "Removes a Frame Marker"

    index : bpy.props.IntProperty(name="Index")

    def execute(self, context):
        self.cycler.timings.frame_markers.remove(self.index)
        return {"FINISHED"}

######################
#   User Interface   #
######################
class SCG_CYCLER_PT_Frame_Markers_Panel(bpy.types.Panel, Context_Interface):
    bl_idname = "SCG_CYCLER_PT_Frame_Markers_Panel"
    bl_label = "Frame Markers"
    bl_category = "SCG Cycler"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        row = self.layout.row()
        row.operator("scg_cycler.add_frame_marker")
        for index, frame_marker in enumerate(self.cycler.timings.frame_markers):
            row = self.layout.row()
            row.prop(frame_marker, "name")
            col = row.column()
            col.prop(frame_marker, "length")
            col = row.column()
            col.label(text="Frame: {0}".format(frame_marker.frame))
            col = row.column()
            remove_op=col.operator("scg_cycler.remove_frame_marker")
            remove_op.index = index

###############################
#   Register and Unregister   #
###############################
classes = (SCG_Cycler_Frame_Marker, SCG_Cycler_Frame_Markers, SCG_CYCLER_OT_Add_Frame_Marker, SCG_CYCLER_OT_Remove_Frame_Marker, SCG_CYCLER_PT_Frame_Markers_Panel)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    
def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)