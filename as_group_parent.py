# Alex Sknarin 2018
# Maya-like Group behavior
# TODO addon preferences

bl_info = {
    "name": "as Group Parent",
    "description": "Parents selected objects to a new Empty (Maya make group with additional features)",
    "author": "asknarin",
    "version": (0, 0, 1),
    "blender": (2, 79, 0),
    "location": "3D View > as Custom",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "https://asknarin.atlassian.net/wiki/spaces/ASTOOLS/pages/222101505/asBatchRename",
    "tracker_url": "",
    "category": "Object"
}

# Import from blender API
import bpy
from bpy.props import StringProperty
from bpy.props import EnumProperty
from bpy.props import BoolProperty
from bpy.props import IntProperty
from bpy.props import PointerProperty

from bpy.types import Panel
from bpy.types import PropertyGroup
from bpy.types import Operator

#-------------------------------------------------------------------------------------------------
# Calculations
#-------------------------------------------------------------------------------------------------

def as_create_empty(location, name):
    bpy.ops.object.empty_add(type='PLAIN_AXES', 
                                            radius=1, 
                                            view_align=False, 
                                            location=location, 
                                            layers=(True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))
    tmp_obj = bpy.context.selected_objects[0]
    tmp_obj.name = name


def as_find_megaparent(s_obj):
    if(s_obj.parent == None):
        return s_obj
    else:
        return as_find_megaparent(s_obj.parent)
    

def as_get_children(s_obj, children_list):
    s_children = s_obj.children
    if(s_children != None):
        for ch in s_children:
            children_list.append(ch.name)
            as_get_children(ch, children_list)

def as_find_shared_parent(s_obj, children_names):
    s_children = s_obj.children
    if(s_children != None):
        for ch in s_children:
            subchildren = []
            as_get_children(ch, subchildren)
            # Count children
            count_current_children = []
            for sch in subchildren:
                if(sch in children_names):
                    count_current_children.append(sch)
            # This child has all selected objects go deeper
            if(len(count_current_children) == 0):
                print(" ")
            elif(len(count_current_children) == len(children_names)):
                return as_find_shared_parent(ch, children_names)
            elif((len(count_current_children) < len(children_names)) and (len(count_current_children) > 0)):
                return ch.parent
    else:
        return ch.parent
    
def as_check_parent(s_obj, possible_parents_list):
    s_parent = s_obj.parent
    if(s_parent == None):
        return False
    else:
        if(s_parent.name in possible_parents_list):
            return True
        else:
            return as_check_parent(s_parent, possible_parents_list)
    

#-------------------------------------------------------------------------------------------------
# Properties
#-------------------------------------------------------------------------------------------------

class as_groupParent_property_group(PropertyGroup):
    
    # String Input field for basename
    as_groupParent_basename_input = StringProperty(
        name = "",
        description = "Base name for the new Empty",
        default = "GroupParent"
    )
    
    
    # Parent to world mode selector
    as_to_world = BoolProperty(
        name = "Always to World",
        description = "new groupParent will be always parented to world. If disabled current parent will be used if possible",
        default = False
    )
        
    # Origin mode selector
    as_origin_mode = EnumProperty(
        name="Origin",
        description="Select what rename mode to use",
        items=[ ('OP1', "World", "Create Empty at World's 0 0 0"),
                ('OP2', "Parent", "Create Empty at the parent location"),
                ('OP3', "3DCursor", "Create Empty at the 3D Cursor location"),
                ('OP4', "ActiveObject", "Create Empty at the ActiveObject location"),
              ]
        )
    
    # Nested parent behavior
    as_nested_parent_mode = EnumProperty(
        name="Nested",
        description="Select what to do if selected objects already have parent//child relationship",
        items=[ ('OP1', "Extract", "Parent will be moved to new groupParent with all its children, then selected children will be moved to the root of a groupParent"),
                ('OP2', "Keep", "Parent with all its children (selected or not) will be moved into a new groupParent"),
              ]
        )
        

#-------------------------------------------------------------------------------------------------
# Operator
#-------------------------------------------------------------------------------------------------

class as_make_groupParent_operator(Operator):
    bl_idname = "wm.as_make_groupparent"
    bl_label = "Make groupParent"
    
    def execute(self, context):
        scene = context.scene
        groupParent_data = scene.as_groupParent_prop_grp
        
        # Get selected objects and active object
        sel_objs = bpy.context.selected_objects
        active_obj = bpy.context.active_object
        
        if(len(sel_objs) == 0):
            print("Nothing Selected")
            return {"FINISHED"}
        
        
        # Nested children
        sel_objs_clean = []
        if(groupParent_data.as_nested_parent_mode == "OP2"):
            #print("need to clean selected list from nested children")
            tmp_names = []
            for obj in sel_objs:
                tmp_names.append(obj.name)
            for obj in sel_objs:
                if(not as_check_parent(obj, tmp_names)):
                    sel_objs_clean.append(obj)
        else:
            sel_objs_clean = sel_objs

        sel_objnames = []
        for obj in sel_objs_clean:
            sel_objnames.append(obj.name)
            
        # Create an empty
        
        empty_obj = active_obj
        #print(empty_obj.name)
        
        if(groupParent_data.as_to_world):
            # Just parent to world
            if((groupParent_data.as_origin_mode == "OP1") or (groupParent_data.as_origin_mode == "OP2")):
                as_create_empty((0.0, 0.0, 0.0), groupParent_data.as_groupParent_basename_input)
                empty_obj = bpy.context.selected_objects[0]
            elif(groupParent_data.as_origin_mode == "OP3"):
                as_create_empty(bpy.context.scene.cursor_location, groupParent_data.as_groupParent_basename_input)
                empty_obj = bpy.context.selected_objects[0]
            elif(groupParent_data.as_origin_mode == "OP4"):
                as_create_empty(active_obj.matrix_world.to_translation(), groupParent_data.as_groupParent_basename_input)
                empty_obj = bpy.context.selected_objects[0]
        else:
            # get parents of selected objects
            worldParent = False
            parents = []
            for obj in sel_objs_clean:
                if(obj.parent != None):
                    parents.append(obj.parent.name)
                else:
                    parents.append("")
            
            if ("" in parents):
                worldParent = True

            if(worldParent):
                #### Create empty same way as in world mode
                if((groupParent_data.as_origin_mode == "OP1") or (groupParent_data.as_origin_mode == "OP2")):
                    as_create_empty((0.0, 0.0, 0.0), groupParent_data.as_groupParent_basename_input)
                    empty_obj = bpy.context.selected_objects[0]
                elif(groupParent_data.as_origin_mode == "OP3"):
                    as_create_empty(bpy.context.scene.cursor_location, groupParent_data.as_groupParent_basename_input)
                    empty_obj = bpy.context.selected_objects[0]
                elif(groupParent_data.as_origin_mode == "OP4"):
                    as_create_empty(active_obj.matrix_world.to_translation(), groupParent_data.as_groupParent_basename_input)
                    empty_obj = bpy.context.selected_objects[0]
            else:
                # Find Closest parent
                print("Parenting Group to some object")
                
                # 1. Situation - all have the same parent. New Empty will be placed under it
                contracted_parents = []
                contracted_parents.append(parents[0])
                for p in parents:
                    if(p not in contracted_parents):
                        contracted_parents.append(p)
                
                if(len(contracted_parents) == 1):
                    print("There is the only parent: " + contracted_parents[0] + " will be used as parent for new groupParent")
                    #### Create empty and parent it to this parent
                    parent_obj = bpy.data.objects.get(contracted_parents[0])
                    if(groupParent_data.as_origin_mode == "OP1"):
                        as_create_empty((0.0, 0.0, 0.0), groupParent_data.as_groupParent_basename_input)
                        empty_obj = bpy.context.selected_objects[0]
                    elif(groupParent_data.as_origin_mode == "OP2"):
                        as_create_empty(parent_obj.matrix_world.to_translation(), groupParent_data.as_groupParent_basename_input)
                        empty_obj = bpy.context.selected_objects[0]
                    elif(groupParent_data.as_origin_mode == "OP3"):
                        as_create_empty(bpy.context.scene.cursor_location, groupParent_data.as_groupParent_basename_input)
                        empty_obj = bpy.context.selected_objects[0]
                    elif(groupParent_data.as_origin_mode == "OP4"):
                        as_create_empty(active_obj.matrix_world.to_translation(), groupParent_data.as_groupParent_basename_input)
                        empty_obj = bpy.context.selected_objects[0]
                    empty_obj.parent = parent_obj
                    empty_obj.matrix_parent_inverse = parent_obj.matrix_world.inverted()
                else:
                    print("there more than one parent - need to find MEGAPARENT")
                    # 2. Situation - selected objects have more than 1 megaparent. World will be used
                    # get megaparent of each selected object:
                    megaparents = []
                    for obj in sel_objs_clean:
                        megaparents.append(as_find_megaparent(obj).name)
                    # Constract megaparents list
                    contracted_megaparents = []
                    contracted_megaparents.append(megaparents[0])
                    for mp in megaparents:
                        if(mp not in contracted_megaparents):
                            contracted_megaparents.append(mp)
                    
                    if(len(contracted_megaparents) > 1):
                        #### Create empty same way as in world mode
                        if((groupParent_data.as_origin_mode == "OP1") or (groupParent_data.as_origin_mode == "OP2")):
                            as_create_empty((0.0, 0.0, 0.0), groupParent_data.as_groupParent_basename_input)
                            empty_obj = bpy.context.selected_objects[0]
                        elif(groupParent_data.as_origin_mode == "OP3"):
                            as_create_empty(bpy.context.scene.cursor_location, groupParent_data.as_groupParent_basename_input)
                            empty_obj = bpy.context.selected_objects[0]
                        elif(groupParent_data.as_origin_mode == "OP4"):
                            as_create_empty(active_obj.matrix_world.to_translation(), groupParent_data.as_groupParent_basename_input)
                            empty_obj = bpy.context.selected_objects[0]
                    else:
                        # 3. Situation - object has shared parents in hierarchy
                        # Start from the top of hierarchy
                        sharedparent = as_find_shared_parent(bpy.data.objects.get(contracted_megaparents[0]), sel_objnames)
                        print(sharedparent)
                        ### Use shared parent to put empty into
                        parent_obj = sharedparent
                        if(groupParent_data.as_origin_mode == "OP1"):
                            as_create_empty((0.0, 0.0, 0.0), groupParent_data.as_groupParent_basename_input)
                            empty_obj = bpy.context.selected_objects[0]
                        elif(groupParent_data.as_origin_mode == "OP2"):
                            as_create_empty(parent_obj.matrix_world.to_translation(), groupParent_data.as_groupParent_basename_input)
                            empty_obj = bpy.context.selected_objects[0]
                        elif(groupParent_data.as_origin_mode == "OP3"):
                            as_create_empty(bpy.context.scene.cursor_location, groupParent_data.as_groupParent_basename_input)
                            empty_obj = bpy.context.selected_objects[0]
                        elif(groupParent_data.as_origin_mode == "OP4"):
                            as_create_empty(active_obj.matrix_world.to_translation(), groupParent_data.as_groupParent_basename_input)
                            empty_obj = bpy.context.selected_objects[0]
                        empty_obj.parent = parent_obj
                        empty_obj.matrix_parent_inverse = parent_obj.matrix_world.inverted()

        # Parent all selected objects to an empty
        for obj in sel_objs_clean:
            # unparent and keep transform
            bpy.ops.object.select_all(action='DESELECT')
            obj.select = True
            bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
            bpy.context.scene.objects.active = empty_obj
            bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
        
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.scene.objects.active = empty_obj
        empty_obj.select = True

        return {"FINISHED"}

#-------------------------------------------------------------------------------------------------
# Panel
#-------------------------------------------------------------------------------------------------

class as_groupParent_panel(Panel):
    bl_idname = "as_groupParent_panel"
    bl_label  = "as_Group Parent"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "Tools"
    bl_context = "objectmode"
    
    #@classmethod
    #def poll(self,context):
    #    return context.object is not None
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        groupParent_data = scene.as_groupParent_prop_grp
        

        layout.label("New Base Name:")
        layout.prop(groupParent_data, "as_groupParent_basename_input")
        layout.prop(groupParent_data, "as_to_world")
        layout.prop(groupParent_data, "as_origin_mode")
        layout.prop(groupParent_data, "as_nested_parent_mode")
        layout.operator("wm.as_make_groupparent")


# ------------------------------------------------------------------------
# Register and Unregister
# ------------------------------------------------------------------------

def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.as_groupParent_prop_grp = PointerProperty(type=as_groupParent_property_group)

def unregister():
    bpy.utils.register_module(__name__)
    del bpy.types.Scene.as_groupParent_prop_grp

if __name__ == "__main__":
    register()