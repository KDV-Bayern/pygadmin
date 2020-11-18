import sys
import unittest

from PyQt5.QtWidgets import QApplication

from pygadmin.widgets.editor_appearance_settings import EditorAppearanceSettingsDialog
from pygadmin.configurator import global_app_configurator


class TestEditorAppearanceSettingsDialogMethods(unittest.TestCase):
    """
    Test the functionality and methods of the editor appearance settings dialog.
    """

    def test_initial_attributes(self):
        """
        Test the existence and correct instance of some initial attributes.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create an editor appearance settings dialog.
        settings_dialog = EditorAppearanceSettingsDialog()

        # Check for the dictionary with the GUI items.
        assert isinstance(settings_dialog.color_items_dictionary, dict)
        # Check for the dictionary with the currently existing color themes.
        assert isinstance(settings_dialog.current_color_themes_dictionary, dict)

    def test_set_selected_item_in_list_widget(self):
        """
        Test the method for selecting a theme with the given name.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create an editor appearance settings dialog.
        settings_dialog = EditorAppearanceSettingsDialog()

        # The theme "Hack" should be available as hard coded theme in the global app configurator.
        item_to_select = "Hack"
        # Select the item in the settings dialog.
        settings_dialog.set_selected_item_in_list_widget(item_to_select)
        # Get the selected item out of the list of selected items.
        selected_item = settings_dialog.current_themes_list_widget.selectedItems()[0]
        # The item to selected and the text of the selected item should be the same.
        assert item_to_select == selected_item.text()

    def test_get_selected_item_in_list_widget(self):
        """
        Test the function for getting the selected item of the list widget as attribute of the dialog.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create an editor appearance settings dialog.
        settings_dialog = EditorAppearanceSettingsDialog()

        # Clear the selection of the settings dialog. If there is a default theme, the default theme is selected.
        settings_dialog.current_themes_list_widget.selectionModel().clearSelection()

        # After clearing the selection, the method for getting the selected item should return False, because there is
        # no selected item.
        assert settings_dialog.get_selected_item_in_list_widget() is False
        # The selected list widget item should be None, because there is no selection.
        assert settings_dialog.selected_list_widget_item is None

        # Choose an item for selecting.
        item_to_select = "Hack"
        # Set the selected item in the list widget.
        settings_dialog.set_selected_item_in_list_widget(item_to_select)

        # Now there should be a selected item in the list widget, so the function returns True.
        assert settings_dialog.get_selected_item_in_list_widget() is True
        # The selected item in the list widget should be the item to select.
        assert settings_dialog.selected_list_widget_item == item_to_select

    def test_save_changes_in_configuration_and_apply(self):
        """
        Test the function for changing the current saves.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create an editor appearance settings dialog.
        settings_dialog = EditorAppearanceSettingsDialog()

        # The function should return True for a successful save.
        assert settings_dialog.save_changes_in_configuration_and_apply() is True

    def test_set_default_theme(self):
        """
        Test the method for setting a new default theme.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create an editor appearance settings dialog.
        settings_dialog = EditorAppearanceSettingsDialog()

        # Choose an item for selecting.
        item_to_select = "Hack"
        # Set the selected item in the list widget.
        settings_dialog.set_selected_item_in_list_widget(item_to_select)

        # Set the default theme. The selected theme is now the default theme.
        settings_dialog.set_default_theme()

        # The default theme in the settings dialog should be saved in the global app configurator.
        assert settings_dialog.default_theme == global_app_configurator.get_single_configuration("color_theme")
