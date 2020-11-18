import sys
import unittest

from PyQt5.QtWidgets import QApplication

from pygadmin.widgets.editor import EditorWidget
from pygadmin.widgets.search_replace_widget import SearchReplaceWidget


class TestSearchPlaceWidgetMethods(unittest.TestCase):
    """
    Test the functionality and methods of the search replace widget.
    """

    def test_initial_attributes(self):
        """
        Check for the correct existence and instance of the initial attributes of the search replace widget.
        """

        # Create an app, because this is necessary for testing a QWidget.
        app = QApplication(sys.argv)
        # Create an editor widget as parent for the search replace dialog.
        editor_widget = EditorWidget()
        # Create a search replace dialog with the editor widget as a parent
        search_replace_widget = SearchReplaceWidget(editor_widget)

        # The dictionaries with the search and replace items should exist as dictionaries.
        assert isinstance(search_replace_widget.search_items, dict)
        assert isinstance(search_replace_widget.replace_items, dict)

    def test_hide_replace_components(self):
        """
        Test the functionality of the method for hiding the replace components.
        """

        # Create an app, because this is necessary for testing a QWidget.
        app = QApplication(sys.argv)
        # Create an editor widget as parent for the search replace dialog.
        editor_widget = EditorWidget()
        # Create a search replace dialog with the editor widget as a parent
        search_replace_widget = SearchReplaceWidget(editor_widget)
        # Hide the replace components.
        search_replace_widget.hide_replace_components()

        # Check every component for hiding.
        for replace_item in search_replace_widget.replace_items.values():
            # The replace item should not be visible.
            assert replace_item.isVisible() is False

    def test_show_replace_components(self):
        """
        Test the method for showing the replace components.
        """

        # Create an app, because this is necessary for testing a QWidget.
        app = QApplication(sys.argv)
        # Create an editor widget as parent for the search replace dialog.
        editor_widget = EditorWidget()
        # Create a search replace dialog with the editor widget as a parent
        search_replace_widget = SearchReplaceWidget(editor_widget)
        # Show the replace components.
        search_replace_widget.show_replace_components()

        # Check every component for showing.
        for replace_item in search_replace_widget.replace_items.values():
            # The replace item should be visible.
            assert replace_item.isVisible() is True

    def test_set_search_text(self):
        """
        Test the method for setting the text of the search line edit.
        """

        # Create an app, because this is necessary for testing a QWidget.
        app = QApplication(sys.argv)
        # Create an editor widget as parent for the search replace dialog.
        editor_widget = EditorWidget()
        # Create a search replace dialog with the editor widget as a parent
        search_replace_widget = SearchReplaceWidget(editor_widget)
        # Define a text for testing.
        test_text = "Test"
        # Set the test text.
        search_replace_widget.set_search_text(test_text)
        # The test text should be the text of the line edit.
        assert search_replace_widget.search_items["search_line_edit"].text() == test_text

    def test_get_search_and_replace_text(self):
        """
        Test the method for getting the current text of the search and the replace line edit.
        """

        # Create an app, because this is necessary for testing a QWidget.
        app = QApplication(sys.argv)
        # Create an editor widget as parent for the search replace dialog.
        editor_widget = EditorWidget()
        # Create a search replace dialog with the editor widget as a parent
        search_replace_widget = SearchReplaceWidget(editor_widget)
        # Define a text for testing.
        test_text = "Test"

        # Set the text for testing as text of the search line edit.
        search_replace_widget.search_items["search_line_edit"].setText(test_text)
        # Now the method for getting the search text should return the test text.
        assert search_replace_widget.get_search_text() == test_text

        # Set the text for testing as text of the replace line edit.
        search_replace_widget.replace_items["replace_line_edit"].setText(test_text)
        # Now the method for getting the replace text should return the test text.
        assert search_replace_widget.get_replace_text() == test_text
