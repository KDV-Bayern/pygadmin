import unittest
import os

from pygadmin.command_history_store import global_command_history_store
from pygadmin.configurator import global_app_configurator


class TestCommandHistoryStoreMethods(unittest.TestCase):
    """
    Test the command history store with its method and its behavior.
    """

    def test_path_of_command_history_file(self):
        """
        Check for the existence of the yaml file, which stores the command history.
        """

        assert os.path.exists(global_command_history_store.yaml_command_history_file)

    def test_command_history_list(self):
        """
        Test the existence and the correct type of the command history list.
        """

        assert isinstance(global_command_history_store.command_history_list, list)

    def test_get_command_history_from_yaml_file(self):
        """
        Test the behavior of the method for getting the current command history from the yaml file.
        """

        # Get the current list.
        command_history_list = global_command_history_store.get_command_history_from_yaml_file()
        # The result of the method should be the current data list of the command history store.
        assert command_history_list == global_command_history_store.command_history_list

    def test_commit_current_list_to_yaml(self):
        """
        Test the correct commit of the current list to the yaml file.
        """

        # Ensure the correct load of all previous commands in the history.
        global_command_history_store.get_command_history_from_yaml_file()
        # The result of committing should be True for a success.
        assert global_command_history_store.commit_current_list_to_yaml() is True

    def test_save_command_history_in_yaml_file(self):
        """
        Test the function for saving one specific command in the command history.
        """

        # Define a dictionary with a command and the information about it.
        command_dictionary = {"Command": "SELECT * FROM test;",
                              "Identifier": "testuser@testserver:5432/testdb",
                              "Time": "2020-10-01 11:53:59",
                              "Result": [["column 0", "column 1", "column 2"], ["row A", "row B", "row C"],
                                         ["row D", "row E", "row F"]]}

        # Save the command dictionary in the yaml file.
        global_command_history_store.save_command_history_in_yaml_file(command_dictionary)
        # Now the dictionary should be part of the command history list.
        assert command_dictionary in global_command_history_store.command_history_list

        # Clean up, so the testing command is no longer part of the command history store.
        global_command_history_store.delete_command_from_history(command_dictionary)

    def test_delete_command_from_history(self):
        """
        Test the deletion of a command from the history.
        """

        # Define a dictionary with a command and the information about it.
        command_dictionary = {"Command": "SELECT * FROM test;",
                              "Identifier": "testuser@testserver:5432/testdb",
                              "Time": "2020-10-01 11:53:59",
                              "Result": [["column 0", "column 1", "column 2"], ["row A", "row B", "row C"],
                                         ["row D", "row E", "row F"]]}

        # Save the command dictionary in the yaml file.
        global_command_history_store.save_command_history_in_yaml_file(command_dictionary)

        # The deletion of the dictionary should return True as a success.
        assert global_command_history_store.delete_command_from_history(command_dictionary) is True
        # A second try with the same dictionary should return False, because the dictionary is already deleted and can
        # not be found.
        assert global_command_history_store.delete_command_from_history(command_dictionary) is False

    def test_delete_all_commands_from_history(self):
        """
        Test the deletion of the complete history.
        """

        # Get the current command history for saving it again later.
        current_command_history = global_command_history_store.get_command_history_from_yaml_file()

        # The deletion of the whole history should be successful.
        assert global_command_history_store.delete_all_commands_from_history() is True
        assert global_command_history_store.command_history_list == []

        # Set the previous saved list as command history list for restoring the correct list.
        global_command_history_store.command_history_list = current_command_history
        # Save the correct list in the yaml file.
        global_command_history_store.commit_current_list_to_yaml()

    def test_get_new_command_limit(self):
        """
        Test the method for getting the new command limit in the command history store.
        """

        # Define a command limit.
        command_limit = 100
        # Set the command limit in the global app configurator.
        global_app_configurator.set_single_configuration("command_limit", command_limit)
        global_app_configurator.save_configuration_data()

        # Get the new command limit as attribute of the class.
        global_command_history_store.get_new_command_limit()

        # The command limit of the global history store should be the command limit, which was set before.
        assert global_command_history_store.command_limit == command_limit

    def test_adjust_saved_history_to_new_command_limit(self):
        """
        Test the method for adjusting an existing list of commands in the history to a new command limit.
        """

        # Define a previous command limit.
        old_command_limit = 100
        # Set the command limit in the global app configurator.
        global_app_configurator.set_single_configuration("command_limit", old_command_limit)
        global_app_configurator.save_configuration_data()

        # Define a new command limit.
        command_limit = 10

        # Add new command dictionaries to the command history.
        for command_number in range(command_limit + 2):
            # Define a unique command dictionary.
            command_dictionary = {"Command": "{}".format(command_number),
                                  "Identifier": "testuser@testserver:5432/testdb",
                                  "Time": "2020-10-01 11:53:{}".format(command_number),
                                  "Result": [["column 0", "column 1", "column 2"], ["row A", "row B", "row C"],
                                             ["row D", "row E", "row F"]]}

            # Save the unique command dictionary in the command history store.
            global_command_history_store.save_command_history_in_yaml_file(command_dictionary)

        # Set the command limit in the global app configurator.
        global_app_configurator.set_single_configuration("command_limit", command_limit)
        global_app_configurator.save_configuration_data()

        # Use the function for adjusting the saved history to the new command list and commit the new list to the yaml
        # file.
        global_command_history_store.adjust_saved_history_to_new_command_limit()
        global_command_history_store.commit_current_list_to_yaml()

        # The length of the list should be the command limit.
        assert len(global_command_history_store.command_history_list) == command_limit

        # Define a test command dictionary. This dictionary was inserted before, but it was too old, so it should be
        # deleted.
        test_command_dictionary = {"Command": "1",
                                   "Identifier": "testuser@testserver:5432/testdb",
                                   "Time": "2020-10-01 11:53:1",
                                   "Result": [["column 0", "column 1", "column 2"], ["row A", "row B", "row C"],
                                              ["row D", "row E", "row F"]]}

        # The test dictionary should not be part of the command history list, because it is deleted.
        assert test_command_dictionary not in global_command_history_store.command_history_list
