from PyQt5.QtWidgets import QWidget, QLineEdit, QPushButton, QGridLayout

from pygadmin.widgets.search_replace_parent import SearchReplaceParent


class SearchReplaceWidget(QWidget):
    """
    Create an own widget for the search and replace dialog in the editor widget.
    """

    def __init__(self, parent):
        super().__init__()

        # Check for the correct instance of the parent.
        if isinstance(parent, SearchReplaceParent) and isinstance(parent, QWidget):
            # Use the given parent, which is normally an editor widget.
            self.setParent(parent)
            self.init_ui()
            self.init_grid()

    def init_ui(self):
        """
        Create the user interface.
        """

        # Create a dictionary for saving all search items.
        self.search_items = {}

        # Create a line edit as search field.
        search_line_edit = QLineEdit()
        # Deactivate the button for searching the next match for a changed text in the line edit, because the function
        # for searching the next item is based on the first search.
        search_line_edit.textChanged.connect(self.parent().deactivate_search_next_and_replace_buttons_and_deselect)
        self.search_items["search_line_edit"] = search_line_edit

        # Create a button for search.
        search_button = QPushButton("Search")
        # Search the (sub) string in the search line edit with clicking on the button.
        search_button.clicked.connect(self.parent().search_and_select_sub_string)
        self.search_items["search_button"] = search_button

        # Define a button for the next search result.
        search_next_button = QPushButton("Next")
        # Search the next (sub) string after clicking on the button.
        search_next_button.clicked.connect(self.parent().search_and_select_next_sub_string)
        self.search_items["search_next_button"] = search_next_button

        # Create a button for closing the widget.
        cancel_button = QPushButton("Cancel")
        # Close the dialog with setting it invisible.
        cancel_button.clicked.connect(self.parent().close_search_replace_widget)
        self.search_items["cancel_button"] = cancel_button

        # Create a dictionary for saving all replace items.
        self.replace_items = {}

        # Create line edit for the replace text.
        replace_line_edit = QLineEdit()
        # Connect the text with the function for checking if a replace should be enabled.
        replace_line_edit.textChanged.connect(self.parent().check_for_replace_enabling)
        self.replace_items["replace_line_edit"] = replace_line_edit

        # Create a button for replacing.
        replace_button = QPushButton("Replace")
        # Connect the button to the function for replacing the current searched selection.
        replace_button.clicked.connect(self.parent().replace_current_selection)
        self.replace_items["replace_button"] = replace_button

        # Create a button for replacing all occurrences of a sub string.
        replace_all_button = QPushButton("Replace All")
        # Connect the button to the function for replacing all sub string matches.
        replace_all_button.clicked.connect(self.parent().replace_all_sub_string_matches)
        self.replace_items["replace_all_button"] = replace_all_button

        # Hide the components for replacing, because the standard dialog is a plain, simple search dialog.
        self.hide_replace_components()

        self.show()

    def init_grid(self):
        """
        Create the grid layout.
        """

        # Define the layout.
        grid_layout = QGridLayout(self)

        # Define a count for placing the items in a row.
        count = 0
        # Place every item of the search items in a row.
        for item in self.search_items.values():
            grid_layout.addWidget(item, 0, count)
            count += 1

        # Set the count back to 0 for the next items.
        count = 0
        # Place every item of the replace items in a row below the search items.
        for item in self.replace_items.values():
            grid_layout.addWidget(item, 1, count)
            count += 1

        grid_layout.setSpacing(10)

        self.setLayout(grid_layout)

    def hide_replace_components(self):
        """
        Hide the replace components with setting them to invisible.
        """

        # Use the dictionary with the replace items for setting every item to invisible.
        for item in self.replace_items.values():
            item.setVisible(False)

    def show_replace_components(self):
        """
        Show the replace components with setting them visible.
        """

        # Set every item in the replace dictionary to visible.
        for item in self.replace_items.values():
            item.setVisible(True)

    def deactivate_replace_buttons(self):
        """
        Deactivate both replace buttons.
        """

        self.replace_items["replace_button"].setEnabled(False)
        self.replace_items["replace_all_button"].setEnabled(False)

    def activate_replace_buttons(self):
        """
        Activate both replace buttons.
        """

        self.replace_items["replace_button"].setEnabled(True)
        self.replace_items["replace_all_button"].setEnabled(True)

    def activate_search_next_button(self):
        """
        Activate the search next button, so a jump to the next search result with the selection is possible.
        """

        self.search_items["search_next_button"].setEnabled(True)

    def deactivate_search_next_button(self):
        """
        Deactivate the search next button.
        """

        self.search_items["search_next_button"].setEnabled(False)

    def activate_replace_button(self):
        """
        Activate the replace button.
        """

        self.replace_items["replace_button"].setEnabled(True)

    def deactivate_replace_all_button(self):
        """
        Deactivate the replace all button.
        """

        self.replace_items["replace_all_button"].setEnabled(False)

    def set_widget_visible(self, replace=False):
        """
        Set the widget visible. Replace is as default False, so there is only a plain and simple standard search dialog.
        If replace is not False, the replace components are shown.
        """

        # Set the widget visible.
        self.setVisible(True)

        # Check for the replace parameter and if this parameter is not False, show also the replace components.
        if replace:
            self.show_replace_components()

        # Hide the replace components, so there is only the search dialog.
        else:
            self.hide_replace_components()

    def set_search_text(self, search_text):
        """
        Set a given text in the search line edit.
        """

        self.search_items["search_line_edit"].setText(search_text)

    def get_replace_text(self):
        """
        Return the text of the replace line edit.
        """

        return self.replace_items["replace_line_edit"].text()

    def get_search_text(self):
        """
        Return the text of the search line edit.
        """

        return self.search_items["search_line_edit"].text()

    def set_widget_invisible(self):
        self.setVisible(False)
