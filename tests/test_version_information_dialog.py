import sys
import unittest

from PyQt5.QtWidgets import QApplication, QLabel

from pygadmin.widgets.version_information_dialog import VersionInformationDialog


class TestVersionInformationDialogMethods(unittest.TestCase):
    """
    Test the methods and behavior of the version information dialog.
    """

    def test_initial_attributes(self):
        """
        Test the initial attributes of the dialog.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a version information dialog.
        version_information_dialog = VersionInformationDialog()

        # The dialog should not be modal.
        assert version_information_dialog.isModal() is False
        # The version label should be a QLabel.
        assert isinstance(version_information_dialog.version_label, QLabel)
