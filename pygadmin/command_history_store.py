import copy
import logging
import os

import yaml

from pygadmin.configurator import global_app_configurator


class CommandHistoryStore:
    """
    Create a class for the administration of the command history. Previous SQL commands can be saved. A .yaml file is
    used for the persistent storage.
    """

    def __init__(self):
        # Define a path for the configuration files.
        configuration_path = os.path.join(os.path.expanduser("~"), '.pygadmin')

        # If the path for the configuration files does not exist, create it.
        if not os.path.exists(configuration_path):
            os.mkdir(configuration_path)

        # Define the file with the command history.
        self.yaml_command_history_file = os.path.join(configuration_path, "command_history.yaml")

        # Predefine a command history list as empty list.
        self.command_history_list = []

        # If the file does not exist, create it.
        if not os.path.exists(self.yaml_command_history_file):
            # Create the file as an empty file for writing in it.
            open(self.yaml_command_history_file, "a")

        # Get the current history out of the command file.
        self.get_command_history_from_yaml_file()
        # Get the current command limit as activation for a deletion process. If there are too many commands in the
        # history, delete the oldest ones, until the command limit is reached.
        self.get_new_command_limit()
        # Adjust the list to the current command limit.
        self.adjust_saved_history_to_new_command_limit()
        # Commit the current list to the yaml file.
        self.commit_current_list_to_yaml()

    def get_command_history_from_yaml_file(self):
        """
        Load the current history from the yaml file.
        """

        # Use a try statement in case of a broken .yaml file.
        try:
            # Use the read mode for getting the content of the file.
            with open(self.yaml_command_history_file, "r") as command_history_data:
                # Use the function for a safe load, because the file can be edited manually.
                self.command_history_list = yaml.safe_load(command_history_data)

                # If the list for the command history from the .yaml file is empty, it is None after a load. But for
                # preventing further errors, this if branch is used.
                if self.command_history_list is None:
                    # Set the connection parameters to an empty list.
                    self.command_history_list = []

                # Return a copy of the list as a result, so changes on the list like reversing do not have an effect to
                # the attribute.
                return copy.copy(self.command_history_list)

        except Exception as file_error:
            logging.error("The file {} cannot be opened and the command history cannot be loaded with the following "
                          "error: {}".format(self.yaml_command_history_file, file_error), exc_info=True)

    def commit_current_list_to_yaml(self):
        """
        Save the current command history list in a yaml file.
        """

        try:
            # Open the .yaml file in writing mode for dumping the data.
            with open(self.yaml_command_history_file, "w") as command_history_data:
                yaml.safe_dump(self.command_history_list, command_history_data)

                # Report the success.
                return True

        except Exception as file_error:
            logging.error("The file {} cannot be opened and the command history cannot be saved with the following "
                          "error: {}".format(self.yaml_command_history_file, file_error))

            # Report the failure.
            return False

    def save_command_history_in_yaml_file(self, new_command_dictionary):
        """
        Save a new command dictionary, so a new command with its meta data, in the command list. Check also for a
        command limit and delete the potential oldest element.
        """

        # Get all current commands in the history.
        self.get_command_history_from_yaml_file()
        # Add the new command to the list.
        self.command_history_list.append(new_command_dictionary)

        # Check for an existing command limit.
        if self.command_limit is not None:
            # If the length of the list is larger than the command limit, delete the oldest element.
            if len(self.command_history_list) > self.command_limit:
                # Delete the first element as oldest element.
                del self.command_history_list[0]

        # Commit the current list to the yaml file for saving it.
        self.commit_current_list_to_yaml()

    def delete_command_from_history(self, delete_command_dictionary):
        """
        Delete one command, specified in a command dictionary.
        """

        # Check for the existence of the command in the command history list.
        if delete_command_dictionary in self.command_history_list:
            # Delete the command after a match.
            self.command_history_list.remove(delete_command_dictionary)
            # Return the result of the saving in the yaml file.
            return self.commit_current_list_to_yaml()

        # Return False as failure.
        return False

    def delete_all_commands_from_history(self):
        """
        Delete all existing commands in the history.
        """

        # Define the command history list as empty list.
        self.command_history_list = []

        # Return the saving result for a success or a failure.
        return self.commit_current_list_to_yaml()

    def get_new_command_limit(self):
        """
        Get the new command limit out of the global app configurator.
        """

        self.command_limit = global_app_configurator.get_single_configuration("command_limit")

    def adjust_saved_history_to_new_command_limit(self):
        """
        Get a new command limit and delete the old commands, if there are old commands above the new limit.
        """

        # Get the new command limit.
        self.get_new_command_limit()

        # If the command limit is still None, end the function with a return.
        if self.command_limit is None:
            return

        # Get the number of overflow commands: The length of the list contains the number of commands and the command
        # limit is the number of valid commands.
        overflow_command_number = len(self.command_history_list) - self.command_limit

        # If there are overflow commands, the number of them is larger than 0.
        if overflow_command_number > 0:
            # Use a for loop for every overflow command.
            for command_number in range(overflow_command_number):
                # Delete the first element of the list: The first element is the oldest element, because there is always
                # an append process to the file and to the list.
                del self.command_history_list[0]


global_command_history_store = CommandHistoryStore()
