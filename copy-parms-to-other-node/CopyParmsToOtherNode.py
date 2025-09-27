# -*- coding: utf-8 -*-

"""
CopyParmsToOtherNode.py
A script to copy a parm or all parms in source parm folder from source node to the destination node.
Updated 9/27/2025

To run, go to the Houdini shelf and right click -> New Tool, go to the Script tab, paste the script
into the editor, scroll down to the bottom (line 147), fill in the correct input parameters, hit
accept, and press the new button in the shelf.

It is recommended to run this script from a Shelf Tool instead of the Python shell so that the
actions taken by the script can be undone/redone with ctrl+z.

https://github.com/conlen-b/cb-houdini-tools/blob/main/copy-parms-in-folder-to-other-node/CopyParmsInFolderToOtherNode.py
"""

__author__ = "Conlen Breheny"
__copyright__ = "Copyright 2025, Conlen Breheny"
__version__ = "1.2.0" #Major.Minor.Patch

import hou
import logging
from typing import Generator, Tuple

#Errors go to error output, rest go to standard output
logging.basicConfig()
#Logger for this module
logger = logging.getLogger(__name__)
#Log all levels down to the debug level
logger.setLevel(logging.DEBUG)
#On code release, switch from DEBUG to INFO
#logger.setLevel(logging.INFO)


def _walk_parm_templates(
    entries : Tuple[hou.ParmTemplate, ...]
    #Generator type hint formatting: Generator[yield_type, send_type, return_type]
) -> Generator[hou.ParmTemplate, None, None]:
    """
    Recursively yield all parm templates (including nested inside folders).
    
    :param entries: Tuple of hou.ParmTemplate
    """
    for template in entries:
        yield template
        if isinstance(template, hou.FolderParmTemplate):
            # Recurse into subfolder contents
            for child in _walk_parm_templates(template.parmTemplates()):
                yield child

def _ZspcCopyParmsToOtherNode(
    src_node_name: str,
    dst_node_name: str,
    src_name: str,
    src_label: str = None
) -> None:
    """
    Copies a parm or all parms in source parm folder from source node to the destination node.

    :param src_node_name: string argument representing the Houdini path to the node to copy the
        folder from.
    :param dst_node_name: string argument representing the Houdini path to the node to copy the
        folder to.
    :param src_name: string argument representing the name of the parm/folder in the source
        node's Operator Type Properties > Parameters > [folder] > Name, eg. "folder_5"
    :param src_label: optional string argument representing the label of the parm/folder in the
        source node's Operator Type Properties > Parameters > [folder] > Label, eg. "Guide"
    :return: Void
    """

    #Get nodes
    src_node = hou.node(src_node_name)
    dst_node = hou.node(dst_node_name)

    # Get parameter templates (interface definitions)
    src_ptg = src_node.parmTemplateGroup()
    dst_ptg = dst_node.parmTemplateGroup()
    
    src_all_parm_templates = list(_walk_parm_templates(src_ptg.entries()))
    
    # Find the source parm
    src_parm = None
    for template in src_all_parm_templates:
        if template.name() != src_name:
            continue
        if src_label is not None and template.label() != src_label:
            continue

        src_parm = template
        break
    
    if src_parm is None:
        raise RuntimeError(
            (
                "Folder/parm of name {f_name} and label {f_label} not found in source "
                "node's parameters."
            ).format(f_name=src_name, f_label=src_label))

    dst_name = src_parm.name()
    dst_label = src_parm.label()

    dst_all_parm_templates = list(_walk_parm_templates(dst_ptg.entries()))

    parm_to_remove = next(
        (parm for parm in dst_all_parm_templates if parm.name() == dst_name),
        None
    ) #Returns the first match, otherwise returns None

    if parm_to_remove is not None:
        logger.debug(parm_to_remove)
        dst_ptg.remove(parm_to_remove)
        logger.warning("Existing parameter/folder has been replaced with copied parameter/folder.")


    if isinstance(template, hou.FolderParmTemplate):
        # Copy the folder and all its child parameters
        new_folder = hou.FolderParmTemplate(dst_name,
                                            dst_label,
                                            folder_type=hou.folderType.Tabs)

        for parm in src_parm.parmTemplates():
            new_folder.addParmTemplate(parm)

        # Append the new folder to the destination parameter interface
        dst_ptg.append(new_folder)
    else:
        #Copy the single parameter
        dst_ptg.append(src_parm)

    # Apply the modified parameter interface to the destination node
    try:
        dst_node.setParmTemplateGroup(dst_ptg)
    except hou.OperationFailed as error:
        logger.error(
            (
                "Failed to copy - one or more parameters likely already exist with "
                "conflicting names. Houdini error: {f_error}"
            ).format(f_error=error)
        )
    else:
        logger.info(
            (
                "Successfully copied parameter/folder {f_label} from source to destination."
            ).format(f_label=dst_label))

#Input parameters
src_node_name = "/obj/geo1/rbdbulletsolver1"
dst_node_name = "/obj/geo1/rbdbulletsolver1/dopnet/forces/CUSTOM_GUIDE_CTRL"
src_name = "folder32"
src_label = "Guided Neighbors"

"""
Run function
(not using __name__ __main__ check because it is ran from a shelf tool button, where
__name__ != __main__)
"""
_ZspcCopyParmsToOtherNode(src_node_name, dst_node_name, src_name, src_label)