import abc


class SearchReplaceParent(abc.ABC):
    """
    Create an interface with the methods, which are necessary for a widget as parent of the search replace widget.
    """

    @abc.abstractmethod
    def deactivate_search_next_and_replace_buttons_and_deselect(self):
        """
        Create a function for deactivating the search and replace buttons of the widget.
        """

        pass

    @abc.abstractmethod
    def search_and_select_sub_string(self):
        """
        Create a method for searching and selection a sub string.
        """

        pass

    @abc.abstractmethod
    def search_and_select_next_sub_string(self):
        """
        Create a method for searching and selecting the following/next sub string.
        """

        pass

    @abc.abstractmethod
    def close_search_replace_widget(self):
        """
        Create a method for closing the search/replace widget.
        """

        pass

    @abc.abstractmethod
    def check_for_replace_enabling(self):
        """
        Create a method for checking the enabling of the replace buttons.
        """

        pass

    @abc.abstractmethod
    def replace_current_selection(self):
        """
        Create a method for replacing the current selection.
        """

        pass

    @abc.abstractmethod
    def replace_all_sub_string_matches(self):
        """
        Create a method for replacing all sub string matches.
        """

        pass
