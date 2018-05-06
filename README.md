# asBlenderTools
Custom tools for blender

- as_batch_rename - 

tool for renaming of multiple selected objects. Can use old name, add prefixes and suffixes. Advanced counter with controllable padding.

- as_group_parent - 

This script parents multiple selected objects under new empty. Actually this is emulation of Maya's 'make group' behaviour. 
All new empties are called groupParent by default, because Blender has completely different concept of groups than Maya.
Has additional features:
- to World mode - new groupParent always be parented to None
- Options where new groupParent origin will be: world( 0 0 0 ), location of parent object, location of active obkect and 3d Cursor location.
  (Maya always put it only to world( 0 0 0 ))