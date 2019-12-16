import sys


# ------------------------------------------------------------------------------
def display_error(*msgs):
    """
    Displays a message to the stdErr

    :param msgs: An arbitrary list of items to display. Each item will be
    converted to a string before being displayed. All items will be displayed on
    a single line.

    :return: Nothing.
    """

    message = ""
    for item in msgs:
        message += str(item) + " "
    print(message.strip(" "), file=sys.stderr)


# ------------------------------------------------------------------------------
def format_alias(alias_name,
                 alias_value):
    """
    Given an alias name and an alias value, returns a bash command to set that
    alias.

    :param alias_name: The name of the alias.
    :param alias_value: The value of the alias.

    :return: A string representing the bash command that would set this alias.
    """

    return "alias " + alias_name + "='" + alias_value + "'"


# ------------------------------------------------------------------------------
def format_env(env_name,
               env_value):
    """
    Given an environmental variable name and an environmental variable value,
    returns a bash command to set that environmental variable.

    :param env_name: The name of the environmental variable.
    :param env_value: The value of the environmental variable.

    :return: A string representing the bash command that would set this
             environmental variable.
    """

    return "export " + env_name + "=" + env_value


# ------------------------------------------------------------------------------
def format_path_var(path_var_name,
                    path_var_values):
    """
    Given a name of a path environmental variable and a list of paths to set for
    this variable, returns a bash command to set that path variable.

    :param path_var_name: The name of the path variable.
    :param path_var_values: A list of path to set for this path variable.

    :return: A string representing the bash command that would set this
             path variable.
    """

    output = ":".join(path_var_values)

    return "export " + path_var_name + "=" + output


# ------------------------------------------------------------------------------
def unset_env_var(var_name):
    """
    Removes an env var..

    :param var_name: The name of the env var to unset

    :return: Nothing.
    """

    output = "unset " + var_name

    return output


# ------------------------------------------------------------------------------
def unalias(alias_name):
    """
    Removes an alias..

    :param alias_name: The name of the alias to unset

    :return: Nothing.
    """

    output = "unalias " + alias_name

    return output


# ------------------------------------------------------------------------------
def export_shell_command(cmd):
    """
    Exports the command for the calling bash shell script to process. Fairly
    simple: It concatenates the list of commands using a semi-colon and then
    simply prints it to stdout.

    :param cmd: A list of shell commands to run. These will be concatenated
           with a ";"

    :return: Nothing.
    """

    output = ";".join(cmd)
    while ";;" in output:
        output = output.replace(";;", ";")

#     display_error(output.strip(";"))
    print(output.strip(";"))
