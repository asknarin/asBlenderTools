# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Alex Sknarin 2017
# Simple Batch rename tool
# TODO #1: Sort by name
# TODO #2: Sort by selection history
# TODO #3: Extract old padding from names
# TODO #4: Filter by object types
# TODO #5: Write documentation and move it to open section of confluence

bl_info = {
    "name": "as Batch Renamer",
    "description": "Renames Selected objects with given pattern",
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
from bpy.types import AddonPreferences

#-------------------------------------------------------------------------------------------------
# Calculations
#-------------------------------------------------------------------------------------------------

def as_assemble_name(mode = 0, base = "_", addpref = False, pref = "_",  
                     addsuf = False, suf = "_",
                     chregister = False, register_mode = "OP1",
                     addcount = True, start = 1, step = 1, padding = 2, index = 0):
    base_name = ""
    prefix = ""
    suffix = ""
    counter = ""
    if(mode == 0):
        # If new name
        base_name = base
    elif(mode == 1):
        # If change name
        base_name = base
        if(addpref == True):
            prefix = pref
    
        if(addsuf == True):
            suffix = suf

        if(chregister == True):
            # Capital
            if(register_mode == "OP1"):
                base_name = prefix+base_name+suffix
                base_name = base_name.capitalize()
            # CapitalBase
            elif(register_mode == "OP2"):
                base_name = base_name.capitalize()
                prefix = prefix.lower()
                suffix = suffix.lower()
                base_name = prefix+base_name+suffix
            # CapitalBoth
            elif(register_mode == "OP3"):
                base_name = base_name.capitalize()
                prefix = prefix.capitalize()
                suffix = suffix.lower()
                base_name = prefix+base_name+suffix
            # Lower
            elif(register_mode == "OP4"):
                base_name = prefix+base_name+suffix
                base_name = base_name.lower()
            # Upper
            elif(register_mode == "OP5"):
                base_name = prefix+base_name+suffix
                base_name = base_name.upper()
        else:
            base_name = prefix+base_name+suffix

    # Add counter
    if (addcount == True):
        counter = "_" + str((index + start) * step).zfill(padding)

    # Assemble full new name
    new_name = base_name + counter
    return new_name
    
     

#-------------------------------------------------------------------------------------------------
# Properties
#-------------------------------------------------------------------------------------------------

class as_rename_property_group(PropertyGroup):
    # Select rename mode
    as_rename_type = EnumProperty(
        name="Mode",
        description="Select what rename mode to use",
        items=[ ('OP1', "New", "Create new names"),
                ('OP2', "Change", "Correct current selected names"),
              ]
    )
    # String Input field for basename
    as_rename_basename_input = StringProperty(
        name = "",
        description = "Base for new names",
        default = ""
    )
    
    # Add prefix selector
    as_add_prefix = BoolProperty(
        name = "Add Prefix",
        description = "Enables adding prefix to current name",
        default = False
    )
    
    # String Input field for Prefix
    as_rename_prefix_input = StringProperty(
        name = "",
        description = "Prefix to add",
        default = ""
    )
    
    # Add suffix selector
    as_add_suffix = BoolProperty(
        name = "Add Suffix",
        description = "Enables adding suffix to current name",
        default = False
    )
    
    # String Input field for Suffix
    as_rename_suffix_input = StringProperty(
        name = "",
        description = "Prefix to add",
        default = ""
    )
    
    # Change register
    as_rename_change_register = BoolProperty(
        name = "Change Register",
        description = "Change register of letters in a name",
        default = False
    )
    
    as_rename_register_type = EnumProperty(
        name="",
        description="Select register change mode",
        items=[ ('OP1', "Capital", "Make first letter Capital with prefix or not"),
                ('OP2', "CapitalBase", "Only first letter of Base name Capital"),
                ('OP3', "CapitalBoth", "First Capital foth both Base name and Prefix "),
                ('OP4', "Lower", "All letters Lower"),
                ('OP5', "Upper", "All letters Capital"),
              ]
    )

    # Counter Properties
    as_add_counter  = BoolProperty(
        name = "Add Counter",
        description = "Add counter",
        default = True
    )
    
    as_rename_start = IntProperty(
        name = "Start",
        description = "Counter number to start from",
        default = 1,
        min = 0,
        soft_max = 10,
        soft_min = 0,
    )
    
    as_rename_step = IntProperty(
        name = "Step",
        description = "Step size",
        default = 1,
        min = 1,
        soft_max = 5,
        soft_min = 1,
    )
    
    as_rename_padding = IntProperty(
        name = "Padding",
        description = "Padding size - to keep number section of equal length filling it with zeroes",
        default = 2,
        min = 1,
        soft_max = 4,
        soft_min = 1,
    )
    
    
    


#-------------------------------------------------------------------------------------------------
# Operator
#-------------------------------------------------------------------------------------------------

class as_rename_operator(Operator):
    bl_idname = "wm.do_as_rename"
    bl_label = "Batch Rename"
    
    def execute(self, context):
        scene = context.scene
        rename_data = scene.as_rename_prop_grp
        
        # Get selected Objects
        sel_objects = bpy.context.selected_objects

        if(len(sel_objects) == 0):
            self.report({"WARNING"}, "Nothing selected!")
            return {"FINISHED"}
        
        i = 0
        for obj in sel_objects:
            if(rename_data.as_rename_type == "OP1"):
                new_name = as_assemble_name(0, rename_data.as_rename_basename_input, 
                                            False, "", 
                                            False, "",
                                            False, "",
                                            rename_data.as_add_counter, 
                                            rename_data.as_rename_start,
                                            rename_data.as_rename_step,
                                            rename_data.as_rename_padding,
                                            i)
                obj.name = new_name
                
            if(rename_data.as_rename_type == "OP2"):
                new_name = as_assemble_name(1, obj.name,
                                            rename_data.as_add_prefix, 
                                            rename_data.as_rename_prefix_input, 
                                            rename_data.as_add_suffix, 
                                            rename_data.as_rename_suffix_input,
                                            rename_data.as_rename_change_register,
                                            rename_data.as_rename_register_type,
                                            rename_data.as_add_counter, 
                                            rename_data.as_rename_start,
                                            rename_data.as_rename_step,
                                            rename_data.as_rename_padding,
                                            i)
                obj.name = new_name

            # Increment counter
            i += rename_data.as_rename_step

        return {"FINISHED"}
        

#-------------------------------------------------------------------------------------------------
# Panel
#-------------------------------------------------------------------------------------------------

class as_batch_rename_panel(Panel):
    bl_idname = "as_batch_rename_panel"
    bl_label  = "as_Batch rename"
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
        rename_data = scene.as_rename_prop_grp
        
        layout.prop(rename_data, "as_rename_type")
    
        if(rename_data.as_rename_type == "OP1"):
            # New name mode - just create full new base name from given string
            layout.label("New Base Name:")
            layout.prop(rename_data, "as_rename_basename_input")
        elif(rename_data.as_rename_type == "OP2"):
            # Change name mode
            layout.prop(rename_data, "as_add_prefix")
            if(rename_data.as_add_prefix == True):
                layout.prop(rename_data, "as_rename_prefix_input")
            layout.prop(rename_data, "as_add_suffix")
            if(rename_data.as_add_suffix == True):
                layout.prop(rename_data, "as_rename_suffix_input")
        
            layout.prop(rename_data, "as_rename_change_register")
            if(rename_data.as_rename_change_register == True):
                layout.prop(rename_data, "as_rename_register_type")

        
        # Counter
        layout.prop(rename_data, "as_add_counter")
        if(rename_data.as_add_counter == True):
            layout.prop(rename_data, "as_rename_start")
            layout.prop(rename_data, "as_rename_step")
            layout.prop(rename_data, "as_rename_padding")
        
        
            
        
        layout.label("Preview:")
        
        if(rename_data.as_rename_type == "OP1"):
            # Preview new name
            layout.label(as_assemble_name(0, rename_data.as_rename_basename_input, 
                                            False, "", 
                                            False, "",
                                            False, "",
                                            rename_data.as_add_counter, 
                                            rename_data.as_rename_start,
                                            rename_data.as_rename_step,
                                            rename_data.as_rename_padding,
                                            0))
        if(rename_data.as_rename_type == "OP2"):
            # Get name of first selected object for preview
            selected_object_name = ""
            if(len(bpy.context.selected_objects) > 0):
                selected_object_name = bpy.context.selected_objects[0].name
            else:
                selected_object_name = "Nothing_Selected!!!"
            
            # Preview changed name
            layout.label(as_assemble_name(1, selected_object_name,
                                            rename_data.as_add_prefix, 
                                            rename_data.as_rename_prefix_input, 
                                            rename_data.as_add_suffix, 
                                            rename_data.as_rename_suffix_input,
                                            rename_data.as_rename_change_register,
                                            rename_data.as_rename_register_type,
                                            rename_data.as_add_counter, 
                                            rename_data.as_rename_start,
                                            rename_data.as_rename_step,
                                            rename_data.as_rename_padding,
                                            0))
        
        
        layout.operator("wm.do_as_rename")
            
    
#-------------------------------------------------------------------------------------------------
# AddonPreferences
#-------------------------------------------------------------------------------------------------

# Define Panel classes for updating
as_panel = as_batch_rename_panel

def update_as_batch_rename_panel(self, context):
    message = "as_batch_rename: Updating Panel locations has failed"
    try:
        if "bl_rna" in as_panel.__dict__:
            bpy.utils.unregister_class(as_panel)

        as_panel.bl_category = context.user_preferences.addons[__name__].preferences.category
        bpy.utils.register_class(as_panel)

    except Exception as e:
        print("\n[{}]\n{}\n\nError:\n{}".format(__name__, message, e))
        pass

class as_batch_renameAddonPreferences(AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    
    bl_idname = __name__

    category = StringProperty(
            name="Category",
            description="Choose a name for the category of the panel",
            default="Tools",
            update=update_as_batch_rename_panel,
            )

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        col = row.column()
        col.label(text="Category:")
        col.prop(self, "category", text="")
		

# ------------------------------------------------------------------------
# Register and Unregister
# ------------------------------------------------------------------------

def register():
    #bpy.utils.register_module(__name__)
    bpy.utils.register_class(as_batch_renameAddonPreferences)
    bpy.utils.register_class(as_rename_property_group)
    bpy.utils.register_class(as_rename_operator)
    bpy.utils.register_class(as_batch_rename_panel)

    bpy.types.Scene.as_rename_prop_grp = PointerProperty(type=as_rename_property_group)

def unregister():
    #bpy.utils.register_module(__name__)
    bpy.utils.unregister_class(as_batch_rename_panel)
    bpy.utils.unregister_class(as_rename_operator)
    bpy.utils.unregister_class(as_rename_property_group)
    bpy.utils.unregister_class(as_batch_renameAddonPreferences)
    del bpy.types.Scene.as_rename_prop_grp
    


if __name__ == "__main__":
    register()