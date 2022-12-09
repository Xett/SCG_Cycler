import bpy
import json
import os

from .interfaces import SCG_Cycler_Context_Interface as Context_Interface

######################
#   Bone Reference   #
######################

# Right now, this is just a container of a name for the bone
# This is used by the valid armature bones collection
class SCG_Cycler_Bone_Reference(bpy.types.PropertyGroup):
    name : bpy.props.StringProperty()

class SCG_Cycler_Whitelist_Path(bpy.types.PropertyGroup):
    path : bpy.props.StringProperty(name="Path", subtype="DIR_PATH")

    @property
    def is_valid(self):
        return False

class SCG_Cycler_Whitelist(bpy.types.PropertyGroup):
    name : bpy.props.StringProperty(name="Name")
    bones : bpy.props.CollectionProperty(type=SCG_Cycler_Bone_Reference)

    @property
    def bone_names(self):
        return [bone.name for bone in self.bones]

    @property
    def enum_item(self):
        return (self.name.upper(), self.name, self.name)

#################
#   Rig Bones   #
#################
class SCG_Cycler_Rig_Bones(bpy.types.PropertyGroup, Context_Interface):
    whitelist : bpy.props.CollectionProperty(type=SCG_Cycler_Bone_Reference)
    blacklist : bpy.props.CollectionProperty(type=SCG_Cycler_Bone_Reference)

    whitelist_current_index : bpy.props.IntProperty()
    blacklist_current_index : bpy.props.IntProperty()

    @property
    def whitelist_paths(self):
        return bpy.context.preferences.addons[__package__].preferences.whitelist_paths
    whitelists : bpy.props.CollectionProperty(type=SCG_Cycler_Whitelist)

    def current_whitelist_name_updated(self, context):
        for whitelist in self.whitelists:
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
        if self.cycler.armature:
            return [bone.name for bone in self.cycler.armature.bones]
        return []

    def armature_changed(self):
        self.whitelist.clear()
        self.blacklist.clear()

        for bone_name in self.bones:
            new_bone = self.blacklist.add()
            new_bone.name = bone_name

    def search_for_whitelists(self):
        self.cycler.rig_bones.whitelists.clear()
        for whitelist_path in self.whitelist_paths:
            directory = os.fsencode(whitelist_path.path)
            for file in os.listdir(directory):
                filename = os.fsdecode(file)
                if filename.endswith(".json"):
                    file_path = whitelist_path.path + filename
                    f = open(file_path)
                    data = json.load(f)
                    f.close()
                    self.load_whitelist(data)
        if "rig_whitelists" in bpy.data.texts:
            data_string = bpy.data.texts["rig_whitelists"].as_string()
            data = json.loads(data_string)
            self.load_whitelist(data)

    def load_whitelist(self, json_data):
        if "whitelists" not in json_data: return
        whitelists = json_data["whitelists"]
        for whitelist, data in whitelists.items():
            if not whitelist in [whitelist.name for whitelist in self.whitelists]:
                new_whitelist = self.cycler.rig_bones.whitelists.add()
                new_whitelist.name = whitelist
                for bone in data:
                    new_bone = new_whitelist.bones.add()
                    new_bone.name = bone
            else:
                for whitelist_entry in self.whitelists:
                    if whitelist_entry.name == whitelist:
                        whitelist_entry.bones.clear()
                        for bone_name in data:
                            new_bone = whitelist_entry.bones.add()
                            new_bone.name = bone_name

    def create_rig_whitelists_data(self):
        rig_whitelists_text = bpy.data.texts.new("rig_whitelists")
        rig_whitelists_text.from_string("{\"whitelists\":{}}")

    def add_whitelist_to_data(self, whitelist):
        if not "rig_whitelists" in bpy.data.texts:
            self.create_rig_whitelists_data()
        data_string = bpy.data.texts["rig_whitelists"].as_string()
        data = json.loads(data_string)
        data["whitelists"][whitelist.name] = whitelist.bone_names            
        bpy.data.texts["rig_whitelists"].from_string(json.dumps(data))

    def add_current_to_data(self):
        if not "rig_whitelists" in bpy.data.texts:
            self.create_rig_whitelists_data()
        data_string = bpy.data.texts["rig_whitelists"].as_string()
        data = json.loads(data_string)
        data["whitelists"][self.current_whitelist_name] = self.whitelist_names 
        bpy.data.texts["rig_whitelists"].from_string(json.dumps(data))


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

class SCG_CYCLER_OT_Add_Whitelist_Path(bpy.types.Operator, Context_Interface):
    bl_idname = "scg_cycler.add_whitelist_path"
    bl_label = "Add Whitelist Path"
    bl_description = "Add a new path to search for rig bone whitelists in"

    def execute(self, context):
        self.cycler.rig_bones.whitelist_paths.add()
        return {"FINISHED"}

class SCG_CYCLER_OT_Remove_Whitelist_Path(bpy.types.Operator, Context_Interface):
    bl_idname = "scg_cycler.remove_whitelist_path"
    bl_label = "Remove Whitelist Path"
    bl_description = "Removes a Whitelist Path"

    index : bpy.props.IntProperty()

    def execute(self, context):
        self.cycler.rig_bones.whitelist_paths.remove(self.index)
        return {"FINISHED"}

class SCG_CYCLER_OT_Refresh_Whitelists(bpy.types.Operator, Context_Interface):
    bl_idname = "scg_cycler.refresh_whitelists"
    bl_label = "Refresh Whitelists"
    bl_description = "Refreshes the current Whitelists"

    def execute(self, context):
        self.cycler.rig_bones.search_for_whitelists()
        return {"FINISHED"}

class SCG_CYCLER_OT_Save_Whitelist(bpy.types.Operator, Context_Interface):
    bl_idname = "scg_cycler.save_whitelist"
    bl_label = "Save Whitelist"
    bl_description = "Saves the current Whitelist"

    def execute(self, context):
        if self.cycler.rig_bones.current_whitelist_name == "":
            return {"CANCELLED"}
        self.cycler.rig_bones.add_current_to_data()
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
        self.layout.row().operator("scg_cycler.refresh_whitelists")

        whitelist_row = self.layout.row()
        whitelist_row.prop(self.cycler.rig_bones, "current_whitelist_name")
        whitelist_row.prop_search(self.cycler.rig_bones, "current_whitelist_name", self.cycler.rig_bones, "whitelists", results_are_suggestions=True)
        column = whitelist_row.column()
        column.operator("scg_cycler.save_whitelist")
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
classes = (SCG_Cycler_Bone_Reference, SCG_Cycler_Whitelist_Path, SCG_Cycler_Whitelist, SCG_Cycler_Rig_Bones, SCG_CYCLER_OT_Whitelist_Bone, SCG_CYCLER_OT_Blacklist_Bone, SCG_CYCLER_OT_Add_Whitelist_Path, SCG_CYCLER_OT_Remove_Whitelist_Path, SCG_CYCLER_OT_Refresh_Whitelists, SCG_CYCLER_OT_Save_Whitelist, SCG_CYCLER_UL_Bone_List, SCG_CYCLER_PT_Rig_Bones_Panel)

def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)
    
def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)