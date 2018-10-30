#!/usr/bin/env python

import ast
import configparser
import os
import sys
import tempfile

LEGAL_COMMANDS = [
    "complete",
    "config",
    "processStdIn",
    "setup",
    "unuse",
    "use",
    "used",
    "which",
]
LEGAL_PERMISSIONS = [644, 744, 754, 755, 654, 655, 645]
ENFORCE_PERMISSIONS = False
DISPLAY_PERMISSIONS_VIOLATIONS = False
DEFAULT_USE_PKG_PATHS = ["/opt/use", "/home/bvz/Documents/dev/use/"]


# ------------------------------------------------------------------------------
def export_stdin():
    """
    Takes the StdIn exports it to StdOut as a python list.

    :return: Nothing.
    """

    export_shell_command(str(sys.stdin))


# ------------------------------------------------------------------------------
def display_usage():
    """
    Prints the usage string. Note: because most of the output of this script is
    intended to be processed by a calling shell script using 'eval', the usage
    string will be printed to stdErr to prevent it from being processed as a
    command.

    :return: Nothing.
    """

    display_error("Usage")


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
def export_shell_command(cmd):
    """
    Exports the command for the calling bash shell script to process. Pretty
    simple, it just prints the command.

    :param cmd: The command to pass back to the calling shell script.

    :return: Nothing.
    """

    # Pretty easy, just print it to stdOut.
    print(cmd)


# ------------------------------------------------------------------------------
def validate_permissions(path, legal_shell_permission_bits):
    """
    Given a file name, verifies that the file is matches the permissions passed
    by a list given in shellPermissionBitsL.

    :param path: A path to the file to be validates.
    :param legal_shell_permission_bits: A list of permissions that are allowed.
           These should be passed as a list of integers exactly as they would be
           used in a shell 'chmod' command. For example: 644

    :return: True if the file matches any of the passed permission bits.  False
             otherwise.
    """

    # Contract
    assert(os.path.exists(path))
    assert(not(os.path.isdir(path)))
    assert(type(legal_shell_permission_bits) is list)

    # Verify that the file is owned by root and is only writable by root.
    if os.stat(path).st_uid != 0:
        return False

    if int(oct(os.stat(path).st_mode)[-3:]) not in legal_shell_permission_bits:
        return False

    return True


# ------------------------------------------------------------------------------
def handle_permission_violation(file_name):
    """
    Handles a permission violation for a particular file. Normally we just
    display an error message and exit. But during development this is
    burdensome. So in that case, we might want to either display the error but
    not exit, or not even display an error.

    :param file_name: The name of the file that violated the permissions.

    :return: Nothing.
    """

    if DISPLAY_PERMISSIONS_VIOLATIONS:
        display_error(
            file_name,
            " must be owned by root and only writable by root. Exiting.")
    if ENFORCE_PERMISSIONS:
        sys.exit(1)


# ------------------------------------------------------------------------------
def complete(stub, search_paths):
    """
    Given a stub, collects all of the use packages that start with this text.
    Exports these items to stdOut as a newline-delimited string.

    This is the corresponding bash function needed to provide tab completion
    using this feature:
    _funcName () {
        local files=`./thisScript.py complete "${COMP_WORDS[$COMP_CWORD]}"`
        COMPREPLY=( ${files[@]} )
    }

    :param stub: The characters we are matching
    :param search_paths: The paths where use packages might live

    :return: Nothing
    """

    outputs = list()
    use_pkgs = list_all_use_pkg_files(search_paths)
    for use_pkg in use_pkgs:
        if use_pkg.startswith(stub):
            output = os.path.splitext(use_pkg)[0]
            outputs.append(output)
    export_shell_command("\n".join(outputs))


# ------------------------------------------------------------------------------
def list_all_use_pkg_files(search_paths):
    """
    Returns a list of all use packages anywhere in the passed search_paths.

    :param search_paths: A list of paths where the use packages could live.

    :return: A list of use package names (deduplicated)
    """

    use_pkg_files = list()
    for searchPath in search_paths:
        file_names = os.listdir(searchPath)
        for fileName in file_names:
            if fileName.endswith(".use"):
                use_pkg_files.append(fileName)
    return list(set(use_pkg_files))


# ------------------------------------------------------------------------------
def list_matching_use_pkg_files(use_pkg_name, search_paths):
    """
    Given a use_pkg_name, tries to find matching "use_pkg_name.use" files
    in search_paths. Returns a list of full paths to these files, resolving any
    symlinks along the way. Returns an empty list if no files match this pattern
    anywhere in the searchPaths.

    :param use_pkg_name: The base name of the use package. I.e. "clarisse"
           if you were looking for "clarisse-3.6sp5.use"
    :param search_paths: A list of paths where the use packages could live.

    :return: A list of full paths to (resolved) use package files that match
             this name. Empty if no matches.
    """

    use_pkg_files = list()
    for search_path in search_paths:
        use_pkg = os.path.join(search_path, use_pkg_name + ".use")
        if os.path.exists(use_pkg):
            use_pkg_files.append(os.path.realpath(use_pkg))

    return use_pkg_files


# ------------------------------------------------------------------------------
def get_use_pkg_file(use_pkg_name, search_paths):
    """
    Given a specific use_pkg_name, returns the first one it can find among
    all that may match this name.

    :param use_pkg_name: The name of the use package.
    :param search_paths: All the paths where this use package might live.

    :return: A full path to the use package file on disk.
    """

    # Find the use package file from this use package name
    use_pkg_files = list_matching_use_pkg_files(use_pkg_name, search_paths)
    if not use_pkg_files:
        display_error("Cannot find", use_pkg_name, "in", str(search_paths))
        sys.exit(1)
    if len(use_pkg_files) > 1:
        display_error("More than one use package matches this name. Using:",
                      use_pkg_files[0])
    return use_pkg_files[0]


# ------------------------------------------------------------------------------
def verify_read_use_pkg(use_pkg_file):
    """
    Opens a use package file (given by use_pkg_file). Verifies the package's
    permissions first. Returns the use package as a configparser object twice.
    Once delimited by '=', once undelimited.

    :param use_pkg_file: The full path to the use package file.

    :return: Tuple of config objects, the first elem is a configparser object
             delimited by '=', the second is undelimited.
    """

    # Verify the security of this file
    if not validate_permissions(use_pkg_file, LEGAL_PERMISSIONS):
        handle_permission_violation(use_pkg_file)

    # Read this use package file (both delimited and undelimited)
    delimited_use_pkg_obj = read_use_pkg(use_pkg_file, "=")
    undelimited_use_pkg_obj = read_use_pkg(use_pkg_file, "\n")

    # Return both
    return delimited_use_pkg_obj, undelimited_use_pkg_obj


# ------------------------------------------------------------------------------
def use_get_aliases(use_pkg_obj):
    """
    Generates the alias commands.

    :param use_pkg_obj: The '=' delimited use package object.

    :return: A string containing the bash shell command to set the alias'.
    """

    aliases = get_use_aliases(use_pkg_obj)
    aliases = reformat_key_value_tuples_with_quotes(aliases)
    alias = ";".join(["alias " + item for item in aliases])
    return alias


# ------------------------------------------------------------------------------
def use_get_existing_aliases(use_pkg_obj):
    """
    For the alias' listed in the use_pkg_obj, get a list of their current
    values. Return this as a dictionary.

    :param use_pkg_obj: The '=' delimited use package object.

    :return: A dictionary of key/value pairs for each alias. If an alias is
             undefined, then the value will be blank.
    """

    # Create a dict to store the existing alias'
    outputs = dict()

    # Get the newly defined alias'
    aliases = get_use_aliases(use_pkg_obj)

    # For each of these alias' try to find that same value in the current shell
    for aliasT in aliases:

        # Check to see if the alias already exists
        alias_name = aliasT[0]
        try:
            alias_value = os.environ[alias_name]
        except KeyError:
            alias_value = ""

        # Add that alias to the dict
        outputs[alias_name] = alias_value

    return outputs


# ------------------------------------------------------------------------------
def use_env(use_pkg_obj):
    """
    Generates the environmental variables.

    :param use_pkg_obj: The '=' delimited use package object.

    :return: A string containing the bash shell command to set the env
             variables.
    """

    env_vars = reformat_key_value_tuples(get_use_env_vars(use_pkg_obj))
    env = ";".join(["export " + item for item in env_vars])
    return env


# ------------------------------------------------------------------------------
def use_path(use_pkg_obj):
    """
    Generates a new PATH variable with the prepend items prepended to the
    beginning and the postpend items appended to the end (removes them from the
    rest of PATH if they already exist).

    :param use_pkg_obj: The undelimited use package object.

    :return: A string containing the bash shell command to set the PATH env
             variable.
    """

    path_prepends = get_use_path_prepends(use_pkg_obj)
    path_postpends = get_use_path_postpends(use_pkg_obj)
    existing_path = os.environ["PATH"]

    # Remove the prepend paths if they are already in the PATH
    for pathPrepend in path_prepends:
        existing_path = existing_path.replace(pathPrepend, "")

    # Remove the postpend paths if they are already in the PATH
    for pathPostpend in path_postpends:
        existing_path = existing_path.replace(pathPostpend, "")

    # Add each prepend to the PATH
    for pathPrepend in path_prepends:
        existing_path = pathPrepend + ":" + existing_path

    # Add each postpend to the PATH
    for pathPostpend in path_postpends:
        existing_path = existing_path + ":" + pathPostpend

    # Remove any doubled up : symbols
    while "::" in existing_path:
        existing_path = existing_path.replace("::", ":")

    return "PATH=" + existing_path


# ------------------------------------------------------------------------------
def use_cmds(use_pkg_obj):
    """
    Generates the free-form bash commands.

    :param use_pkg_obj: The undelimited use package object.

    :return: A string containing the raw bash shell commands read from the use
             package file.
    """

    cmds = get_use_bash_cmds(use_pkg_obj)
    cmd = ";".join([item for item in cmds])
    return cmd


# ------------------------------------------------------------------------------
def use(use_pkg_name, search_paths, aliases):
    """
    Uses a new package (given by use_pkg_name). Processes this file and exports
    the contents converted into bash commands.

    :param use_pkg_name: A name of the use package (not the file name, just
           the package name. (Eg: clarisse-3.6sp2, and not clarisse-3.6sp2.use).
    :param search_paths: A list of paths where the use package might live.
    :param aliases: A python list of the existing alias' in the current shell.

    :return: Nothing
    """

    # Find the use package file from this use package name
    use_pkg_file = get_use_pkg_file(use_pkg_name, search_paths)

    # Read this use package file (both delimited and undelimited)
    use_obj_delim, use_obj_undelim = verify_read_use_pkg(use_pkg_file)

    # Extract the data from the package file and reformat it into a series of
    # bash shell commands
    bash_cmd = ""
    bash_cmd += use_get_aliases(use_obj_delim) + ";"
    bash_cmd += use_env(use_obj_delim) + ";"
    bash_cmd += use_path(use_obj_undelim) + ";"
    bash_cmd += use_cmds(use_obj_undelim)
    while ";;" in bash_cmd:
        bash_cmd.replace(";;", ";")

    display_error(use_get_existing_aliases(use_obj_delim))

    # Write out the history
    write_history(use_pkg_name, use_obj_delim, use_obj_undelim, aliases)

    # Export the bash command
    export_shell_command(bash_cmd)


# ------------------------------------------------------------------------------
def read_use_pkg(use_pkg_file, *delimiters):
    """
    Reads in the contents of a use package and returns it in the form of a
    configparser object (.ini file)

    :param use_pkg_file: The use package to read.
    :param delimiters: A list of different delimiters to use. If empty, then the
           default of "\n" will be used.

    :return: A configparser object.
    """

    if not delimiters:
        delimiters = tuple("\n")

    use_pkg_obj = configparser.ConfigParser(allow_no_value=True,
                                            delimiters=delimiters)

    # Force configparser to maintain capitalization of keys
    use_pkg_obj.optionxform = str
    use_pkg_obj.read(use_pkg_file)

    return use_pkg_obj


# ------------------------------------------------------------------------------
def get_use_aliases(use_pkg_obj):
    """
    Returns all of the alias commands from the useConfig

    :param use_pkg_obj: The config parser object.

    :return: Nothing
    """

    try:
        return use_pkg_obj.items("alias")
    except configparser.NoSectionError:
        return []


# ------------------------------------------------------------------------------
def get_use_env_vars(use_pkg_obj):
    """
    Returns all of the environment variable settings from the useConfig

    :param use_pkg_obj: The config parser object.

    :return: Nothing
    """

    try:
        return use_pkg_obj.items("env")
    except configparser.NoSectionError:
        return []


# ------------------------------------------------------------------------------
def get_use_path_prepends(use_pkg_obj):
    """
    Returns the paths to prepend to $PATH from the useConfig

    :param use_pkg_obj: The config parser object. This should be one that is
           read without delimiters

    :return: Nothing
    """

    try:
        return reformat_no_value_tuples(use_pkg_obj.items("path-prepend"))
    except (configparser.NoSectionError, configparser.NoOptionError):
        return []


# ------------------------------------------------------------------------------
def get_use_path_postpends(use_pkg_obj):
    """
    Returns the paths to postpend to $PATH from the useConfig

    :param use_pkg_obj: The config parser object. This should be one that is
           read without delimiters

    :return: A list containing all of the lines in the path-postpend section.
    """

    try:
        return reformat_no_value_tuples(use_pkg_obj.items("path-postpend"))
    except (configparser.NoSectionError, configparser.NoOptionError):
        return []


# ------------------------------------------------------------------------------
def get_use_bash_cmds(use_pkg_obj):
    """
    Returns any additional shell commands to run from the useConfig

    :param use_pkg_obj: The config parser object. This should be one that is
           read without delimiters

    :return: A list containing all of the lines in the cmds section
    """

    try:
        return reformat_no_value_tuples(use_pkg_obj.items("cmds"))
    except configparser.NoSectionError:
        return []


# ------------------------------------------------------------------------------
def write_history(use_pkg_file, use_obj_delim, use_obj_undelim, aliases):
    """
    Writes the current use command to the temp history file.

    :param use_pkg_file: The full name of the use package.
    :param use_obj_delim: A configparser object of the use package, delimited
           by '='.
    :param use_obj_undelim: A configparser object of the use package, delimited
           by "\n".
    :param aliases: A list of all the alias' in the current shell.

    :return: Nothing
    """

    # Make sure the history file exists and that we can find it
    try:
        history_file = os.environ["USE_HISTORY_FILE"]
    except KeyError:
        display_error("No history file. Did you forget to run setup first?")
        sys.exit(1)
    if not os.path.exists(history_file):
        display_error("History file",
                      history_file,
                      "does not exist. Did setup fail?")
        sys.exit(1)

    # Build the history dict
    outputs = dict()
    outputs["use_pkg_file"] = use_pkg_file
    outputs["alias"] = get_use_aliases(use_obj_delim)
    outputs["env"] = get_use_env_vars(use_obj_delim)
    outputs["path-prepend"] = get_use_path_prepends(use_obj_undelim)
    outputs["path-postpend"] = get_use_path_postpends(use_obj_undelim)
    outputs["cmds"] = get_use_bash_cmds(use_obj_undelim)

    display_error(aliases)

    # Open the history command for appending and write out the history string
    f = open(history_file, "a")
    f.write(str(outputs) + "\n")
    f.close()


# ------------------------------------------------------------------------------
def reformat_key_value_tuples_with_quotes(key_values):
    """
    Given a list of tuples, returns a list of strings with key=value pairs.
    Returns the value in quotes (as required by the bash alias command).

    :param key_values: The list of key/value tuples

    :return: A list of strings of key=value pairs where the value is enclosed in
             quotes (as required by the bash alias command).
    """

    outputs = list()
    for item in key_values:
        outputs.append(item[0] + '="' + item[1] + '"')
    return outputs


# ------------------------------------------------------------------------------
def reformat_key_value_tuples(key_values):
    """
    Given a list of tuples, returns a list of strings with key=value pairs.

    :param key_values: The list of key/value tuples

    :return: A list of strings of key=value pairs.
    """

    outputs = list()
    for item in key_values:
        outputs.append(item[0] + "=" + item[1])
    return outputs


# ------------------------------------------------------------------------------
def reformat_no_value_tuples(key_values):
    """
    When reading a section that has a simple list (i.e. just text without
    delimiters or key/value pairs), configparser loads the data in a list of
    tuples where the second element in the tuple is empty. This reconstructs
    this into a list of strings to match how a normal key/value section is
    presented.

    :param key_values: The list of key/value tuples to reconstruct.

    :return: A list of strings.
    """

    outputs = list()
    for item in key_values:
        outputs.append(item[0])
    return outputs


# ------------------------------------------------------------------------------
def used():
    """
    Reads the history file and returns a list of all used packages in the
    current shell.

    :return: Nothing.
    """

    # Open the history file
    try:
        use_history_file = os.environ["USE_HISTORY_FILE"]
    except KeyError:
        display_error("Unable to locate a use history file")
        sys.exit(1)

    # Read in the whole file into a single list
    f = open(use_history_file, "r")
    lines = f.readlines()
    f.close()

    # Step through the list and convert it to
    used_pkg_names = list()
    for line in lines:
        used_pkg_names.append(ast.literal_eval(line)["usePkgName"])

    # Remove duplicates
    used_pkg_names = list(set(used_pkg_names))
    used_pkg_names.sort()

    # Export the shell command to display these items
    export_shell_command('printf "' + r'\n'.join(used_pkg_names) + r'\n' + '"')


# ------------------------------------------------------------------------------
def setup():
    """
    Does the setup for the current shell. Needs to be run once per shell before
    the system is usable.

    :return: An environmental variable USE_HISTORY_FILE with a path to a text
             file that contains the history of use commands for the current
             session.
    """

    # Check to see if there is already a use history file for this shell.
    # Create one if needed.
    try:
        use_history_file = os.environ["USE_HISTORY_FILE"]
    except KeyError:
        f, use_history_file = tempfile.mkstemp(suffix=".usehistory", text=True)

    # Store this file name in the form of an environmental variable.
    output = "export USE_HISTORY_FILE=" + use_history_file

    # Read in the existing USE_PKG_PATH
    try:
        use_pkg_path = os.environ["USE_PKG_PATH"]
    except KeyError:
        use_pkg_path = ":".join(DEFAULT_USE_PKG_PATHS)

    # Convert it into a list
    use_pkg_paths = use_pkg_path.split(":")

    legal_path_found = False
    for path in use_pkg_paths:
        if os.path.exists(path) and os.path.isdir(path):
            legal_path_found = True

    if not legal_path_found:
        display_error("No use package directory found. I looked for:",
                      ":".join(use_pkg_paths))
        sys.exit(1)

    # Store the use package paths
    output += ";export USE_PKG_PATH=" + ":".join(use_pkg_paths)

    # Export these env variables.
    export_shell_command(output)


# ==============================================================================
# ==============================================================================
if __name__ == "__main__":

    # Make sure this script is owned by root and only writable by root.
    # TODO: Wrap this to check for assertion error
    if not validate_permissions(os.path.abspath(__file__), LEGAL_PERMISSIONS):
        handle_permission_violation(os.path.abspath(__file__))

    # Only handle specific types of requests
    if sys.argv[1] not in LEGAL_COMMANDS:
        display_error("Unknown command.")
        display_usage()

    # SETUP
    # ===========================
    if sys.argv[1] == "setup":
        setup()
        sys.exit(0)

    # Read some system-wide env variables (this MUST come after we run setup)
    try:
        env_use_pkg_path = os.environ["USE_PKG_PATH"]
    except KeyError:
        display_error("Missing USE_PKG_PATH env variable (where use packages "
                      "live). Exiting.")
        sys.exit(1)
    if ":" in env_use_pkg_path:
        use_pkg_search_paths = env_use_pkg_path.split(":")
    else:
        use_pkg_search_paths = [env_use_pkg_path]

    # ===========================
    if sys.argv[1] == "complete":
        complete(sys.argv[2], use_pkg_search_paths)

    # ===========================
    if sys.argv[1] == "use":
        use(sys.argv[3], use_pkg_search_paths, ast.literal_eval(sys.argv[2]))

    # ===========================
    if sys.argv[1] == "used":
        used()

    # ===========================
    if sys.argv[1] == "unuse":
        pass

    # ===========================
    if sys.argv[1] == "processStdIn":
        export_stdin()
