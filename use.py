#!/usr/bin/env python

import ast
import configparser
import os
import re
import sys
import tempfile

LEGAL_COMMANDS = [
    "complete_unuse",
    "complete_use",
    "config",
    "package_from_branch",
    "setup",
    "unuse",
    "use",
    "used",
    "which",
    "update_latest",
]
LEGAL_PERMISSIONS = [644, 744, 754, 755, 654, 655, 645]
ENFORCE_PERMISSIONS = False
DISPLAY_PERMISSIONS_VIOLATIONS = False
DEFAULT_USE_PKG_PATHS = ["/opt/use", os.path.expanduser("/Documents/dev/use/")]


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
def list_all_use_pkg_files(search_paths):
    """
    Returns a list of all use packages anywhere in the passed search_paths.

    :param search_paths: A list of paths where the use packages could live.

    :return: A list of use package names (de-duplicated)
    """

    use_pkg_files = list()
    for searchPath in search_paths:
        if os.path.exists(searchPath) and os.path.isdir(searchPath):
            file_names = os.listdir(searchPath)
            for fileName in file_names:
                if fileName.endswith(".use"):
                    use_pkg_files.append(fileName)
    return list(set(use_pkg_files))


# ------------------------------------------------------------------------------
def complete_use(stub, search_paths):
    """
    Given a stub, collects all of the use packages that start with this text.
    Exports these items to stdOut as a newline-delimited string.

    This is the corresponding bash function needed to provide tab completion
    using this feature:
    _funcName () {
        local files=`./thisScript.py complete_use "${COMP_WORDS[$COMP_CWORD]}"`
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
def complete_unuse(stub):
    """
    Given a stub, collects all of the use packages that have already been used
    that start with this stub.

    This is the corresponding bash function needed to provide tab completion
    using this feature:
    _funcName () {
        local pkgs=`./thisScript.py complete_unuse "${COMP_WORDS[$COMP_CWORD]}"`
        COMPREPLY=( ${pkgs[@]} )
    }

    :param stub: The characters we are matching

    :return: Nothing
    """

    outputs = list()
    use_pkgs = get_used()
    for use_pkg in use_pkgs:
        if use_pkg.startswith(stub):
            outputs.append(use_pkg)
    export_shell_command("\n".join(outputs))


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
def verify_and_read_use_pkg(use_pkg_file):
    """
    Opens a use package file (given by use_pkg_file). Verifies the package's
    permissions first. Returns the use package as a configparser object twice.
    Once delimited by '=', once undelimited.

    :param use_pkg_file: The full path to the use package file.

    :return: Tuple of config objects, the first elem is a configparser object
             delimited by '=', the second is undelimited (technically it is
             delimited by '\n', but that is effectively the same as being
             undelimited).
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
def format_existing_aliases(raw_aliases):
    """
    Given a list of strings containing the alias definitions, formats it into
    a list of key/value tuples.

    :param raw_aliases: A string containing all of the current aliases.

    :return: A list of key/value tuples.
    """

    # Convert the stdin to a list of existing aliases
    existing_aliases = list()
    for existing_alias in list(raw_aliases):
        existing_aliases.append(existing_alias.rstrip("\n"))

    # Reformat the existing aliases to be a list of key/value tuples
    # (this makes it match the format that the other data is stored in as well)
    existing_aliases = reformat_existing_aliases(existing_aliases)

    return existing_aliases


# ------------------------------------------------------------------------------
def get_branches(use_pkg_obj):
    """
    Returns all of the branches from the use_pkg_obj.

    :param use_pkg_obj: The config parser object, undelimited.

    :return: A list of key/value tuples containing all of the branches.
    """

    try:
        return use_pkg_obj.items("branch")
    except configparser.NoSectionError:
        return []


# ------------------------------------------------------------------------------
def get_aliases(use_pkg_obj):
    """
    Returns all of the alias commands from the use_pkg_obj.

    :param use_pkg_obj: The config parser object, delimited.

    :return: A list of key/value tuples containing all of the aliases.
    """

    try:
        return use_pkg_obj.items("alias")
    except configparser.NoSectionError:
        return []


# ------------------------------------------------------------------------------
def get_env_vars(use_pkg_obj):
    """
    Returns all of the environment variable settings from the use_pkg_obj.

    :param use_pkg_obj: The config parser object, delimited.

    :return: A list of key/value tuples containing all of the env vars.
    """

    try:
        return use_pkg_obj.items("env")
    except configparser.NoSectionError:
        return []


# ------------------------------------------------------------------------------
def get_path_prepends(use_pkg_obj):
    """
    Returns the paths to prepend to $PATH from the use_pkg_obj.

    :param use_pkg_obj: The config parser object, undelimited.

    :return: A list of key/value tuples containing all of the path prepends.
    """

    try:
        return use_pkg_obj.items("path-prepend")
    except (configparser.NoSectionError, configparser.NoOptionError):
        return []


# ------------------------------------------------------------------------------
def get_path_postpends(use_pkg_obj):
    """
    Returns the paths to postpend to $PATH from the use_pkg_obj.

    :param use_pkg_obj: The config parser object, undelimited.

    :return: A list of key/value tuples containing all of the path postpends.
    """

    try:
        return use_pkg_obj.items("path-postpend")
    except (configparser.NoSectionError, configparser.NoOptionError):
        return []


# ------------------------------------------------------------------------------
def get_bash_cmds(use_pkg_obj):
    """
    Returns any additional shell commands to run from the use_pkg_obj.

    :param use_pkg_obj: The config parser object, undelimited.

    :return: A list of key/value tuples containing all of the bash commands.
    """

    try:
        return use_pkg_obj.items("cmds")
    except configparser.NoSectionError:
        return []


# ------------------------------------------------------------------------------
def get_unuse(use_pkg_obj):
    """
    Returns all of the unuse commands from the use_pkg_obj.

    :param use_pkg_obj: The config parser object, undelimited.

    :return: A list of key/value tuples containing all of the unuse commands.
    """

    try:
        return use_pkg_obj.items("unuse")
    except configparser.NoSectionError:
        return []


# ------------------------------------------------------------------------------
def format_aliases_for_shell(aliases):
    """
    Formats the aliases that are read directly from the config object as a
    string ready for the bash shell.

    :param aliases: A list of key/value tuples that contain the aliases.

    :return: A string containing the bash shell command to set the aliases.
    """

    output = ""
    for alias in aliases:
        output += "alias "
        output += alias[0]
        output += "="
        output += "'" + alias[1] + "';"

    return output.rstrip(";")


# ------------------------------------------------------------------------------
def format_env_vars_for_shell(env_vars):
    """
    Generates the environmental variables.

    :param env_vars: A list of key/value tuples that contain the env vars.

    :return: A string containing the bash shell command to set the env
             variables.
    """

    output = ""
    for env_var in env_vars:
        output += "export "
        output += env_var[0]
        output += "="
        output += "'" + env_var[1] + "';"

    return output.rstrip(";")


# ------------------------------------------------------------------------------
def format_path_for_shell(path_prepends, path_postpends):
    """
    Generates a new PATH variable with the prepend items prepended to the
    beginning and the postpend items appended to the end (removes them from the
    rest of PATH if they already exist).

    :param path_prepends: A list of key/value tuples that contain the path
           prepends. Only element [0] of the tuple is useful.
    :param path_postpends: A list of key/value tuples that contain the path
           postpends. Only element [0] of the tuple is useful.

    :return: A string containing the bash shell command to set the PATH env
             variable.
    """

    existing_path = os.environ["PATH"]

    # Remove the prepend paths if they are already in the PATH
    for path_prepend in path_prepends:
        existing_path = existing_path.replace(path_prepend[0], "")

    # Remove the postpend paths if they are already in the PATH
    for path_postpend in path_postpends:
        existing_path = existing_path.replace(path_postpend[0], "")

    # Add each prepend to the PATH
    for path_prepend in path_prepends:
        existing_path = path_prepend[0] + ":" + existing_path

    # Add each postpend to the PATH
    for path_postpend in path_postpends:
        existing_path = existing_path + ":" + path_postpend[0]

    # Remove any doubled up : symbols
    while "::" in existing_path:
        existing_path = existing_path.replace("::", ":")

    return "PATH=" + existing_path


# ------------------------------------------------------------------------------
def format_cmds_for_shell(cmds):
    """
    Generates the free-form bash commands.

    :param cmds: A list of key/value tuples that contain the commands.

    :return: A string containing the raw bash shell commands read from the use
             package file.
    """

    output = ""
    for cmd in cmds:
        output += cmd[0] + "';"

    return output.rstrip(";")


# ------------------------------------------------------------------------------
def reformat_existing_aliases(existing_aliases):
    """
    Takes in a list of the raw alias strings and reformats them to be a list of
    key/value tuples.

    :param existing_aliases: A list of raw strings for each alias.

    :return: A list of key/value tuples where the key is the alias name and the
             value is the alias definition.
    """

    reformatted_aliases = list()

    pattern = r"(alias )(.*)(=)(.*)"
    for existing_alias in existing_aliases:
        match_obj = re.match(pattern, existing_alias)
        if match_obj is not None:
            reformatted_aliases.append((match_obj[2], match_obj[4].strip("'")))

    return reformatted_aliases


# ------------------------------------------------------------------------------
def get_matching_aliases(new_aliases, existing_aliases):
    """
    Given a list of new aliases and existing aliases, returns a list of existing
    aliases that are also in new_aliases.

    :param new_aliases: A list of key/value tuples that contain the new aliases.
    :param existing_aliases: A list of key/value tuples that contain the
           existing aliases.

    :return: A list of key/value pairs of the existing aliases for those aliases
             that also exist in new_aliases.
    """

    matching = list()

    # Build a list of the new alias names
    new_alias_names = list()
    for new_alias in new_aliases:
        new_alias_names.append(new_alias[0])

    for existing_alias in existing_aliases:
        if existing_alias[0] in new_alias_names:
            matching.append(existing_alias)

    return matching


# ------------------------------------------------------------------------------
def get_matching_env_vars(new_env_vars):
    """
    For the env vars listed in the use_pkg_obj, get a list of their current
    values. Returns a list of key/value tuples.

    :param new_env_vars: A list of key/value tuples containing the new env vars
           to be set.

    :return: A list of key/value pairs for each env var that exists in the
             current shell that is being modified by the use package.
    """

    matching_env_vars = list()
    for new_env_var in new_env_vars:
        new_env_var_name = new_env_var[0]
        try:
            existing_var_value = os.environ[new_env_var_name]
        except KeyError:
            existing_var_value = False
        if existing_var_value:
            matching_env_vars.append((new_env_var_name, existing_var_value))

    return matching_env_vars


# ------------------------------------------------------------------------------
def get_existing_path():
    """
    Extracts the existing value of $PATH from the calling shell.

    :return: The current path string.
    """

    if "PATH" in os.environ.keys():
        return os.environ["PATH"]
    else:
        return ""


# ------------------------------------------------------------------------------
def write_history(use_pkg_file, branches, new_aliases, new_env_vars,
                  new_path_prepends, new_path_postpends, cmds, existing_aliases,
                  existing_env_vars, existing_path, unuse_cmds):
    """
    Writes the actions being taken by the current use package to a temp history
    file. Also includes any existing aliases, env vars, and paths that may be
    modified in the process.

    :param use_pkg_file: The full name of the use package.
    :param branches: A list of key/value tuples listing the branches for this
           use package.
    :param new_aliases: A list of key/value tuples listing the aliases being set
           in this use package.
    :param new_env_vars: A list of key/value tuples listing the env vars being
           set in this use package.
    :param new_path_prepends: A list of key/value tuples listing the new path
           prepends in this use package.
    :param new_path_postpends: A list of key/value tuples listing the new path
           postpends in this use package.
    :param cmds: A list of key/value tuples listing the bash shell commands
           being run by this use package.
    :param existing_aliases: A list of key/value tuples listing the existing
           aliases that will be overwritten by the new aliases in this use
           package.
    :param existing_env_vars: A list of key/value tuples listing the existing
           env vars that will be overwritten by the new env vars in this use
           package.
    :param existing_path: The existing path.
    :param unuse_cmds: A list of key/value tuples listing the bash shell
           commands to be run when doing an unuse of this use package.

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

    # All history is stored as a dictionary
    history = dict()

    history["use_package"] = use_pkg_file
    history["branches"] = branches
    history["new_aliases"] = new_aliases
    history["new_env_vars"] = new_env_vars
    history["new_path_prepends"] = new_path_prepends
    history["new_path_postpends"] = new_path_postpends
    history["cmds"] = cmds
    history["existing_aliases"] = existing_aliases
    history["existing_env_vars"] = existing_env_vars
    history["existing_path"] = existing_path
    history["unuse"] = unuse_cmds

    # Open the history command for appending and write out the history string
    f = open(history_file, "a")
    f.write(str(history) + "\n")
    f.close()


# ------------------------------------------------------------------------------
def use(use_pkg_name, search_paths, raw_aliases):
    """
    Uses a new package (given by use_pkg_name). Processes this file and exports
    the contents converted into bash commands.

    :param use_pkg_name: A name of the use package (not the file name, just
           the package name. (Eg: clarisse-3.6sp2, and not clarisse-3.6sp2.use).
    :param search_paths: A list of paths where the use package might live.
    :param raw_aliases: The contents of the stdin.

    :return: Nothing
    """

    # Find the use package file from this use package name
    use_pkg_file = get_use_pkg_file(use_pkg_name, search_paths)

    # Read this use package file (both delimited and undelimited)
    use_obj_delim, use_obj_undelim = verify_and_read_use_pkg(use_pkg_file)

    # Extract the various bits of data we need from this config
    branches = get_branches(use_obj_undelim)
    aliases = get_aliases(use_obj_delim)
    env_vars = get_env_vars(use_obj_delim)
    path_prepends = get_path_prepends(use_obj_undelim)
    path_postpends = get_path_postpends(use_obj_undelim)
    cmds = get_bash_cmds(use_obj_undelim)
    unuse_cmds = get_unuse(use_obj_undelim)
    #
    # # Find the last used package in this branch and unuse it
    # prev_use_pkg = get_use_pkg_name_from_branch()
    # if prev_use_pkg is not None:
    #     unuse(prev_use_pkg, stdin)

    # Extract the data from the package file and reformat it into a series of
    # bash shell commands that will be passed back as a single, semi-colon
    # delimited command.
    bash_cmd = ""
    bash_cmd += format_aliases_for_shell(aliases) + ";"
    bash_cmd += format_env_vars_for_shell(env_vars) + ";"
    bash_cmd += format_path_for_shell(path_prepends, path_postpends) + ";"
    bash_cmd += format_cmds_for_shell(cmds)
    while ";;" in bash_cmd:
        bash_cmd.replace(";;", ";")

    # Reformat the existing aliases to be a list of key/value tuples
    # (this makes it match the format that the other data is stored in as well)
    existing_aliases = format_existing_aliases(raw_aliases)

    # Get a list of aliases in the current shell that match those being reset
    matched_aliases = get_matching_aliases(aliases, existing_aliases)

    # Get a list of env vars in the current shell that match those being reset
    matched_env_vars = get_matching_env_vars(env_vars)

    # Get the existing path
    existing_path = get_existing_path()

    # Write out the history
    write_history(use_pkg_name, branches, aliases, env_vars, path_prepends,
                  path_postpends, path_postpends, matched_aliases,
                  matched_env_vars, existing_path, unuse_cmds)

    # Export the bash command
    export_shell_command(bash_cmd)


# ------------------------------------------------------------------------------
def read_history(history_file):
    """
    Reads in the history file given by history_file.

    :param history_file: The full path to the file to be read.

    :return: A list of dictionary objects containing the contents of the history
             file.
    """

    f = open(history_file, "r")
    lines = f.readlines()
    f.close()

    history = list()
    for line in lines:
        history.append(ast.literal_eval(line))

    return history


# ------------------------------------------------------------------------------
def remove_history(history_file, remove_line):
    """
    Reads in the history file given by history_file, finds the line that matches
    the remove_line line, and then writes history back out without this line.

    :param history_file: The full path to the file to be read.
    :param remove_line: The line that is to be removed.

    :return: Nothing.
    """

    f = open(history_file, "r")
    lines = f.readlines()
    f.close()

    history = list()
    for line in lines:
        if line != remove_line + "\n":
            history.append(line)

    f = open(history_file, "w")
    for line in history:
        f.write(line)
    f.close()


# ------------------------------------------------------------------------------
def get_used():
    """
    Reads the history file and returns a list of all used packages in the
    current shell.

    :return: A list of used package names.
    """

    # Open the history file
    try:
        use_history_file = os.environ["USE_HISTORY_FILE"]
    except KeyError:
        display_error("Unable to locate a use history file")
        sys.exit(1)

    # Read in the whole file into a single list
    history = read_history(use_history_file)

    # Step through the list and convert it to
    used_pkg_names = list()
    for item in history:
        used_pkg_names.append(item["use_package"])

    # Remove duplicates
    used_pkg_names = list(set(used_pkg_names))
    used_pkg_names.sort()

    return used_pkg_names


# ------------------------------------------------------------------------------
def used():
    """
    Reads the history file and returns a list of all used packages in the
    current shell.

    :return: Nothing.
    """

    used_pkg_names = get_used()

    # Export the shell command to display these items
    export_shell_command('printf "' + r'\n'.join(used_pkg_names) + r'\n' + '"')


# ------------------------------------------------------------------------------
def get_use_pkg_name_from_branch(use_pkg_name, search_paths):
    """
    Given a use package name, extracts the branch and uses that to find the most
    recent use package in the history that is in this same branch.

    :param use_pkg_name: The name of the use package.
    :param search_paths: A list of paths where the use package might live.

    :return: The name of the most recent use package in the history that matches
             these branches.
    """

    # Find the use package file from this use package name
    use_pkg_file = get_use_pkg_file(use_pkg_name, search_paths)

    # Read this use package file (both delimited and undelimited)
    use_obj_delim, use_obj_undelim = verify_and_read_use_pkg(use_pkg_file)

    # Extract the various bits of data we need from this config
    branches = get_branches(use_obj_undelim)
    branches = [item[0] for item in branches]

    # Open the history file
    try:
        use_history_file = os.environ["USE_HISTORY_FILE"]
    except KeyError:
        display_error("Unable to locate a use history file")
        sys.exit(1)

    # Read in the whole file into a single list
    history = read_history(use_history_file)

    # Step through the list backwards till we find the last used package that
    # matches any one of the branches
    for history_item in reversed(range(len(history))):
        history_branches = history[history_item]["branches"]
        history_branches = [item[0] for item in history_branches]
        for history_branch in history_branches:
            if history_branch in branches:
                use_pkg_name = history[history_item]["use_package"]
                export_shell_command(use_pkg_name)
                return
    export_shell_command("")


# ------------------------------------------------------------------------------
def unuse_aliases(aliases, old_aliases, raw_aliases):
    """
    Undoes the aliases defined in aliases. It follows the following logic:

    If the alias does not exist in the current shell, then something has
    actively removed this alias. We do not want to override this decision, so do
    nothing.

    If the alias still exists in the current shell but is different than the
    value set by the use package, then something has actively changed it since
    we ran the use command. We do not want to override this decision, so do
    nothing.

    If the alias still exists in the current shell but is the same as the
    value set by the use package, then nothing has actively changed it since
    we ran the use command. We should then consider the following two options:

    If the alias did not exist prior to us running the use package, we should
    unset this alias so that it no longer exists.

    If the alias did exist prior to us running the use package, then we should
    reset this alias to that value.

    :param aliases: A list of key/value tuples of the aliases set by the use
           package.
    :param old_aliases: A list of key/value tuples of the aliases that were
           in place when the use package was invoked.
    :param raw_aliases: The stdIn that contains the aliases as they exist in the
           current shell.

    :return: A string of semi-colon separated commands to either reset or
             unset the aliases that were set by the use command.
    """

    output = ""

    # Format the existing aliases into key/value tuples
    existing_aliases = format_existing_aliases(raw_aliases)

    # Step through each of the aliases that were set by the use package we are
    # now un-using.
    for alias in aliases:

        # Find the matching alias in the current aliases (if it exists)
        existing_alias = tuple()
        for item in existing_aliases:
            if alias[0] == item[0]:
                existing_alias = item
                break

        # Find the matching alias in the aliases that existed prior to the use
        # package changing it.
        old_alias = tuple()
        for item in old_aliases:
            if alias[0] == item[0]:
                old_alias = item
                break

        # If the alias does not exist in the current shell, do nothing.
        if not existing_alias:
            continue

        # If the alias still exists in the current shell and is different from
        # what was set by the use package, do nothing.
        if existing_alias != () and alias[1] != existing_alias[1]:
            continue

        # If we get here, then the alias exists in the current shell and is
        # identical to the value set by the use package.

        # If the alias does not exist in the old_aliases, unset the alias.
        if not old_alias:
            output += "unalias " + alias[0] + ";"
            continue

        # If the alias does exist in the old_aliases, reset the alias to that
        # value.
        output += "alias " + alias[0] + "='" + old_alias[1] + "';"

    # remove any doubled up semi-colons, and remove trailing colons
    while ";;" in output:
        output = output.replace(";;", ";")
    output = output.rstrip(";")

    return output


# ------------------------------------------------------------------------------
def unuse_env_vars(env_vars, old_env_vars):
    """
    Undoes the env_vars defined in env_vars. It follows the following logic:

    If the env var does not exist in the current shell, then something has
    actively removed this var. We do not want to override this decision, so do
    nothing.

    If the env var still exists in the current shell but is different than the
    value set by the use package, then something has actively changed it since
    we ran the use command. We do not want to override this decision, so do
    nothing.

    If the env var still exists in the current shell but is the same as the
    value set by the use package, then nothing has actively changed it since
    we ran the use command. We should then consider the following two options:

    If the env var did not exist prior to us running the use package, we should
    delete this env var so that it no longer exists.

    If the env var did exist prior to us running the use package, then we should
    reset this env var to that value.

    :param env_vars: A list of key/value tuples of the env vars set by the use
           package.
    :param old_env_vars: A list of key/value tuples of the env vars that were
           in place when the use package was invoked.

    :return: A string of semi-colon separated commands to either reset or
             delete the env vars that were set by the use command.
    """

    output = ""

    # Step through each of the aliases that were set by the use package we are
    # now un-using.
    for env_var in env_vars:

        # Find the matching env_var in the current env vars (if it exists)
        existing_env_var = tuple()
        for item in os.environ.keys():
            if env_var[0] == item:
                existing_env_var = (item, os.environ[item])
                break

        # Find the matching env_var in the aliases that existed prior to the use
        # package changing it.
        old_env_var = tuple()
        for item in old_env_vars:
            if env_var[0] == item[0]:
                old_env_var = item
                break

        # If the env_var does not exist in the current shell, do nothing.
        if not existing_env_var:
            continue

        # If the env_var still exists in the current shell and is different from
        # what was set by the use package, do nothing.
        if existing_env_var != () and env_var[1] != existing_env_var[1]:
            continue

        # If we get here, then the env_var exists in the current shell and is
        # identical to the value set by the use package.

        # If the env_var does not exist in the old_aliases, delete the env_var.
        if not old_env_var:
            output += "unset " + env_var[0] + ";"
            continue

        # If the env_var does exist in the old_env_vars, reset the env_var to
        # that value.
        output += "export " + env_var[0] + "=" + old_env_var[1] + ";"

    # remove any doubled up semi-colons, and remove trailing colons
    while ";;" in output:
        output = output.replace(";;", ";")
    output = output.rstrip(";")

    return output


# ------------------------------------------------------------------------------
def unuse_path(path_prepends, path_postpends, old_path, history):
    """
    Removes any additions to the path that may have been created by the use
    command. The basic rules are as follows:

    First check to see if the path_prepend and path_postpend already existed
    before the use command was run. If so, don't do anything.

    Look through the remaining history and see if any other use commands have
    added any of the same path_prepends or path_postpends. If they have not,
    then feel free to remove these from the current path, but only if they also
    did not exist in the old_path.

    :param path_prepends: The list of path_prepends set by the use package
    :param path_postpends: The list of path_postpends set by the use package
    :param old_path: The string containing the PATH prior to the use package
    :param history: The history of use commands since the use package

    :return: A string containing the bash command that sets the PATH variable.
    """

    try:
        existing_paths = os.environ["PATH"].split(":")
    except KeyError:
        display_error("$PATH does not exist as an environmental variable.")
        sys.exit(1)

    # Convert the old path into a list.
    old_path = old_path.split(":")

    # Build a list of subsequent path_prepends and path_postpends.
    subsequent_history_paths = list()
    for history_item in history:
        subsequent_history_paths.append(history_item["new_path_prepends"])
        subsequent_history_paths.append(history_item["new_path_postpends"])

    # Build a list of paths to remove.
    paths_to_remove = list()

    # Process each path in path_prepends
    for path in path_prepends:

        path = path[0]

        # If path is blank, do nothing
        if path == "":
            continue

        # Do not remove any paths that were in the path prior to use.
        if path in old_path:
            continue

        # Do not remove any paths that were in the subsequent use packages.
        if path in subsequent_history_paths:
            continue

        # If we get this far, add this path to the list to be extracted.
        paths_to_remove.append(path)

    # Process each path in path_postpends
    for path in path_postpends:

        path = path[0]

        # If path is blank, do nothing
        if path == "":
            continue

        # Do not remove any paths that were in the path prior to use.
        if path in old_path:
            continue

        # Do not remove any paths that were in the subsequent use packages.
        if path in subsequent_history_paths:
            continue

        # If we get this far, add this path to the list to be extracted.
        paths_to_remove.append(path)

    # Remove the paths
    for path_to_remove in paths_to_remove:
        existing_paths.remove(path_to_remove)

    # Create the bash command
    return "export PATH=" + ":".join(existing_paths).rstrip(":")


# ------------------------------------------------------------------------------
def unuse_unuse_cmds(cmds):
    """
    Runs the free-form unuse commands from the use package.

    :param cmds: The free-form commands in the use package "cmds" section.

    :return: A series of bash formatted commands separated by semi-colons.
    """

    output = ""
    for cmd in cmds:
        output += cmd[0] + "';"

    return output.rstrip(";")


# ------------------------------------------------------------------------------
def unuse(use_pkg_name, raw_aliases):
    """
    Given a use_pkg_name this will find the most recent version in the history
    file and try to undo whatever that use command did (but being aware not to
    step on any similar commands that have been run since that time).

    :param use_pkg_name: The name of the use package we are un-using.
    :param raw_aliases: The list of raw alias strings.

    :return: Nothing.
    """

    # Open the history file
    try:
        use_history_file = os.environ["USE_HISTORY_FILE"]
    except KeyError:
        display_error("Unable to locate a use history file")
        sys.exit(1)

    # Read in the whole file into a single list
    history = read_history(use_history_file)

    # Step through the list backwards till we find the last used package
    unuse_pkg = None
    for history_item in reversed(range(len(history))):
        if history[history_item]["use_package"] == use_pkg_name:
            unuse_pkg = history[history_item]
            history = history[history_item+1:]
            break

    if unuse_pkg is None:
        return

    # Load in the changes made by this use package
    aliases = unuse_pkg["new_aliases"]
    env_vars = unuse_pkg["new_env_vars"]
    path_prepends = unuse_pkg["new_path_prepends"]
    path_postpends = unuse_pkg["new_path_postpends"]
    existing_aliases = unuse_pkg["existing_aliases"]
    existing_env_vars = unuse_pkg["existing_env_vars"]
    existing_path = unuse_pkg["existing_path"]
    cmds = unuse_pkg["unuse"]

    # Try to undo the aliases, env_vars, and path.
    unuse_aliases_cmd = unuse_aliases(aliases, existing_aliases, raw_aliases)
    unuse_aliases_cmd += ";"
    unuse_aliases_cmd += unuse_env_vars(env_vars, existing_env_vars)
    unuse_aliases_cmd += ";"
    unuse_aliases_cmd += unuse_path(path_prepends, path_postpends,
                                    existing_path, history)
    unuse_aliases_cmd += ";"
    unuse_aliases_cmd += unuse_unuse_cmds(cmds)

    # Remove this line from the use history
    remove_history(use_history_file, str(unuse_pkg))

    # Export the shell command to display these items
    export_shell_command(str(unuse_aliases_cmd).rstrip(";"))


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


# ------------------------------------------------------------------------------
def update_latest(search_paths):
    """
    Goes through the use package directory and makes sure that every file has
    a latest. For example, if there are two files:

    blender-2.79.use and blender-2.80.use

    this function will find the newest of the two and create a symlink called
    blender-latest.use that points to the newest (presumably blender-2.80.use,
    though it is based on file modification date, not name).

    :return: Nothing.
    """

    use_pkgs = list()
    for search_path in search_paths:
        if not os.path.exists(search_path) or not os.path.isdir(search_path):
            continue

        items = os.listdir(search_path)
        for item in items:
            if item.endswith(".use"):
                if not os.path.isdir(item):
                    if not os.path.islink(item):
                        use_pkgs.append(item)

        if not use_pkgs:
            continue

        use_prefixes = dict()
        for use_pkg in use_pkgs:
            prefix = use_pkg.split("-")[0]
            if prefix not in use_prefixes.keys():
                use_prefixes[prefix] = [use_pkg]
            else:
                use_prefixes[prefix].append(use_pkg)

        for prefix in use_prefixes.keys():

            # Find the most recently modified use package for each prefix
            latest = use_prefixes[list(use_prefixes.keys())[0]]
            max_time = 0
            for item in use_prefixes[prefix]:
                mod_date = os.path.getmtime(os.path.join(search_path, item))
                if mod_date > max_time:
                    latest = os.path.join(search_path, item)
                    max_time = mod_date

            # Get rid of the existing symlink if needed
            link = str(prefix) + "-latest.use"
            if os.path.exists(os.path.join(search_path, link)):
                os.unlink(os.path.join(search_path, link))

            # Make a symlink
            os.symlink(latest,
                       os.path.join(search_path, str(prefix) + "-latest.use"))


# ==============================================================================
# ==============================================================================
if __name__ == "__main__":

    # Make sure this script is owned by root and only writable by root.
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
    if sys.argv[1] == "update_latest":
        update_latest(use_pkg_search_paths)

    # ===========================
    if sys.argv[1] == "complete_use":
        complete_use(sys.argv[2], use_pkg_search_paths)

    # ===========================
    if sys.argv[1] == "complete_unuse":
        complete_unuse(sys.argv[2])

    # ===========================
    if sys.argv[1] == "package_from_branch":
        if len(sys.argv) != 3:
            display_error("package_from_branch: Wrong number of arguments.")
            sys.exit(1)
        get_use_pkg_name_from_branch(sys.argv[2], use_pkg_search_paths)

    # ===========================
    if sys.argv[1] == "use":
        if len(sys.argv) != 3:
            display_error("use: Wrong number of arguments.")
            sys.exit(1)
        stdin = list(sys.stdin)
        use(sys.argv[2], use_pkg_search_paths, stdin)

    # ===========================
    if sys.argv[1] == "used":
        used()

    # ===========================
    if sys.argv[1] == "unuse":
        stdin = list(sys.stdin)
        if len(sys.argv) > 2:
            unuse(sys.argv[2], stdin)
