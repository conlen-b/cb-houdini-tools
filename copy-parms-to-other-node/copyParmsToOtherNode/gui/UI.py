# -*- coding: utf-8 -*-

"""
Some code/logic from: https://github.com/fredrikaverpil/pyvfx-boilerplate/blob/master/src/pyvfx_boilerplate/boilerplate_ui.py
TODO: Make a method _create_connections (see Mauricio's example) to create connections separately from building the UI
"""

import logging
import hou
from ..core.CopyParmsToOtherNode import _copy_parms_to_other_node as CopyParmsToOtherNode
try:
    from qtpy import QtCore, QtWidgets
except ImportError:
    raise ImportError(
        'QtPy not found in the Houdini environment. Please install it with:\n'
        '`"[PROGRAM_FILES_PATH]\\Side Effects Software\\'
        'Houdini [VERSION]\\bin\\hython.exe" -m pip install QtPy`.'
    )



logger = logging.getLogger(f"copyParmsToOtherNode.{__name__}")



def _houdini_main_window() -> QtWidgets.QWidget:
    """
    Return Houdini's main window.
    
    :return: The main Qt window of Houdini.
    """
    return hou.ui.mainQtWindow()

class CopyParmsUI(QtWidgets.QMainWindow):
    """
    GUI window for copying parameters from one Houdini node to another.
    """

    WINDOW_NAME = "copyParmsToOtherNode"
    WINDOW_TITLE = "Copy Parms To Other Node"

    def __init__(self):
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

    def _build_ui(self):
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
        grid_layout_source_destination.setColumnStretch(1, 1)  # Input field expands
        grid_layout_source_destination.setColumnStretch(2, 0)  # Button column fixed

        #Source node
        self.input_source_node = hou.qt.InputField(hou.qt.InputField.StringType, 1)
        self.node_chooser_source_node = hou.qt.NodeChooserButton()
        self._add_node_input_to_grid_layout(self.input_source_node,
                                            self.node_chooser_source_node,
                                            "Source Node",
                                            grid_layout_source_destination,
                                            0)

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
        self.input_destination_node = hou.qt.InputField(hou.qt.InputField.StringType, 1)
        self.node_chooser_destination_node = hou.qt.NodeChooserButton()
        self._add_node_input_to_grid_layout(self.input_destination_node,
                                            self.node_chooser_destination_node,
                                            "Destination Node",
                                            grid_layout_source_destination,
                                            4)

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

    def _add_node_input_to_grid_layout(
            self,
            input_field: hou.qt.InputField,
            node_chooser: hou.qt.NodeChooserButton,
            label_text: str,
            layout: QtWidgets.QGridLayout,
            layout_row: int
        ) -> None:
        """
        Add a labeled node input field + node chooser button to a grid layout.

        :param input_field: The hou.qt.InputField where the node path will be placed.
        :param node_chooser: The NodeChooserButton used to select the node.
        :param label_text: Text that will appear in the label (e.g. "Source Node").
        :param layout: The QGridLayout to which the widgets will be added.
        :param layout_row: The row index in the layout where this block should be inserted.
        :return: None
        """
        # Label
        label = hou.qt.FieldLabel(label_text)
        label.setFixedWidth(150)  # prevent clipping
        layout.addWidget(label, layout_row, 0)

        # Input field
        input_field.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed
        )
        layout.addWidget(input_field, layout_row, 1)

        # Node chooser button
        node_chooser.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed,
            QtWidgets.QSizePolicy.Fixed
        )

        node_chooser.nodeSelected.connect(
            lambda node: self._set_input_field_from_node_chooser(
                node=node,
                input_field=input_field
            )
        )

        layout.addWidget(node_chooser, layout_row, 2)

    def _add_labeled_input_to_grid_layout(
        self,
        input_field: hou.qt.InputField,
        label_text: str,
        layout: QtWidgets.QGridLayout,
        layout_row: int
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

    def _set_input_field_from_node_chooser(self,
                                            node: hou.Node = None,
                                            input_field: hou.qt.InputField = None) -> None:
        """
        Set the value of an input field from a node chooser.

        :param node: The node selected from the chooser.
        :param input_field: The input field to update.
        :return: Void
        """
        if not node or not input_field:
            return
        input_field.setValue(node.path(), 0)

    def _copy_parms(self) -> None:
        """
        Copies parameters from the source node to the destination node based on the user's input.

        :return: Void
        """
        src_node_name = self.input_source_node.value(0)
        src_name = self.input_source_name.value(0)
        src_label = self.input_source_label.value(0)
        dst_node_name = self.input_destination_node.value(0)
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
