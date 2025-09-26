# -*- coding: utf-8 -*-

"""
CopyParmsInFolderToOtherNode.py
A script to copy all parms in source parm folder from source node to the destination node.
Updated 9/25/2025

To run, go to the Houdini shelf and right click -> New Tool, go to the Script tab, paste the script
into the editor, scroll down to the bottom (line 103), fill in the correct input parameters, hit
accept, and press the new button in the shelf.

It is recommended to run this script from a Shelf Tool instead of the Python shell so that the
actions taken by the script can be undone/redone with ctrl+z.

https://github.com/conlen-b/cb-houdini-tools/blob/main/copy-parms-in-folder-to-other-node/CopyParmsInFolderToOtherNode.py
"""

__author__ = "Conlen Breheny"
__copyright__ = "Copyright 2025, Conlen Breheny"
__version__ = "1.1.0" #Major.Minor.Patch

import hou
import logging

#Errors go to error output, rest go to standard output
logging.basicConfig()
#Logger for this module
logger = logging.getLogger(__name__)
#Log all levels down to the debug level
#logger.setLevel(logging.DEBUG)
#On code release, switch from DEBUG to INFO
logger.setLevel(logging.INFO)

def _ZspcCopyParmsInFolderToOtherNode(src_node_name: str,
                                        dst_node_name: str,
                                        src_folder_name: str,
                                        src_folder_label: str = None) -> None:
    """
    Copies all parms in source parm folder from source node to the destination node.

    :param src_node_name: string argument representing the Houdini path to the node to copy the
        folder from.
    :param dst_node_name: string argument representing the Houdini path to the node to copy the
        folder to.
    :param src_folder_name: string argument representing the name of the folder in the source
        node's Operator Type Properties > Parameters > [folder] > Name, eg. "folder_5"
    :param src_folder_label: optional string argument representing the label of the folder in the
        source node's Operator Type Properties > Parameters > [folder] > Label, eg. "Guide"
    :return: Void
    """

    #Get nodes
    src_node = hou.node(src_node_name)
    dst_node = hou.node(dst_node_name)

    # Get parameter templates (interface definitions)
    src_ptg = src_node.parmTemplateGroup()
    dst_ptg = dst_node.parmTemplateGroup()

    # Find the source folder
    src_folder = None
    for template in src_ptg.entries():
        if not isinstance(template, hou.FolderParmTemplate):
            continue
        if template.name() != src_folder_name:
            continue
        if src_folder_label is not None and template.label() != src_folder_label:
            continue

        src_folder = template
        break

    dst_folder_name = src_folder.name()
    dst_folder_label = src_folder.label()

    # Check if a folder of the same name already exists in destination
    existing_dst_folder = None
    for entry in dst_ptg.entries():
        if isinstance(entry, hou.FolderParmTemplate) and entry.name() == dst_folder_name:
            existing_dst_folder = entry
            break

    # If folder exists, remove it to replace
    if existing_dst_folder:
        dst_ptg.remove(existing_dst_folder)

    # Copy the folder and all its child parameters
    new_folder = hou.FolderParmTemplate(dst_folder_name,
                                        dst_folder_label,
                                        folder_type=hou.folderType.Tabs)

    for parm in src_folder.parmTemplates():
        new_folder.addParmTemplate(parm)

    # Append the new folder to the destination parameter interface
    dst_ptg.append(new_folder)

    # Apply the modified parameter interface to the destination node
    dst_node.setParmTemplateGroup(dst_ptg)

    logger.info("Successfully copied folder {f_label} from source to destination.".format(f_label=dst_folder_label))

#Input parameters
src_node_name = "/obj/geo1/rbdbulletsolver1"
dst_node_name = "/obj/geo1/rbdbulletsolver1/dopnet/forces/CUSTOM_GUIDE_CTRL"
src_folder_name = "folder_5"
src_folder_label = "Guide"

"""
Run function
(not using __name__ __main__ check because it is ran from a shelf tool button, where
__name__ != __main__)
"""
_ZspcCopyParmsInFolderToOtherNode(src_node_name, dst_node_name, src_folder_name, src_folder_label)