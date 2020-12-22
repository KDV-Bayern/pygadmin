import copy
import logging
import os
import yaml

from pygadmin.configurator import global_app_configurator


class FileManager:
    """"
    Create a class for administrating the open files in the editor tabs. This class saves the paths of the open tabs in
    a yaml file.
    """

    def __init__(self):
        # Define a container for the open files.
        self.open_files = []
        # Define a path for the configuration files.
        configuration_path = os.path.join(os.path.expanduser("~"), '.pygadmin')

        # If the path for the configuration files does not exist, create it.
        if not os.path.exists(configuration_path):
            os.mkdir(configuration_path)

        # Define a yaml file, which stores the current open files in the editor widgets, so it is independent from the
        # user's operating system.
        self.open_files_file = os.path.join(configuration_path, "open_files.yaml")

        # Check for the existence of the file.
        if not os.path.exists(self.open_files_file):
            # Create the file as an empty file for writing in it.
            open(self.open_files_file, "a")

        # If the current configuration is False, delete all current files, because a storage is not necessary.
        if global_app_configurator.get_single_configuration("open_previous_files") is False:
            self.delete_all_files()
            self.commit_current_files_to_yaml()

    def add_new_file(self, file_name):
        """
        Add a new file with its name/path to the list of open files.
        """

        self.open_files.append(file_name)

        return True

    def delete_file(self, file_name):
        """
        Delete a file with its name/path.
        """

        # Check for the existence of the file.
        if file_name not in self.open_files:
            # If the file does not exist, return False for a failure.
            return False

        # Remove the file name.
        self.open_files.remove(file_name)

        # Return True for a success.
        return True

    def delete_all_files(self):
        """
        Delete all current open files with overwriting the current content of the open files list with an empty list.
        """

        self.open_files = []

    def commit_current_files_to_yaml(self):
        """
        Try to save the current list in the yaml file.
        """

        try:
            # Try to open the file in writing mode.
            with open(self.open_files_file, "w") as file_data:
                # Use a safe dump, because the file can be manually edited by a user.
                yaml.safe_dump(self.open_files, file_data)

                # Return True for a success.
                return True

        # Use the exception during the writing process for an error message.
        except Exception as file_error:
            logging.error("The file {} cannot be opened and the open files in the editor cannot be saved with the "
                          "following error: {}".format(self.open_files_file, file_error), exc_info=True)

            # Return False for a failure.
            return False

    def load_open_file_list(self):
        """
        Load the content of the open files out of the yaml file. Use a try statement for a potential failure of the file
        reading process.
        """

        # Use a try statement in case of a broken .yaml file.
        try:
            # Use the read mode for getting the content of the file.
            with open(self.open_files_file, "r") as file_data:
                # Use the function for a safe load, because the file can be edited manually.
                self.open_files = yaml.safe_load(file_data)

                # If the list with the open files out of the .yaml file is empty, it is None after a load. But for
                # preventing further errors, because a list is expected, this if branch is used.
                if self.open_files is None:
                    # Define the list of open files as an empty list.
                    self.open_files = []

                # Return a copy of the list, so there is no manipulation from the outside.
                return copy.copy(self.open_files)

        except Exception as file_error:
            logging.error("The file {} cannot be opened previous open files cannot be loaded with the following "
                          "error: {}".format(self.open_files_file, file_error), exc_info=True)


global_file_manager = FileManager()
