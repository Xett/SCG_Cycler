import bpy
import json
import os

from .interfaces import SCG_Cycler_Context_Interface as Context_Interface
from .interfaces import SCG_Cycler_Collection_Wrapper as Collection_Wrapper
from .interfaces import SCG_Cycler_Loads_From_JSON as Loads_From_JSON

######################
#   Bone Reference   #
######################

# Right now, this is just a container of a name for the bone
# This is used by the valid armature bones collection
class SCG_Cycler_Bone_Reference(bpy.types.PropertyGroup):
    name : bpy.props.StringProperty()

class SCG_Cycler_Whitelist_Path(bpy.types.PropertyGroup):
    path : bpy.props.StringProperty(name="Path", subtype="DIR_PATH")

class SCG_Cycler_Whitelist(bpy.types.PropertyGroup):
    name : bpy.props.StringProperty(name="Name")
    bones : bpy.props.CollectionProperty(type=SCG_Cycler_Bone_Reference)

    @property
    def bone_names(self):
        return [bone.name for bone in self.bones]

    @property
    def enum_item(self):
        return (self.name.upper(), self.name, self.name)

    @property
    def json_data(self):
        return self.bone_names

#################
#   Rig Bones   #
#################
class SCG_Cycler_Rig_Bones(bpy.types.PropertyGroup, Context_Interface):
    whitelist : bpy.props.CollectionProperty(type=SCG_Cycler_Bone_Reference)
    blacklist : bpy.props.CollectionProperty(type=SCG_Cycler_Bone_Reference)

    whitelist_current_index : bpy.props.IntProperty()
    blacklist_current_index : bpy.props.IntProperty()

    def current_whitelist_name_updated(self, context):
        for whitelist in self.cycler.rig_bone_whitelists:
            if whitelist.name == self.current_whitelist_name:
                self.armature_changed()
                for bone in whitelist.bones:
                    for index, blacklist_bone in enumerate(self.blacklist):
                        if bone.name == blacklist_bone.name:
                            self.blacklist.remove(index)
                            if not bone.name in self.whitelist_names:
                                new_bone = self.whitelist.add()
                                new_bone.name = bone.name
                            break

    current_whitelist_name : bpy.props.StringProperty(name="Current Whitelist", update=current_whitelist_name_updated)

    @property
    def whitelist_names(self):
        return [bone.name for bone in self.whitelist]

    @property
    def blacklist_names(self):
        return [bone.name for bone in self.blacklist]

    @property
    def bones(self):
        if self.cycler.rig_action.armature:
            return [bone.name for bone in self.cycler.rig_action.armature.bones]
        return []

    def armature_changed(self):
        self.whitelist.clear()
        self.blacklist.clear()

        for bone_name in self.bones:
            new_bone = self.blacklist.add()
            new_bone.name = bone_name

    @property
    def json_data(self):
        return self.whitelist_names

class SCG_Cycler_Rig_Bone_Whitelists(bpy.types.PropertyGroup, Context_Interface, Loads_From_JSON):
    @property
    def paths(self):
        return bpy.context.preferences.addons[__package__].preferences.whitelist_paths
    @property
    def data_text_name(self):
        return "rig_whitelists"
    @property
    def json_entries_name(self):
        return "whitelists"
    @property
    def default_data_string(self):
        return "{\"whitelists\":{}}"
    children : bpy.props.CollectionProperty(type=SCG_Cycler_Whitelist)

    def set_child_from_json_data(self, child, json_data):
        child.bones.clear()
        for bone_name in json_data:
            new_bone = child.bones.add()
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
        return self.cycler.rig_action.rig_bones.blacklist[self.cycler.rig_action.rig_bones.blacklist_current_index].name

    def execute(self, context):
        bone_name = self.bone_name
        if len(self.cycler.rig_action.rig_bones.blacklist) == 0:
            return {"CANCELLED"}
        whitelist_bone = self.cycler.rig_action.rig_bones.whitelist.add()
        whitelist_bone.name = bone_name
        for index, bone in enumerate(self.cycler.rig_action.rig_bones.blacklist):
            if bone.name == bone_name:
                self.cycler.rig_action.rig_bones.blacklist.remove(index)
                break
        return {"FINISHED"}

class SCG_CYCLER_OT_Blacklist_Bone(bpy.types.Operator, Context_Interface):
    bl_idname = "scg_cycler.blacklist_bone"
    bl_label = "<-"
    bl_description = "Move Bone to Blacklist"

    @property
    def bone_name(self):
        return self.cycler.rig_action.rig_bones.whitelist[self.cycler.rig_action.rig_bones.whitelist_current_index].name

    def execute(self, context):
        bone_name = self.bone_name
        if len(self.cycler.rig_action.rig_bones.whitelist) == 0:
            return {"CANCELLED"}
        for index, bone in enumerate(self.cycler.rig_action.rig_bones.whitelist):
            if bone.name == bone_name:
                self.cycler.rig_action.rig_bones.whitelist.remove(index)
                break
        blacklist_bone = self.cycler.rig_action.rig_bones.blacklist.add()
        blacklist_bone.name = bone_name
        return {"FINISHED"}

class SCG_CYCLER_OT_Add_Whitelist_Path(bpy.types.Operator, Context_Interface):
    bl_idname = "scg_cycler.add_whitelist_path"
    bl_label = "Add Whitelist Path"
    bl_description = "Add a new path to search for rig bone whitelists in"

    def execute(self, context):
        bpy.context.preferences.addons[__package__].preferences.whitelist_paths.add()
        return {"FINISHED"}

class SCG_CYCLER_OT_Remove_Whitelist_Path(bpy.types.Operator, Context_Interface):
    bl_idname = "scg_cycler.remove_whitelist_path"
    bl_label = "Remove Whitelist Path"
    bl_description = "Removes a Whitelist Path"

    index : bpy.props.IntProperty()

    def execute(self, context):
        bpy.context.preferences.addons[__package__].preferences.whitelist_paths.remove(self.index)
        return {"FINISHED"}

class SCG_CYCLER_OT_Refresh_Whitelists(bpy.types.Operator, Context_Interface):
    bl_idname = "scg_cycler.refresh_whitelists"
    bl_label = "Refresh Whitelists"
    bl_description = "Refreshes the current Whitelists"

    def execute(self, context):
        self.cycler.rig_bone_whitelists.search()
        return {"FINISHED"}

class SCG_CYCLER_OT_Save_Whitelist(bpy.types.Operator, Context_Interface):
    bl_idname = "scg_cycler.save_whitelist"
    bl_label = "Save Whitelist"
    bl_description = "Saves the current Whitelist"

    def execute(self, context):
        if self.cycler.rig_action.rig_bones.current_whitelist_name == "":
            return {"CANCELLED"}
        
        self.cycler.rig_bone_whitelists.add_to_data(self.cycler.rig_action.rig_bones.current_whitelist_name, self.cycler.rig_action.rig_bones.json_data)
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

    @classmethod
    def poll(cls, context):
        return bpy.context.scene.scg_cycler_context.rig_action

    def draw(self, context):
        self.layout.row().operator("scg_cycler.refresh_whitelists")

        whitelist_row = self.layout.row()
        whitelist_row.prop(self.cycler.rig_action.rig_bones, "current_whitelist_name")
        whitelist_row.prop_search(self.cycler.rig_action.rig_bones, "current_whitelist_name", self.cycler.rig_bone_whitelists, "children", results_are_suggestions=True)
        column = whitelist_row.column()
        column.operator("scg_cycler.save_whitelist")
        main_row = self.layout.row()

        blacklist_column = main_row.column()
        blacklist_row = blacklist_column.row()
        blacklist_row.label(text="Blacklist")
        blacklist_row = blacklist_column.row()
        blacklist_row.template_list("SCG_CYCLER_UL_Bone_List", "Bone_Blacklist", self.cycler.rig_action.rig_bones, "blacklist", self.cycler.rig_action.rig_bones, "blacklist_current_index")

        buttons_column = main_row.column()
        row = buttons_column.row()
        whitelist = row.operator("scg_cycler.whitelist_bone")
        row = buttons_column.row()
        blacklist = row.operator("scg_cycler.blacklist_bone")
        
        whitelist_column = main_row.column()
        whitelist_row = whitelist_column.row()
        whitelist_row.label(text="Whitelist")
        whitelist_row = whitelist_column.row()
        whitelist_column.template_list("SCG_CYCLER_UL_Bone_List", "Bone_Whitelist", self.cycler.rig_action.rig_bones, "whitelist", self.cycler.rig_action.rig_bones, "whitelist_current_index")

###############################
#   Register and Unregister   #
###############################
classes = (SCG_Cycler_Bone_Reference, SCG_Cycler_Whitelist_Path, SCG_Cycler_Whitelist, SCG_Cycler_Rig_Bones, SCG_Cycler_Rig_Bone_Whitelists, SCG_CYCLER_OT_Whitelist_Bone, SCG_CYCLER_OT_Blacklist_Bone, SCG_CYCLER_OT_Add_Whitelist_Path, SCG_CYCLER_OT_Remove_Whitelist_Path, SCG_CYCLER_OT_Refresh_Whitelists, SCG_CYCLER_OT_Save_Whitelist, SCG_CYCLER_UL_Bone_List, SCG_CYCLER_PT_Rig_Bones_Panel)

def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)
    
def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)