# -*- coding: utf-8 -*-

"""
Some code/logic from: https://github.com/fredrikaverpil/pyvfx-boilerplate/blob/master/src/pyvfx_boilerplate/boilerplate_ui.py
Thank you to Kiran Irugalbandara and Paweł Bernaciak for helping figure out the NodeField autocomplete.
TODO: Make a method _create_connections (see Mauricio's example) to create connections separately from building the UI
"""

import logging
import hou
import nodegraphquicknav #From $HFS/houdini/python3.11libs/nodegraphquicknav.py
from ..core.CopyParmsToOtherNode import _copy_parms_to_other_node as CopyParmsToOtherNode
try:
    from qtpy import QtCore, QtWidgets
except ImportError:
    raise ImportError(
        'QtPy not found in the Houdini environment. Please install it with a Houdini package.'
    )



logger = logging.getLogger(f"copyParmsToOtherNode.{__name__}")



"""
MONKEY PATCHES:
"""
#nodegraphquicknav: Default behavior has a bug causing a crash, so overriding
def _nodegraphquicknav_safe_children(self, node : hou.Node) -> list:
    if isinstance(node, hou.OpNode) and node.isLockedHDA():
        return []

    try:
        return node.allItems()
    except hou.OperationFailed:
        #Raised when node isn't a network (e.g. a trailing slash typed after a
        #leaf node like a Null). Not a real error - just means no children to show.
        return []

def _monkeypatch_nodegraphquicknav() -> None:
    nodegraphquicknav.ItemRef.ItemTypes = (
        hou.networkItemType.Node,
    )
    nodegraphquicknav.NodeRef._compute_children = _nodegraphquicknav_safe_children

#Called on module load/run to monkey patch the imported nodegraphquicknav
_monkeypatch_nodegraphquicknav() 



def _houdini_main_window() -> QtWidgets.QWidget:
    """
    Return Houdini's main window.

    :return: The main Qt window of Houdini.
    """
    return hou.ui.mainQtWindow()

class NodeField(QtWidgets.QLineEdit):
    """
    QLineEdit for Houdini node paths with QCompletion from the Houdini node graph quick nav.

    :ivar node_graph_completer_model: nodegraphquicknav.NetworkTreeModel representing the
        completer's data model, cleared and refreshed each time the field gains focus.
    :ivar node_graph_completer: nodegraphquicknav.NodePathCompleter representing the popup
        completer attached to this field.
    """

    def __init__(self, parent : QtWidgets.QWidget = None) -> None:
        """
        Initializes the NodeField.

        :param parent: Parent widget.
        :return: Void
        """
        super(NodeField, self).__init__(parent)
        self.node_graph_completer_model = nodegraphquicknav.NetworkTreeModel(self)
        self.node_graph_completer = nodegraphquicknav.NodePathCompleter(self)
        self.node_graph_completer.setModel(self.node_graph_completer_model)
        self.node_graph_completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
        self.setCompleter(self.node_graph_completer)

    def focusInEvent(self, event : QtCore.QEvent) -> None:
        """
        Override parent method to refresh the scene node graph tree, then runs the
        parent implementation.

        :param event: The Qt focus event.
        :return: Void
        """
        self.node_graph_completer_model.clear()
        super(NodeField, self).focusInEvent(event)

class NodeFieldWithButton(QtWidgets.QWidget):
    """
    A NodeField paired with a NodeChooserButton in a 1x2 grid (field, then button).
    Exposes text()/setText() as passthroughs to the internal field.

    :ivar field: NodeField representing the node path text field.
    :ivar chooser: hou.qt.NodeChooserButton representing the button that opens Houdini's
        node chooser dialog.
    """

    def __init__(self, parent : QtWidgets.QWidget = None) -> None:
        """
        Initializes the NodeFieldWithButton.

        :param parent: Parent widget.
        :return: Void
        """
        super(NodeFieldWithButton, self).__init__(parent)

        self.field = NodeField(self)
        self.chooser = hou.qt.NodeChooserButton()

        grid_layout = hou.qt.GridLayout()
        grid_layout.setColumnStretch(0, 1)  # Input field expands
        grid_layout.setColumnStretch(1, 0)  # Button column fixed
        self.setLayout(grid_layout)

        self.field.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed
        )
        grid_layout.addWidget(self.field, 0, 0)

        self.chooser.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed,
            QtWidgets.QSizePolicy.Fixed
        )
        grid_layout.addWidget(self.chooser, 0, 1)

        self.chooser.nodeSelected.connect(self._set_field_from_chooser)
        self.field.editingFinished.connect(self._sync_chooser_initial_node)

    def eventFilter(self, watched : QtCore.QObject, event : QtCore.QEvent) -> bool:
        """
        Override parent method to intercept mouse presses on the chooser button so
        the initial node syncs right before the dialog opens. editingFinished
        isn't reliable here: it never fires from a programmatic setText() (e.g.
        Mark Selected as Source), and even for manual typing its timing races the
        button's own click handling.

        :param watched: The watched object.
        :param event: The Qt event.
        :return: Whether the event was handled (always defers to the base class).
        """
        if watched is self.chooser and event.type() == QtCore.QEvent.MouseButtonPress:
            self._sync_chooser_initial_node()
        return super(NodeFieldWithButton, self).eventFilter(watched, event)

    def _set_field_from_chooser(self, node : hou.Node = None) -> None:
        """
        Set the field's text from a node picked via the chooser button.

        :param node: The node selected from the chooser.
        :return: Void
        """
        if not node:
            return
        self.field.setText(node.path())

    def _sync_chooser_initial_node(self) -> None:
        """
        Set the chooser's initial node to the node at the field's current path, or
        clear it if the path is blank or invalid.

        :return: Void
        """
        path = self.field.text()
        node = hou.node(path) if path else None

        try:
            self.chooser.setNodeChooserInitialNode(node)
        except hou.OperationFailed as error:
            logger.warning(f"Could not set node chooser initial node to '{path}': {error}")

    def text(self) -> str:
        """
        Return the field's text.

        :return: The field's text.
        """
        return self.field.text()

    def setText(self, text : str) -> None:
        """
        Set the field's text.

        :param text: The text to set.
        :return: Void
        """
        self.field.setText(text)

class CopyParmsUI(QtWidgets.QMainWindow):
    """
    GUI window for copying parameters from one Houdini node to another.

    :cvar WINDOW_NAME: string representing the object name assigned to the window.
    :cvar WINDOW_TITLE: string representing the window's title bar text.
    :ivar input_source_node: NodeFieldWithButton representing the Source Node path field.
    :ivar input_source_name: hou.qt.InputField representing the parm/folder name to copy.
    :ivar input_source_label: hou.qt.InputField representing the optional parm/folder label to copy.
    :ivar input_destination_node: NodeFieldWithButton representing the Destination Node path field.
    :ivar run_button: QtWidgets.QPushButton that copies the parm(s) when clicked.
    """

    WINDOW_NAME = "copyParmsToOtherNode"
    WINDOW_TITLE = "Copy Parms To Other Node"

    def __init__(self) -> None:
        """
        Initializes the CopyParmsUI window, setting up the layout and UI components.

        :return: Void
        """
        #Run the parent class' init
        parent = _houdini_main_window()
        super(CopyParmsUI, self).__init__(parent)

        #Run QMainWindow methods to initialize window
        self.resize(500, 200)
        # Set object name and window title
        self.setObjectName(CopyParmsUI.WINDOW_NAME)
        self.setWindowTitle(CopyParmsUI.WINDOW_TITLE)

        # Set window type
        self.setWindowFlags(QtCore.Qt.Window)

        self._build_ui()

    def _build_ui(self) -> None:
        """
        Build the UI layout and elements for the CopyParmsUI window.

        :return: Void
        """
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(8)

        #Source Destination Grid Layout
        grid_layout_source_destination = hou.qt.GridLayout()
        main_layout.addLayout(grid_layout_source_destination)
        grid_layout_source_destination.setColumnStretch(0, 0)  # Label column stays fixed
        grid_layout_source_destination.setColumnStretch(1, 1)  # Field+button column expands

        #Source node
        label_source_node = hou.qt.FieldLabel("Source Node")
        label_source_node.setFixedWidth(150)  # prevent clipping
        grid_layout_source_destination.addWidget(label_source_node, 0, 0)

        self.input_source_node = NodeFieldWithButton()
        grid_layout_source_destination.addWidget(self.input_source_node, 0, 1)

        #Info label
        label_info = hou.qt.FieldLabel(
                                        "Enter label and/or name for "
                                        "the parm/folder to copy."
                                    )
        label_info.setFixedWidth(300)  # prevent clipping
        grid_layout_source_destination.addWidget(label_info, 1, 1)

        #Source Name
        self.input_source_name = hou.qt.InputField(hou.qt.InputField.StringType, 1)
        self._add_labeled_input_to_grid_layout(self.input_source_name,
                                            "Name",
                                            grid_layout_source_destination,
                                            2)

        #Source Label
        self.input_source_label = hou.qt.InputField(hou.qt.InputField.StringType, 1)
        self._add_labeled_input_to_grid_layout(self.input_source_label,
                                            "Label (Optional)",
                                            grid_layout_source_destination,
                                            3)


        #Destination Node
        label_destination_node = hou.qt.FieldLabel("Destination Node")
        label_destination_node.setFixedWidth(150)  # prevent clipping
        grid_layout_source_destination.addWidget(label_destination_node, 4, 0)

        self.input_destination_node = NodeFieldWithButton()
        grid_layout_source_destination.addWidget(self.input_destination_node, 4, 1)

        #Copy Button Layout
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setSpacing(6)
        main_layout.addLayout(button_layout)

        self.run_button = QtWidgets.QPushButton("Copy Parm(s)")
        # Signal to copy when clicked
        self.run_button.clicked.connect(self._copy_parms)
        self.run_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        button_layout.addWidget(self.run_button)

        #Spacer at bottom
        main_layout.addStretch()

    def _add_labeled_input_to_grid_layout(
        self,
        input_field : hou.qt.InputField,
        label_text : str,
        layout : QtWidgets.QGridLayout,
        layout_row : int
    ) -> None:
        """
        Add a labeled InputField to a grid layout.

        :param input_field: hou.qt.InputField that will hold text.
        :param label_text: Text that appears in the label.
        :param layout: QGridLayout where these widgets will be inserted.
        :param layout_row: Row index in the layout.
        :return: None
        """

        # Label
        label = hou.qt.FieldLabel(label_text)
        label.setFixedWidth(150)
        layout.addWidget(label, layout_row, 0)

        # Input field
        input_field.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed
        )
        layout.addWidget(input_field, layout_row, 1)

    def _copy_parms(self) -> None:
        """
        Copies parameters from the source node to the destination node based on the user's input.

        :return: Void
        """
        src_node_name = self.input_source_node.text()
        src_name = self.input_source_name.value(0)
        src_label = self.input_source_label.value(0)
        dst_node_name = self.input_destination_node.text()
        if src_label:
            CopyParmsToOtherNode(src_node_name, dst_node_name, src_name, src_label)
        else:
            CopyParmsToOtherNode(src_node_name, dst_node_name, src_name)


    def display(self) -> None:
        """
        Displays the UI window.

        :return: Void
        """
        self.show()