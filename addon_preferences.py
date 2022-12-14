import bpy

from .interfaces import SCG_Cycler_Context_Interface as Context_Interface
from .bone import SCG_Cycler_Whitelist_Path
from .animation_template import SCG_Cycler_Animation_Template_Path

class SCG_Cycler_Addon_Preferences(bpy.types.AddonPreferences, Context_Interface):
    bl_idname = __package__
    whitelist_paths : bpy.props.CollectionProperty(type=SCG_Cycler_Whitelist_Path)
    animation_template_paths : bpy.props.CollectionProperty(type=SCG_Cycler_Animation_Template_Path)

    def draw(self, context):
        row = self.layout.row()
        row.label(text="Rig Bone Whitelist Paths")
        column = row.column()
        box = column.box()
        box_row = box.row()
        box_row.operator("scg_cycler.add_whitelist_path")
        for index, whitelist_path in enumerate(self.whitelist_paths):
            row = box.row()
            row.prop(whitelist_path, "path")
            column = row.column()
            remove_whitelist_path = column.operator("scg_cycler.remove_whitelist_path")
            remove_whitelist_path.index = index
        
        row = self.layout.row()
        row.label(text="Animation Template Paths")
        column = row.column()
        box = column.box()
        box_row = box.row()
        box_row.operator("scg_cycler.add_animation_template_path")
        for index, animation_template_path in enumerate(self.animation_template_paths):
            row = box.row()
            row.prop(animation_template_path, "path")
            column = row.column()
            remove_path = column.operator("scg_cycler.remove_animation_template_path")
            remove_path.index = index

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