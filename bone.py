import bpy

from .interfaces import SCG_Cycler_Context_Interface as Context_Interface

######################
#   Bone Reference   #
######################

# Right now, this is just a container of a name for the bone
# This is used by the valid armature bones collection
class SCG_Cycler_Bone_Reference(bpy.types.PropertyGroup):
    name : bpy.props.StringProperty()

#################
#   Rig Bones   #
#################
class SCG_Cycler_Rig_Bones(bpy.types.PropertyGroup, Context_Interface):
    whitelist : bpy.props.CollectionProperty(type=SCG_Cycler_Bone_Reference)
    blacklist : bpy.props.CollectionProperty(type=SCG_Cycler_Bone_Reference)

    whitelist_current_index : bpy.props.IntProperty()
    blacklist_current_index : bpy.props.IntProperty()

    @property
    def whitelist_names(self):
        return [bone.name for bone in self.whitelist]

    @property
    def blacklist_names(self):
        return [bone.name for bone in self.blacklist]

    @property
    def bones(self):
        if self.cycler.armature:
            return [bone.name for bone in self.cycler.armature.bones]
        return []

    def armature_changed(self):
        self.whitelist.clear()
        self.blacklist.clear()

        for bone_name in self.bones:
            new_bone = self.blacklist.add()
            new_bone.name = bone_name

#################
#   Operators   #
#################
class SCG_CYCLER_OT_Whitelist_Bone(bpy.types.Operator, Context_Interface):
    bl_idname = "scg_cycler.whitelist_bone"
    bl_label = "->"
    bl_description = "Move Bone to Whitelist"

    @property
    def bone_name(self):
        return self.cycler.rig_bones.blacklist[self.cycler.rig_bones.blacklist_current_index].name

    def execute(self, context):
        bone_name = self.bone_name
        if len(self.cycler.rig_bones.blacklist) == 0:
            return {"CANCELLED"}
        whitelist_bone = self.cycler.rig_bones.whitelist.add()
        whitelist_bone.name = bone_name
        for index, bone in enumerate(self.cycler.rig_bones.blacklist):
            if bone.name == bone_name:
                self.cycler.rig_bones.blacklist.remove(index)
                break
        return {"FINISHED"}

class SCG_CYCLER_OT_Blacklist_Bone(bpy.types.Operator, Context_Interface):
    bl_idname = "scg_cycler.blacklist_bone"
    bl_label = "<-"
    bl_description = "Move Bone to Blacklist"

    @property
    def bone_name(self):
        return self.cycler.rig_bones.whitelist[self.cycler.rig_bones.whitelist_current_index].name

    def execute(self, context):
        bone_name = self.bone_name
        if len(self.cycler.rig_bones.whitelist) == 0:
            return {"CANCELLED"}
        for index, bone in enumerate(self.cycler.rig_bones.whitelist):
            if bone.name == bone_name:
                self.cycler.rig_bones.whitelist.remove(index)
                break
        blacklist_bone = self.cycler.rig_bones.blacklist.add()
        blacklist_bone.name = bone_name
        return {"FINISHED"}

######################
#   User Interface   #
######################
class SCG_CYCLER_UL_Bone_List(bpy.types.UIList, Context_Interface):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.name)

class SCG_CYCLER_PT_Rig_Bones_Panel(bpy.types.Panel, Context_Interface):
    bl_idname = "SCG_CYCLER_PT_Rig_Bones_Panel"
    bl_label = "Rig Bones"
    bl_category = "SCG Cycler"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        main_row = self.layout.row()

        blacklist_column = main_row.column()
        blacklist_row = blacklist_column.row()
        blacklist_row.label(text="Blacklist")
        blacklist_row = blacklist_column.row()
        blacklist_row.template_list("SCG_CYCLER_UL_Bone_List", "Bone_Blacklist", self.cycler.rig_bones, "blacklist", self.cycler.rig_bones, "blacklist_current_index")

        buttons_column = main_row.column()
        row = buttons_column.row()
        whitelist = row.operator("scg_cycler.whitelist_bone")
        row = buttons_column.row()
        blacklist = row.operator("scg_cycler.blacklist_bone")
        
        whitelist_column = main_row.column()
        whitelist_row = whitelist_column.row()
        whitelist_row.label(text="Whitelist")
        whitelist_row = whitelist_column.row()
        whitelist_column.template_list("SCG_CYCLER_UL_Bone_List", "Bone_Whitelist", self.cycler.rig_bones, "whitelist", self.cycler.rig_bones, "whitelist_current_index")

###############################
#   Register and Unregister   #
###############################
classes = (SCG_Cycler_Bone_Reference, SCG_Cycler_Rig_Bones, SCG_CYCLER_OT_Whitelist_Bone, SCG_CYCLER_OT_Blacklist_Bone, SCG_CYCLER_UL_Bone_List, SCG_CYCLER_PT_Rig_Bones_Panel)

def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)
    
def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)