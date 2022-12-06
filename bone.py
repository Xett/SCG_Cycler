import bpy

######################
#   Bone Reference   #
######################

# Right now, this is just a container of a name for the bone
# This is used by the valid armature bones collection
class SCG_Cycler_Bone_Reference(bpy.types.PropertyGroup):
    name : bpy.props.StringProperty()

###############################
#   Register and Unregister   #
###############################
classes = (SCG_Cycler_Bone_Reference,)

def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)
    
def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)