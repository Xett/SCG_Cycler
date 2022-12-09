import bpy

from .interfaces import SCG_Cycler_Context_Interface as Context_Interface
from .bone import SCG_Cycler_Whitelist_Path

class SCG_Cycler_Addon_Preferences(bpy.types.AddonPreferences, Context_Interface):
    bl_idname = __package__
    whitelist_paths : bpy.props.CollectionProperty(type=SCG_Cycler_Whitelist_Path)

    def draw(self, context):
        row = self.layout.row()
        row.label(text="Rig Bone Whitelist Paths")
        column = row.column()
        box = column.box()
        box_row = box.row()
        box_row.operator("scg_cycler.add_whitelist_path")
        for index, whitelist_path in enumerate(self.cycler.rig_bones.whitelist_paths):
            row = box.row()
            row.prop(whitelist_path, "path")
            column = row.column()
            remove_whitelist_path = column.operator("scg_cycler.remove_whitelist_path")
            remove_whitelist_path.index = index

###############################
#   Register and Unregister   #
###############################
classes = (SCG_Cycler_Addon_Preferences,)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    
def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)