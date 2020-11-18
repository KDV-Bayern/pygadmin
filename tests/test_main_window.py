import sys
import unittest

from PyQt5.QtWidgets import QApplication, QMdiArea, QDockWidget, QMenuBar, QToolBar

from pygadmin.widgets.main_window import MainWindow
from pygadmin.widgets.connection_dialog import ConnectionDialogWidget
from pygadmin.widgets.configuration_settings import ConfigurationSettingsDialog
from pygadmin.widgets.editor_appearance_settings import EditorAppearanceSettingsDialog
from pygadmin.widgets.version_information_dialog import VersionInformationDialog
from pygadmin.configurator import global_app_configurator


class TestMainWindowMethods(unittest.TestCase):
    """
    Test the functionality and methods of the main window.
    """

    @staticmethod
    def set_opening_connection_dialog_to_false():
        """
        Set the configuration for opening a connection dialog at the start of the application/main window to False, so
        a connection dialog is not displayed.
        """

        global_app_configurator.set_single_configuration("open_connection_dialog_at_start", False)

    def test_initial_attributes(self):
        """
        Test the existence and correct instance of some initial attributes.
        """

        self.set_opening_connection_dialog_to_false()
        # Create an app, because this is necessary for testing a QMainWindow.
        app = QApplication(sys.argv)
        # Create a main window.
        main_window = MainWindow()

        # The MdiArea of the main window should be a QMdiArea.
        assert isinstance(main_window.mdi_area, QMdiArea)
        # The central widget should be the mdi area.
        assert main_window.centralWidget() == main_window.mdi_area
        # The sub window list of the mdi area should contain one item, because there is one editor at the start.
        assert len(main_window.mdi_area.subWindowList()) == 1

        # The dock widget should be a QDockWidget.
        assert isinstance(main_window.dock_widget, QDockWidget)

        # The menu bar should be a QMenuBar.
        assert isinstance(main_window.menu_bar, QMenuBar)
        # The tool bar should be a QToolBar.
        assert isinstance(main_window.tool_bar, QToolBar)

        # The status bar should show the message "Ready" at the start.
        assert main_window.statusBar().currentMessage() == "Ready"

    def test_add_action_to_menu_bar(self):
        """
        Test the correct appending of an action to the menu bar. In this case, the edit menu point is used.
        """

        self.set_opening_connection_dialog_to_false()
        # Create an app, because this is necessary for testing a QMainWindow.
        app = QApplication(sys.argv)
        # Create a main window.
        main_window = MainWindow()

        # Define a name for the new action.
        new_action_name = "test"

        # The name of the new action should not be the name of an existing action.
        for action in main_window.edit_menu.actions():
            assert action.text() != new_action_name

        # Add the action with the new name and a simple test function to the menu bar. Without a menu, the edit menu is
        # used.
        main_window.add_action_to_menu_bar(new_action_name, lambda: print("test"))

        # Check for an action with the name of the new action. The result should be one item, because there is one item
        # with the name of the new action: The new action.
        matching_action = [action.text() for action in main_window.edit_menu.actions()
                           if action.text() == new_action_name]

        # The list should contain one element.
        assert len(matching_action) == 1

    def test_add_action_to_tool_bar(self):
        """
        Test the correct appending of an action to the tool bar.
        """

        self.set_opening_connection_dialog_to_false()
        # Create an app, because this is necessary for testing a QMainWindow.
        app = QApplication(sys.argv)
        # Create a main window.
        main_window = MainWindow()

        # Define a name for the new action.
        new_action_name = "test"

        # The name of the new action should be unique, so there should not be an action with its text/name.
        for action in main_window.tool_bar.actions():
            assert new_action_name != action.text()

        # Add the new action to the tool bar. The path for the icon is an invalid test path and the function is only a
        # simple test function.
        main_window.add_action_to_tool_bar(new_action_name, "test_path", lambda: print("test"))

        # Check for an action with the name of the new action. The result should be one item, because there is one item
        # with the name of the new action: The new action.
        matching_action = [action.text() for action in main_window.tool_bar.actions()
                           if action.text() == new_action_name]

        # The resulting list should contain one element.
        assert len(matching_action) == 1

    def test_activate_new_connection_dialog(self):
        """
        Test the activation of a new connection dialog.
        """

        self.set_opening_connection_dialog_to_false()
        # Create an app, because this is necessary for testing a QMainWindow.
        app = QApplication(sys.argv)
        # Create a main window.
        main_window = MainWindow()

        # Activate a new connection dialog.
        main_window.activate_new_connection_dialog()
        # The new connection dialog should be a connection dialog.
        assert isinstance(main_window.new_connection_dialog, ConnectionDialogWidget)
        # The new connection dialog should be visible, because it is active.
        assert main_window.new_connection_dialog.isVisible() is True

    def test_activate_new_configuration_settings_dialog(self):
        """
        Test the activation of a new configuration settings dialog.
        """

        self.set_opening_connection_dialog_to_false()
        # Create an app, because this is necessary for testing a QMainWindow.
        app = QApplication(sys.argv)
        # Create a main window.
        main_window = MainWindow()

        # Activate a new configuration settings dialog.
        main_window.activate_new_configuration_settings_dialog()
        # The new dialog should have the correct type.
        assert isinstance(main_window.configuration_settings_dialog, ConfigurationSettingsDialog)
        # The dialog should be visible/active.
        assert main_window.configuration_settings_dialog.isVisible() is True

    def test_activate_new_editor_appearance_dialog(self):
        """"
        Test the activation of a new editor appearance dialog.
        """

        self.set_opening_connection_dialog_to_false()
        # Create an app, because this is necessary for testing a QMainWindow.
        app = QApplication(sys.argv)
        # Create a main window.
        main_window = MainWindow()

        # Activate a new editor appearance settings dialog.
        main_window.activate_new_editor_appearance_dialog()
        # The new dialog should have the correct type.
        assert isinstance(main_window.editor_appearance_dialog, EditorAppearanceSettingsDialog)
        # The dialog should be visible/active.
        assert main_window.editor_appearance_dialog.isVisible() is True

    def test_show_status_bar_message(self):
        """
        Test the function for showing a new status bar message.
        """

        self.set_opening_connection_dialog_to_false()
        # Create an app, because this is necessary for testing a QMainWindow.
        app = QApplication(sys.argv)
        # Create a main window.
        main_window = MainWindow()

        # Define a new message for the status bar.
        new_message = "test"
        # Set the message in the status bar.
        main_window.show_status_bar_message(new_message)
        # The status bar message should be the new message.
        assert main_window.statusBar().currentMessage() == new_message

    def test_show_version_information_dialog(self):
        """"
        Test the activation of a new version information dialog.
        """

        self.set_opening_connection_dialog_to_false()
        # Create an app, because this is necessary for testing a QMainWindow.
        app = QApplication(sys.argv)
        # Create a main window.
        main_window = MainWindow()

        # Show a new version information dialog.
        main_window.show_version_information_dialog()
        # The new dialog should have the correct type.
        assert isinstance(main_window.version_information_dialog, VersionInformationDialog)
        # The dialog should be visible/active.
        assert main_window.version_information_dialog.isVisible() is True

