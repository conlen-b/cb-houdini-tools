# -*- coding: utf-8 -*-

"""
copyParmsToOtherNode
A script to copy a parm or all parms in source parm folder from source node to the destination node.
Updated 12/10/2026

Information and instructions on GitHub:
https://github.com/conlen-b/cb-houdini-tools/blob/main/copy-parms-to-other-node/CopyParmsToOtherNode.py
"""

__author__ = "Conlen Breheny"
__copyright__ = "Copyright 2025, Conlen Breheny"
__version__ = "1.3.1" #Major.Minor.Patch

import logging

from copyParmsToOtherNode.gui.UI import CopyParmsUI

#Errors go to error output, rest go to standard output
logging.basicConfig(format=f"%(levelname)s: [Copy Parms to Other Node] %(message)s")
#Logger for this module
logger = logging.getLogger("copyParmsToOtherNode")
#Log all levels down to the debug level
logger.setLevel(logging.DEBUG)
#On code release, switch from DEBUG to INFO
#logger.setLevel(logging.INFO)
