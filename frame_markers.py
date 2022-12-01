import bpy

from .interfaces import SCG_Cycler_Context_Interface as Context_Interface

####################
#   Frame Marker   #
####################
def update_frame_marker(self, context):
    bpy.context.scene.scg_cycler_context.frame_markers.update()

class SCG_Cycler_Frame_Marker(bpy.types.PropertyGroup):
    # Displayed props
    name : bpy.props.StringProperty(name="Name", update=update_frame_marker)
    length : bpy.props.IntProperty(name="Marker Length", update=update_frame_marker, default=1, min=1)
    
    # Displayed as a string, not editable in the ui
    frame : bpy.props.FloatProperty()

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

    def update(self):
        frame = 1
        for marker in self.markers:
            marker.frame = frame
            frame += marker.length

        bpy.context.scene.timeline_markers.clear()
        for index, marker in enumerate(self.markers):
            marker_1 = bpy.context.scene.timeline_markers.new("{0} 1".format(marker.name), frame=marker.frame)
            marker_2 = bpy.context.scene.timeline_markers.new("{0} 2".format(marker.name), frame=marker.frame+self.cycler.half_point-1)
            if index == 0:
                marker_3 = bpy.context.scene.timeline_markers.new("{0} 1".format(marker.name), frame=self.cycler.num_animated_frames)

#################
#   Operators   #
#################
class SCG_CYCLER_OT_Add_Frame_Marker(bpy.types.Operator, Context_Interface):
    bl_idname = "scg_cycler.add_frame_marker"
    bl_label = "Add Marker"
    bl_description = "Add a new Frame Marker"

    def execute(self, context):
        self.cycler.frame_markers.add()
        return {"FINISHED"}

class SCG_CYCLER_OT_Remove_Frame_Marker(bpy.types.Operator, Context_Interface):
    bl_idname = "scg_cycler.remove_frame_marker"
    bl_label = "Remove Marker"
    bl_description = "Removes a Frame Marker"

    index : bpy.props.IntProperty(name="Index")

    def execute(self, context):
        self.cycler.frame_markers.remove(self.index)
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
        for index, frame_marker in enumerate(self.cycler.frame_markers):
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