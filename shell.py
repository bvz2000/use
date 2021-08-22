import sys

import bash
import display

LEGAL_SHELLS = [
    "bash",
]


# ======================================================================================================================
class Shell(object):

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self,
                 shell_type):
        """
        Initialize the object.

        :param shell_type: The type of shell (bash, tcsh, etc.) Currently only handles "bash".

        :return: Nothing.
        """

        if shell_type.lower() not in LEGAL_SHELLS:
            display.display_error("Unknown shell: " + sys.argv[1])
            display.display_usage()
            sys.exit(1)

        self.shell_type = shell_type.lower()

    # ------------------------------------------------------------------------------------------------------------------
    def format_alias(self,
                     alias_name,
                     alias_value) -> str:
        """
        Given an alias name and an alias value, returns a bash command to set that
        alias.

        :param alias_name: The name of the alias.
        :param alias_value: The value of the alias.

        :return: A string representing the bash command that would set this alias.
        """

        if self.shell_type == "bash":
            return bash.format_alias(alias_name, alias_value)

    # ------------------------------------------------------------------------------------------------------------------
    def format_env(self,
                   env_name,
                   env_value) -> str:
        """
        Given an environmental variable name and an environmental variable value,
        returns a bash command to set that environmental variable.

        :param env_name: The name of the environmental variable.
        :param env_value: The value of the environmental variable.

        :return: A string representing the bash command that would set this
                 environmental variable.
        """

        if self.shell_type == "bash":
            return bash.format_env(env_name, env_value)

    # ------------------------------------------------------------------------------------------------------------------
    def format_path_var(self,
                        path_var_name,
                        path_var_values) -> str:
        """
        Given a name of a path environmental variable and a list of paths to set for
        this variable, returns a bash command to set that path variable.

        :param path_var_name: The name of the path variable.
        :param path_var_values: A list of path to set for this path variable.

        :return: A string representing the bash command that would set this
                 path variable.
        """

        if self.shell_type == "bash":
            return bash.format_path_var(path_var_name, path_var_values)

    # ------------------------------------------------------------------------------------------------------------------
    def unset_env_var(self,
                      var_name):
        """
        Removes an env var..

        :param var_name: The name of the env var to unset

        :return: Nothing.
        """

        if self.shell_type == "bash":
            return bash.unset_env_var(var_name)

    # ------------------------------------------------------------------------------------------------------------------
    def unalias(self,
                alias_name):
        """
        Removes an alias..

        :param alias_name: The name of the alias to unset

        :return: Nothing.
        """

        if self.shell_type == "bash":
            return bash.unalias(alias_name)

    # ------------------------------------------------------------------------------------------------------------------
    def export_shell_command(self,
                             cmd):
        """
        Exports the command for the calling bash shell script to process. Fairly
        simple: It concatenates the list of commands using a semi-colon and then
        simply prints it to stdout.

        :param cmd: A list of shell commands to run. These will be concatenated
               with a ";"

        :return: Nothing.
        """

        if self.shell_type == "bash":
            bash.export_shell_command(cmd)
