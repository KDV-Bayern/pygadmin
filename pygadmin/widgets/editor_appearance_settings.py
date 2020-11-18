from PyQt5.QtWidgets import QDialog, QPushButton, QGridLayout, QColorDialog, QLabel, QListWidget, QMessageBox, \
    QInputDialog

from pygadmin.configurator import global_app_configurator
from pygadmin.widgets.widget_icon_adder import IconAdder


class EditorAppearanceSettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setModal(True)
        # Add the pygadmin icon as window icon.
        icon_adder = IconAdder()
        icon_adder.add_icon_to_widget(self)
        self.init_ui()
        self.init_grid()

    def init_ui(self):
        """
        Initialize the user interface with its components.
        """

        self.choose_description_label = QLabel("Choose a theme to change")
        # Create a label with the description of the current option.
        self.description_label = QLabel("Change the current editor colors")

        # Show the current default theme.
        self.current_default_theme_label = QLabel("Current default theme: None")

        # Get the current default theme with its information.
        current_default_theme = global_app_configurator.get_default_color_theme_style()

        # Set the correct default theme, if it exists.
        if current_default_theme is not None:
            self.current_default_theme_label.setText("Current default theme: {}".format(current_default_theme[0]))

        # Define a list with all color types.
        color_change_list = ["default_paper_color", "default_color", "keyword_color", "number_color",
                             "other_keyword_color", "apostrophe_color"]

        # Define a dictionary for saving the following items.
        self.color_items_dictionary = {}

        # Create items for every color description.
        for color_description_item in color_change_list:
            # Define a label with a human readable appearance.
            description_label = QLabel(color_description_item.replace("_", " ").title())
            # Create a button for changing the color.
            change_color_button = QPushButton("Change Color")
            # Connect the button with the activation of a color dialog.
            change_color_button.clicked.connect(self.activate_color_dialog)
            # Save the GUI elements in the dictionary with the description as key.
            self.color_items_dictionary[color_description_item] = [description_label, change_color_button]

        # Create a list widget and initialize it.
        self.init_list_widget()

        # Define a button for saving the current state.
        self.save_changes_button = QPushButton("Save")
        # Connect the button with the function for saving the state and closing the dialog.
        self.save_changes_button.clicked.connect(self.save_changes_and_close)
        # Define a button for closing the dialog.
        self.cancel_button = QPushButton("Cancel")
        # Connect the button with the function for closing and checking for changes before.
        self.cancel_button.clicked.connect(self.check_for_changes_before_close)
        # Define a button for adding a new theme.
        self.add_new_theme_button = QPushButton("Add New Theme")
        # Connect the button with the function for adding a new theme.
        self.add_new_theme_button.clicked.connect(self.add_new_color_theme)
        # Define a button for setting the current selected theme as default.
        self.set_as_default_theme_button = QPushButton("Set As Default")
        # Connect the button with the function for setting a new default theme.
        self.set_as_default_theme_button.clicked.connect(self.set_default_theme)

        # Adjust the size of the dialog.
        self.setMaximumSize(720, 300)
        self.showMaximized()

        self.setWindowTitle("Edit Editor Appearance")
        self.show()

    def init_grid(self):
        """
        Place the components of the user interface with a grid layout.
        """

        # Get a grid layout.
        grid_layout = QGridLayout(self)

        grid_layout.addWidget(self.choose_description_label, 0, 0)

        grid_layout.addWidget(self.current_default_theme_label, 1, 0)

        grid_layout.addWidget(self.current_themes_list_widget, 2, 0, 6, 2)

        # Add the description label.
        grid_layout.addWidget(self.description_label, 0, 2)

        # Use an incrementer for the next for loop.
        grid_incrementer = 2

        # Place every value of the dictionary on the grid.
        for color_item_value in self.color_items_dictionary.values():
            # Place the label on the left.
            grid_layout.addWidget(color_item_value[0], grid_incrementer, 2)
            # Place the button on the right.
            grid_layout.addWidget(color_item_value[1], grid_incrementer, 3, 1, 2)
            # Increase the value of the incrementer for correct placing of the next components.
            grid_incrementer += 1

        # Place the buttons.
        grid_layout.addWidget(self.add_new_theme_button, 8, 0)
        grid_layout.addWidget(self.set_as_default_theme_button, 8, 1)
        grid_layout.addWidget(self.cancel_button, 8, 3)
        grid_layout.addWidget(self.save_changes_button, 8, 4)

        grid_layout.setSpacing(10)
        self.setLayout(grid_layout)

    def init_list_widget(self):
        """
        Create a list widget for the existing themes and get all current themes out of the global app configurator. Load
        all current themes in the list widget with the special function for this.
        """

        # Create the list widget.
        self.current_themes_list_widget = QListWidget()
        self.current_themes_list_widget.itemSelectionChanged.connect(self.show_colors_for_current_selected_theme)
        # Get all existing and saved themes.
        self.current_color_themes_dictionary = global_app_configurator.get_all_current_color_style_themes()
        # Load all current themes in the list widget.
        self.load_all_current_themes_in_list_widget()

    def load_all_current_themes_in_list_widget(self, item_to_select=None):
        """
        Load all current existing themes out of the class-wide dictionary in the list widget. If an item for selecting
        is not given, select the default theme.
        """

        # Clear the list widget, so old items are not as duplicate in the widget after an update.
        self.current_themes_list_widget.clear()

        # Use a count for inserting the items in the list widget, because such a count is required for placing.
        theme_number_count = 0

        # Iterate over every key.
        for color_theme_name in self.current_color_themes_dictionary.keys():
            # Set the color theme name with the count in the list widget.
            self.current_themes_list_widget.insertItem(theme_number_count, color_theme_name)
            # Increase the count for the place of the next item.
            theme_number_count += 1

        # If the item to select is None (which is the default), use the default theme.
        if item_to_select is None:
            # Get all the information about the default theme.
            default_theme_information = global_app_configurator.get_default_color_theme_style()
            # Proceed, if the default theme information is not None. The default theme information is None for an empty
            # default theme.
            if default_theme_information is not None:
                self.default_theme = default_theme_information[0]
                # Select the default theme.
                self.set_selected_item_in_list_widget(self.default_theme)

        # If an item is given, proceed.
        else:
            # Select the given item.
            self.set_selected_item_in_list_widget(item_to_select)

    def set_selected_item_in_list_widget(self, item_to_select):
        """
        Find the given item in the list widget and select it.
        """

        # Iterate over every item in the list widget with the index.
        for item_index in range(self.current_themes_list_widget.count()):
            # If the text of an item is the given item for selection, proceed.
            if self.current_themes_list_widget.item(item_index).text() == item_to_select:
                # Set the match as selected item.
                self.current_themes_list_widget.item(item_index).setSelected(True)

    def show_colors_for_current_selected_theme(self):
        """
        Get the colors of the current selected themes and color the QLabels, which show a description of the color.
        """

        # Get a new selected item.
        self.get_selected_item_in_list_widget()

        # Check for a selected item. Normally, there should be one.
        if self.selected_list_widget_item:
            color_description_with_value = self.current_color_themes_dictionary[self.selected_list_widget_item]

            # Iterate over the color description and use the description to get the color value. The color value can now
            # be used for the function for changing the color of the description label of a color.
            for color_description in self.color_items_dictionary.keys():
                self.change_color_description_label_color(color_description_with_value[color_description],
                                                          color_description)

    def get_selected_item_in_list_widget(self):
        """
        Get the current selected item in the list widget and store it in a class-wide variable.
        """

        # Check for a selected item/index.
        if self.current_themes_list_widget.selectedIndexes():
            # Get the item at the first selected index. The item is a QListWidgetItem. The text of the item is
            # necessary. The text of the item is the name of the current selected theme.
            self.selected_list_widget_item = self.current_themes_list_widget.selectedItems()[0].text()

            # Report the success.
            return True

        # If there is not a selected item, set the value to None.
        else:
            self.selected_list_widget_item = None

            return False

    def change_color_description_label_color(self, color_string, color_description):
        """
        Change the color of a description for showing the current color.
        """

        # Get the two GUI elements related to the description.
        color_gui_elements = self.color_items_dictionary[color_description]
        # Get the description label.
        description_label = color_gui_elements[0]
        # Set a new text of the description label: The color of the font is set with HTML tags as possible way
        # for setting the color of a text in a QLabel. The text is more readable for humans: The _ in the
        # description is replaced by a space and the first letter is capitalized.
        description_label.setText("<font color='{}'>{}</font>".format(color_string,
                                                                      color_description.replace("_", " ").title()))

    def activate_color_dialog(self):
        """
        Activate a QColor dialog, so a new color is chosen by the user. The color is used and set as new color for
        the description to the related button.
        """

        # Open a new color dialog.
        color_dialog = QColorDialog()
        # Get the chosen color by the user. A color is always returned by the color dialog.
        chosen_color = color_dialog.getColor()

        # Check for a valid color: The color is valid, if the user does not cancel the dialog and chooses a color.
        if chosen_color.isValid():
            # Get the name of the color.
            chosen_color_string = chosen_color.name()

            # Iterate over the items of the dictionary with the items.
            for color_description, color_gui_element in self.color_items_dictionary.items():
                # Check the first GUI element for equality with the sender: This is the button, which started the
                # function. The button as GUI element is connected with the description in the dictionary.
                if color_gui_element[1] == self.sender():
                    # Get the dictionary of the current theme.
                    theme_dictionary = self.current_color_themes_dictionary[self.selected_list_widget_item]
                    # Set the value of the color description to the new chosen color with its string.
                    theme_dictionary[color_description] = chosen_color_string

            # Update the appearance in the dialog.
            self.show_colors_for_current_selected_theme()

    def save_changes_in_configuration_and_apply(self):
        """
        Save the changes in the configuration in the style dictionary and in the configuration dictionary.
        """

        # Use every name and the related values in the dictionary for all themes.
        for color_theme_name, color_values in self.current_color_themes_dictionary.items():
            # Add the theme name and the color values as single style.
            global_app_configurator.add_style_configuration(color_theme_name, color_values)

        # Save all the style data.
        global_app_configurator.save_style_configuration_data()

        # Save the configuration data.
        global_app_configurator.save_configuration_data()

        return True

    def save_changes_and_close(self):
        """
        Save the current changes and close the dialog.
        """

        # Save the information and use the result for a user information.
        if self.save_changes_in_configuration_and_apply():
            # Inform the user about a necessary restart for applying the changes.
            QMessageBox.information(self, "Please Restart",
                                    "Please restart pygadmin to apply the changes in the editor theme.")

        # Close the dialog.
        self.close()

    def check_for_changes_before_close(self):
        """
        Check for recent unsaved changes.
        """

        # Check for unsaved themes.
        if self.current_color_themes_dictionary != global_app_configurator.get_all_current_color_style_themes():
            # Ask the user to proceed with the deletion of changes.
            cancel_with_unsaved_changes = QMessageBox.question(self, "Close with unsaved changes?",
                                                               "Do you want to close with unsaved changes, which will "
                                                               "be deleted?")

            # Check for the users answer.
            if cancel_with_unsaved_changes == QMessageBox.No:
                # If the user does not want to proceed and delete unsaved changes, end the function with a return.
                return

        # Close at this point with consent or without changes.
        self.close()

    def add_new_color_theme(self):
        """
        Add a new color theme with a name given by the user and default values for the colors, so the user can use the
        default colors for changes.
        """

        # Define a new theme name for triggering the next while loop. Normally, the result after an input dialog shows
        # the given name and the clicked button, True for Ok and False for Cancel.
        new_theme_name = ("", True)

        # Use the while loop for correct user input. Correct user input is a cancel or a non-empty string.
        while new_theme_name[0] == "" and new_theme_name[1] is True:
            # Get the name by the user.
            new_theme_name = QInputDialog.getText(self, "Theme Name", "Enter the name of the new theme")

        # If the input is not canceled, proceed.
        if new_theme_name[1] is True:
            # Set the name theme with default colors.
            self.current_color_themes_dictionary[new_theme_name[0]] = {
                "default_color": "#ff000000",
                "default_paper_color": "#ffffffff",
                "keyword_color": "#ff00007f",
                "number_color": "#ff007f7f",
                "other_keyword_color": "#ff7f7f00",
                "apostrophe_color": "#ff7f007f"
            }

            # Load all current themes in the list widget and select the new one.
            self.load_all_current_themes_in_list_widget(item_to_select=new_theme_name[0])

    def set_default_theme(self):
        """
        Set a new, default theme.
        """

        # Get a new selected item and proceed for a success.
        if self.get_selected_item_in_list_widget() is not None:
            # Define the default theme as selected list widget item.
            self.default_theme = self.selected_list_widget_item
            # Set the configuration.
            global_app_configurator.set_single_configuration("color_theme", self.default_theme)
            # Set a new text to the label.
            self.current_default_theme_label.setText("Current default theme: {}".format(self.default_theme))

