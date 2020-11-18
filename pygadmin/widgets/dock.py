from PyQt5.QtWidgets import QDockWidget

from pygadmin.widgets.tree import TreeWidget


class DockWidget(QDockWidget):
    """
    Create a class which is a child class of QDockWidget. This widget provides the possibility to be docked on a
    specific side of a window. It contains the tree widget and is used as a container.
    """

    def __init__(self):
        """
        Separate specific functions for initialization.
        """

        super().__init__()
        self.init_ui()

    def init_ui(self):
        """
        Design the user interface and its components.
        """

        # Get the tree widget.
        self.tree = TreeWidget()
        # Make the dock widget movable, so it can be docked to all sides and make the title bar vertical. The title bar
        # contains the title of the widget.
        self.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetVerticalTitleBar)
        self.setWindowTitle(self.tree.windowTitle())
        self.setWidget(self.tree)
