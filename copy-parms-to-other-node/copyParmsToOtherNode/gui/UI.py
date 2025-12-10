"""
Some code/logic from: https://github.com/fredrikaverpil/pyvfx-boilerplate/blob/master/src/pyvfx_boilerplate/boilerplate_ui.py
"""

try:
    from qtpy import QtCore, QtWidgets
except ImportError:
    raise ImportError(
        'QtPy not found in the Houdini environment. Please install it with:\n'
        '`"[PROGRAM_FILES_PATH]\\Side Effects Software\\Houdini [VERSION]\\bin\\hython.exe" -m pip install QtPy`.'
    )
import logging
import hou



logger = logging.getLogger(f"copyParmsToOtherNode.{__name__}")



def _houdini_main_window():
    """Return Houdini's main window"""
    return hou.ui.mainQtWindow()

class CopyParmsUI(QtWidgets.QMainWindow):
    WINDOW_NAME = "copyParmsToOtherNode"
    WINDOW_TITLE = "Copy Parms To Other Node"

    def __init__(self):
        #Run the parent class' init
        parent = _houdini_main_window()
        super(CopyParmsUI, self).__init__(parent)

        #Run QMainWindow methods to initialize window
        # Set object name and window title
        self.setObjectName(CopyParmsUI.WINDOW_NAME)
        self.setWindowTitle(CopyParmsUI.WINDOW_TITLE)

        # Set window type
        self.setWindowFlags(QtCore.Qt.Window)

        self.build_ui()

    def build_ui(self):
    	# TODO: fill in with widgets/layout
        pass

    def display(self):
        logger.debug("This is a green bean test!!")
        self.show()