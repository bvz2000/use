#!/usr/bin/env python

import ast
import configparser
import os
import sys
import tempfile
import time

LEGAL_COMMANDS = [
    "complete_unuse",
    "complete_use",
    "config",
    "setup",
    "refresh",
    "unuse",
    "unuse_package_from_use_package",
    "use",
    "used",
    "which",
    "symlink_latest",
    "update_desktop",
    "test",
]

# A list of legal permissions for use packages (those that do not have one of
# these permissions will not be allowed to run for security purposes)
LEGAL_PERMISSIONS = [644, 744, 754, 755, 654, 655, 645]

# Whether to enforce these permissions. Should almost always be set to False
# when doing development. Whether to set these to True for actual production is
# up to your sense of comfort. The idea behind setting restrictive permissions
# is that this system will call arbitrary commands that may be invisible to the
# end user if they are not actively examining the .use files and checking the
# provenance of any scripts that these arbitrary commands have.
#
# That said, if someone has compromised your system and installed user-level
# malicious code, you probably have bigger problems than having this system
# execute this code. Still, the best practice would be to enable all of the
# permission checking.
#
# There are three options:
# Enforce app permissions means this use.py file must be owned by root and only
# writable by root.
# Enforce use pkg permissions means that any use packages must be owned by root
# and only writable by root.
# Enforce called script permissions means that any scripts called by a use
# package must be owned by root and only writable by root.
ENFORCE_APP_PERMISSIONS = False
ENFORCE_USE_PKG_PERMISSIONS = False
ENFORCE_CALLED_SCRIPT_PERMISSIONS = True

# Show errors for use packages or files that do not meet the permissions
# requirements, or simply ignore them silently.
DISPLAY_PERMISSIONS_VIOLATIONS = True

# This is an offset that indicates where the version number is in the path
# (relative to the use package). So, for example, if the path to a use package
# is:
#   /opt/apps/isotropix/clarisse/3.6sp7/wrapper/clarisse.use
# then the relative path offset is -2 (i.e. parent dir is -1, grandparent dir is
# -2, and so on). The values do not have to be negative as only the absolute
# value is used. The value may not be zero. The name of the directory specified
# will be used in its entirety as the version number, but it does not have to
# actually be a number. Any text can be used. For example: "2" is a valid
# version number, but so is "3.6sp7", or even "latest". This setting can be
# overridden by using an env variable set below.
DEFAULT_AUTO_VERSION_OFFSET = 2

# Where to look for auto version use packages. This setting can be overridden by
# using an env variable set below.
DEFAULT_USE_PKG_AV_PATHS = "/opt/apps/"

# Where to look for baked version use packages. This setting can be overridden
# by using an env variable set below.
DEFAULT_USE_PKG_BV_PATHS = "/opt/use/"

# Whether to search sub-directories of the use package paths. This setting can
# be overridden by using an env variable set below.
DEFAULT_DO_RECURSIVE_SEARCH = True

# Env variables (some of which might contain settings that will override the
# above settings)
USE_PKG_AVAILABLE_PACKAGES_ENV = "USE_PKG_PACKAGES"
USE_PKG_AV_SEARCH_PATHS_ENV = "USE_PKG_AUTO_VER_SEARCH_PATHS"
USE_PKG_BV_SEARCH_PATHS_ENV = "USE_PKG_BAKED_VER_SEARCH_PATHS"
USE_PKG_SEARCH_RECURSIVE_ENV = "USE_PKG_SEARCH_RECURSIVE"
USE_PKG_HISTORY_FILE_ENV = "USE_PKG_HISTORY_FILE"
USE_PKG_AUTO_VERSION_ENV = "USE_PKG_AUTO_VERSION"
USE_PKG_AUTO_VERSION_OFFSET_ENV = "USE_PKG_AUTO_VERSION_OFFSET"


# ------------------------------------------------------------------------------
def merge_dict_of_lists(dict_a,
                        dict_b,
                        deduplicate=False):
    """
    Given two dictionaries who's contents are lists, merges them. If the same
    key appears in both, then the lists will be merged into a single key. If
    the key only appears in one or the other, then that entire dictionary entry
    will be added to the output as is.

    :param dict_a: The first dictionary who's values are a list.
    :param dict_b: The second dictionary who's values are a list.
    :param deduplicate: If True, then when lists are merged, any duplicate items
           will be removed.

    :return: A dictionary where both source dictionaries have been merged.
    """

    output = dict()

    for key in dict_a.keys():

        if key in dict_b.keys():
            merged_list = dict_a[key] + dict_b[key]
        else:
            merged_list = dict_a[key]

        if deduplicate:
            merged_list = list(set(merged_list))

        output[key] = merged_list

    for key in dict_b.keys():
        if key not in output.keys():
            if deduplicate:
                output[key] = list(set(dict_b[key]))
            else:
                output[key] = dict_b[key]

    return output


# ------------------------------------------------------------------------------
def get_env(var,
            default=None):
    """
    Returns the value of the env variable give by var. If the variable is
    missing, returns the default.

    :param var: The name of the env variable.
    :param default: The value to return if the variable is missing. Defaults to
           None.

    :return: The value of the variable, or default if it is missing.
    """

    try:
        return os.environ[var]
    except KeyError:
        return default


# ------------------------------------------------------------------------------
def sort_list_of_strings_by_length(unsorted_list,
                                   inverse=False):
    """
    Given a list, sorts this list so that the shortest elements come first. If
    two or more items have the same length, there is no defined order in which
    they will be sorted.

    Only works on lists of strings. If any element is not a string, raises an
    assertion error.

    :param unsorted_list: The list to sort.
    :param inverse: If True, then the list will be sorted in inverse order.

    :return: A new list where the shortest elements come first.
    """

    temp = dict()

    for item in unsorted_list:
        if not isinstance(item, str):
            raise AssertionError("sorting may only be done on lists of strings")

    for item in unsorted_list:
        length = len(item)
        try:
            temp[length].append(item)
        except KeyError:
            temp[length] = [item]

    output = list()
    keys = list(temp.keys())
    keys.sort(reverse=inverse)
    for key in keys:
        output.extend(temp[key])

    return output


# ------------------------------------------------------------------------------
def read_user_settings_from_env():
    """
    Reads some specific settings from the env. If they are missing, then it uses
    the built in constants.

    :return: a dictionary containing the values of the env settings. If any of
             these settings are missing from the env, then the globals will
             be substituted.
    """

    output = dict()

    # Auto Version Search paths (converted to a list)
    output["pkg_av_search_paths"] = get_env(USE_PKG_AV_SEARCH_PATHS_ENV,
                                            DEFAULT_USE_PKG_AV_PATHS)
    output["pkg_av_search_paths"] = output["pkg_av_search_paths"].split(":")

    # Baked Version Search paths (converted to a list)
    output["pkg_bv_search_paths"] = get_env(USE_PKG_BV_SEARCH_PATHS_ENV,
                                            DEFAULT_USE_PKG_BV_PATHS)
    output["pkg_bv_search_paths"] = output["pkg_bv_search_paths"].split(":")

    # Whether to search recursively, converted to a boolean
    output["do_recursive_search"] = get_env(USE_PKG_SEARCH_RECURSIVE_ENV,
                                            str(DEFAULT_DO_RECURSIVE_SEARCH))
    if output["do_recursive_search"].upper() not in ["TRUE", "FALSE"]:
        msg = "Environmental variable: " + USE_PKG_SEARCH_RECURSIVE_ENV
        msg += " must be either 'True' or 'False'. Exiting."
        display_error(msg)
        sys.exit(1)
    if output["do_recursive_search"].upper() == "TRUE":
        output["do_recursive_search"] = True
    else:
        output["do_recursive_search"] = False

    # Get the default offset for auto versions, converted to an integer
    output["auto_version_offset"] = get_env(USE_PKG_AUTO_VERSION_OFFSET_ENV,
                                            DEFAULT_AUTO_VERSION_OFFSET)
    try:
        output["auto_version_offset"] = int(output["auto_version_offset"])
    except ValueError:
        msg = "Environmental variable: " + USE_PKG_AUTO_VERSION_OFFSET_ENV
        msg += " must be an integer. Exiting."
        display_error(msg)
        sys.exit(1)

    return output


# ------------------------------------------------------------------------------
def get_version_path(use_pkg_path,
                     path_offset):
    """
    Gets the version path from the use pkg path. It uses the path_offset
    to find which parent dir is the version dir. May be either a positive or
    negative number (only the absolute value is used). For example, if the
    offset is 2 and the path to the use pkg is:

    /opt/apps/isotropix/clarisse/2.0sp1/wrapper/clarisse.use

    then the version path will be found two steps up the path from the use file,
    i.e.:

    /opt/apps/isotropix/clarisse/2.0sp1/

    :param use_pkg_path: The path to the use package we want to get the version
           from.
    :param path_offset: The number of paths to step up through to find the
           version number. Defaults to the global variable AUTO_VERSION_OFFSET.
           Can be either a positive or negative value. Only the absolute value
           is used.

    :return: A string containing the version path.
    """
    path_offset = abs(path_offset)

    remaining_path = use_pkg_path
    for i in range(path_offset):
        remaining_path = os.path.split(remaining_path)[0]

    return remaining_path


# ------------------------------------------------------------------------------
def get_version(use_pkg_path,
                path_offset):
    """
    Gets the version number automatically from the path. It uses the path_offset
    to find which parent dir is the version dir. May be either a positive or
    negative number (only the absolute value is used). For example, if the
    offset is 2 and the path to the use pkg is:

    /opt/apps/isotropix/clarisse/2.0sp1/wrapper/clarisse.use

    then the version will be found two steps up the path from the use file,
    i.e.:

    2.0sp1

    :param use_pkg_path: The path to the use package we want to get the version
           from.
    :param path_offset: The number of paths to step up through to find the
           version number. Defaults to the global variable AUTO_VERSION_OFFSET.
           Can be either a positive or negative value. Only the absolute value
           is used.

    :return: A string containing the version.
    """
    remaining_path = get_version_path(use_pkg_path, path_offset)

    return os.path.split(remaining_path)[1]


# ------------------------------------------------------------------------------
def get_built_in_vars(use_pkg_path,
                      path_offset):
    """
    This system has a few built-in variables that can be referenced in the .use
    files. These variables will then be replaced with their values with a simple
    text replacement. This function defines these variables and returns them in
    the format of a dictionary.

    At the moment, the variables the system understands are:

    VERSION <- the version number of the current use package.
    USE_PKG_PATH <- a path to where the use package is.
    VERSION_PATH <- a path up to where the version is.
    PRE_VERSION_PATH <- a path up to the version, but not including the version.

    :param use_pkg_path: The path to the use package we want to get the version
           from.
    :param path_offset: The number of paths to step up through to find the
           version number. Defaults to the global variable AUTO_VERSION_OFFSET.
           Can be either a positive or negative value. Only the absolute value
           is used.

    :return: A dict where the key is the variable name, and the value is the
             value.
    """

    output = dict()
    output["VERSION"] = get_version(use_pkg_path, path_offset)
    output["USE_PKG_PATH"] = os.path.split(use_pkg_path)[0]
    output["VERSION_PATH"] = get_version_path(use_pkg_path, path_offset)
    output["PRE_VERSION_PATH"] = os.path.split(output["VERSION_PATH"])[0]

    return output


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
            "must be owned by root and only writable by root. Exiting.")
    sys.exit(1)


# ------------------------------------------------------------------------------
def evaluate_use_pkg_file(file_n,
                          dir_n,
                          auto_version,
                          auto_version_offset):
    """
    Given a path to a file, evaluates whether it is a use pkg file or not. If it
    is, returns a tuple containing the use package name (including version, and
    a path to this use package.

    :param file_n: A path to a file.
    :param dir_n: The path where the file is located.
    :param auto_version: If True, then the version number will be added just
           before the .use. This version number will be extracted from the
           path. It will be added in the format: "-<version>". For example:
           clarisse.use would become clarisse-3.6sp7.use (where the version is
           "3.7sp7"). This will also auto-add a "latest" version that is based
           on a sort of available versions and points to the highest version.
    :param auto_version_offset: The offset that indicates which parent directory
           defines the version number. 1 = use package directory. 2 = parent
           of use package directory, 3 = grandparent, etc.

    :return: A tuple where the first element is the name of the use package
             (munged to include the version number if auto_version is true),
             and the second value is the path to the use package. If the file
             is not a valid use package, returns None.
    """

    if file_n.endswith(".use"):
        full_p = os.path.join(dir_n, file_n)
        if auto_version:
            version = get_version(full_p,
                                  auto_version_offset)
            file_n = os.path.splitext(file_n)[0]
            file_n += "-" + version + os.path.splitext(file_n)[1]
        else:
            file_n = os.path.splitext(file_n)[0]
        if ENFORCE_USE_PKG_PERMISSIONS:
            if not validate_permissions(full_p, LEGAL_PERMISSIONS):
                return None
        return file_n, full_p
    return None


# ------------------------------------------------------------------------------
def find_all_use_pkg_files(search_paths,
                           auto_version,
                           auto_version_offset,
                           recursive):
    """
    Finds all of the use packages:

    :param search_paths: A list of paths where the use packages could live.
    :param auto_version: If True, then the version number will be added just
           before the .use. This version number will be extracted from the
           path. It will be added in the format: "-<version>". For example:
           clarisse.use would become clarisse-3.6sp7.use (where the version is
           "3.6sp7").
    :param auto_version_offset: The offset that indicates which parent directory
           defines the version number. 1 = use package directory. 2 = parent
           of use package directory, 3 = grandparent, etc.
    :param recursive: If true, then all sub-dirs of the search paths will be
           traversed as well.

    :return: A dictionary of use package file names where the key is the name
             of the use package, and the value is the full path to this use
             package.
    """

    use_pkg_files = dict()
    for search_path in search_paths:
        if os.path.exists(search_path) and os.path.isdir(search_path):
            if recursive:
                for dir_n, dirs_n, files_n in os.walk(search_path):
                    for file_n in files_n:
                        result = evaluate_use_pkg_file(file_n,
                                                       dir_n,
                                                       auto_version,
                                                       auto_version_offset)
                        if result:
                            use_pkg_files[result[0]] = result[1]

            else:
                files_n = os.listdir(search_path)
                for file_n in files_n:
                    result = evaluate_use_pkg_file(file_n,
                                                   search_path,
                                                   auto_version,
                                                   auto_version_offset)
                    if result:
                        use_pkg_files[result[0]] = result[1]

    return use_pkg_files


# ------------------------------------------------------------------------------
def cmd_to_write_use_pkg_files_to_env(av_search_paths,
                                      bv_search_paths,
                                      auto_version_offset,
                                      recursive):
    """
    Finds all of the use packages and writes their names to an env var called
    "USE_AVAILABLE_PACKAGES" in the format:

    name1;path1:name2;path2:...:nameN;pathN


    :param av_search_paths: A list of paths where the auto version use packages
           could live.
    :param bv_search_paths: A list of paths where the baked version use packages
           could live.
    :param auto_version_offset: The offset that indicates which parent directory
           defines the version number. 1 = use package directory. 2 = parent
           of use package directory, 3 = grandparent, etc.
    :param recursive: If true, then all sub-dirs of the search paths will be
           traversed as well.

    :return: A string that is the bash shell command to create the env var.
    """

    use_pkg_files = list()
    av_use_pkgs = find_all_use_pkg_files(av_search_paths,
                                         True,
                                         auto_version_offset,
                                         recursive)

    bv_use_pkgs = find_all_use_pkg_files(bv_search_paths,
                                         False,
                                         0,
                                         recursive)

    for key in bv_use_pkgs.keys():
        if key not in av_use_pkgs.keys():
            av_use_pkgs[key] = bv_use_pkgs[key]

    for use_pkg in av_use_pkgs.keys():
        use_pkg_files.append(use_pkg + "@" + av_use_pkgs[use_pkg])

    output = ":".join(use_pkg_files)
    output = "export " + USE_PKG_AVAILABLE_PACKAGES_ENV + "=" + output
    return output


# ------------------------------------------------------------------------------
def get_use_package_names_and_paths_from_env():
    """
    Returns a dictionary of use package names and their full paths from the
    env. If more than one use package has the exact same name, only one will be
    returned. Which one is undefined.

    :return: A dict of full paths to (resolved) use package files keyed on their
             name (which may or may not include an added version number).
    """

    output = dict()
    env = os.environ[USE_PKG_AVAILABLE_PACKAGES_ENV]
    env = env.split(":")
    for item in env:
        output[item.split("@")[0]] = item.split("@")[1]
    return output


# ------------------------------------------------------------------------------
def get_use_package_names_from_env():
    """
    Returns a list of use package names only from the env. If more than one use
    package has the exact same name, only one will be returned. Which one is
    undefined.

    :return: A list of use package names (de-duplicated)
    """

    use_pkgs = get_use_package_names_and_paths_from_env()
    return use_pkgs.keys()


# ------------------------------------------------------------------------------
def get_use_package_path_from_env(use_pkg_name):
    """
    Given a specific use_pkg_name, returns the file path stored in the env var.

    :param use_pkg_name: The name of the use package.

    :return: A full path to the use package file on disk.
    """

    # Find the use package file from this use package name
    use_pkg_files = get_use_package_names_and_paths_from_env()
    try:
        return use_pkg_files[use_pkg_name]
    except KeyError:
        return None


# ------------------------------------------------------------------------------
def complete_use(stub):
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

    :return: Nothing
    """

    outputs = list()
    use_pkgs = get_use_package_names_from_env()
    for use_pkg in use_pkgs:
        if use_pkg.startswith(stub):
            outputs.append(use_pkg)
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
def read_use_pkg(use_pkg_file,
                 *delimiters):
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
                                            delimiters=delimiters,
                                            empty_lines_in_values=True)

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

    :param raw_aliases: A list of strings containing all of the current aliases.

    :return: A list of key/value tuples.
    """

    reformatted_aliases = dict()

    for raw_alias in raw_aliases:
        raw_alias = raw_alias.split("alias ")[1]
        key = raw_alias.split("=")[0]
        value = raw_alias.split("=")[1].rstrip("\n")
        reformatted_aliases[key] = value.strip("'")

    return reformatted_aliases


# ------------------------------------------------------------------------------
def get_use_package_branch(use_pkg_obj):
    """
    Returns all of the branches from the use_pkg_obj.

    :param use_pkg_obj: The config parser object, undelimited.

    :return: A list of key/value tuples containing all of the branches.
    """

    try:
        return use_pkg_obj.items("branch")[0][0]
    except configparser.NoSectionError:
        return ""


# ------------------------------------------------------------------------------
def get_use_package_path_appends(use_pkg_obj,
                                 do_prepend=True):
    """
    Path prepends and postpends are a special case because there may be multiple
    sections - one for each path variable - and we don't know how many there are
    ahead of time. Returns a dictionary keyed with the path variable and where
    the value is the path to either prepend or postpend.

    :param use_pkg_obj: The config parser object, undelimited.
    :param do_prepend: If True, look for prepends. Otherwise, look at postpends.

    :return: A dictionary where the key is the path variable, and the value is a
             list of paths to either prepend or postpend.
    """

    output = dict()
    sections = use_pkg_obj.sections()

    for section in sections:

        if do_prepend:
            match_str = "path-prepend-"
        else:
            match_str = "path-postpend-"

        if section.startswith(match_str):
            var = section.split(match_str)[1]
            items = [value[0] for value in use_pkg_obj.items(section)]
            output[var] = items

    return output


# ------------------------------------------------------------------------------
def get_use_package_items(use_pkg_obj,
                          item_type):
    """
    Returns all of the items from a specific section of the use_pkg_obj.

    :param use_pkg_obj: The config parser object, delimited.
    :param item_type: They type of item to return. Options are:
           env
           alias
           path_prepend
           path_postpend

    :return: A dict containing all of the items, where the key is the
             name of the item and value is the value it is being set to.
    """

    assert item_type in ["env", "alias"]

    output = dict()
    try:
        items = use_pkg_obj.items(item_type)
    except (configparser.NoSectionError, configparser.NoOptionError):
        return output

    for item in items:
        output[item[0]] = item[1]

    return output


# ------------------------------------------------------------------------------
def get_use_package_use_scripts(use_pkg_obj):
    """
    Returns any additional shell scripts to run as part of a use command from
    the use_pkg_obj.

    :param use_pkg_obj: The config parser object, undelimited.

    :return: A list of key/value tuples containing all of the bash commands.
    """

    try:
        return use_pkg_obj.items("use-scripts")
    except configparser.NoSectionError:
        return []


# ------------------------------------------------------------------------------
def get_use_package_unuse_scripts(use_pkg_obj):
    """
    Returns any additional shell scripts to run as part of an unuse command from
    the use_pkg_obj.

    :param use_pkg_obj: The config parser object, undelimited.

    :return: A list of key/value tuples containing all of the unuse commands.
    """

    try:
        return use_pkg_obj.items("unuse-scripts")
    except configparser.NoSectionError:
        return []


# ------------------------------------------------------------------------------
def get_use_package_use_cmds(use_pkg_obj):
    """
    Returns any additional shell scripts to run as part of a use command from
    the use_pkg_obj.

    :param use_pkg_obj: The config parser object, undelimited.

    :return: A list of key/value tuples containing all of the bash commands.
    """

    try:
        return use_pkg_obj.items("use-cmds")
    except configparser.NoSectionError:
        return []


# ------------------------------------------------------------------------------
def get_use_package_unuse_cmds(use_pkg_obj):
    """
    Returns any additional shell scripts to run as part of an unuse command from
    the use_pkg_obj.

    :param use_pkg_obj: The config parser object, undelimited.

    :return: A list of key/value tuples containing all of the unuse commands.
    """

    try:
        return use_pkg_obj.items("unuse-cmds")
    except configparser.NoSectionError:
        return []


# ------------------------------------------------------------------------------
def format_aliases_for_shell(aliases, variables):
    """
    Formats the aliases that are read directly from the config object as a
    string ready for the bash shell.

    :param aliases: A list of key/value tuples that contain the aliases.
    :param variables: A dict of string substitutions to perform.

    :return: A string containing the bash shell command to set the aliases.
    """

    output = ""
    for alias in aliases.keys():
        output += "alias "
        output += alias
        output += "="
        output += "'" + aliases[alias] + "';"

    replace_keys = list(variables.keys())
    replace_keys = sort_list_of_strings_by_length(replace_keys, True)

    for key in replace_keys:
        output = output.replace("$" + key, variables[key])

    return output.rstrip(";")


# ------------------------------------------------------------------------------
def format_env_vars_for_shell(env_vars, variables):
    """
    Generates the environmental variables.

    :param env_vars: A list of key/value tuples that contain the env vars.
    :param variables: A dict of string substitutions to perform.

    :return: A string containing the bash shell command to set the env
             variables.
    """

    output = ""
    for env_var in env_vars.keys():
        output += "export "
        output += env_var
        output += "="
        output += "'" + env_vars[env_var] + "';"

    replace_keys = list(variables.keys())
    replace_keys = sort_list_of_strings_by_length(replace_keys, True)

    for key in replace_keys:
        output = output.replace("$" + key, variables[key])

    return output.strip(";")


# ------------------------------------------------------------------------------
def format_paths_for_shell(path_prepends,
                           path_postpends,
                           sub_vars):
    """
    Given a list of path variables and values, appends the value to each of the
    path variables.

    :param path_prepends: A dictionary where the key is the name of the path
           variable and the value is a list of paths to prepend to this var.
    :param path_postpends: A dictionary where the key is the name of the path
           variable and the value is a list of paths to postpend to this var.
    :param sub_vars: A dict of string substitutions to perform.

    :return: A string containing the bash shell command to set the path env
             variable.
    """

    output = list()

    # Build a merged list of path variables
    path_vars = list(path_prepends.keys())
    path_vars.extend(list(path_postpends.keys()))
    path_vars = list(set(path_vars))

    for path_var in path_vars:

        try:
            prepends = path_prepends[path_var]
        except KeyError:
            prepends = []

        try:
            postpends = path_postpends[path_var]
        except KeyError:
            postpends = []

        replace_keys = list(sub_vars.keys())
        replace_keys = sort_list_of_strings_by_length(replace_keys, True)

        for sub_var in replace_keys:
            for i in range(len(prepends)):
                prepends[i] = prepends[i].replace("$" + sub_var,
                                                  sub_vars[sub_var])
            for i in range(len(postpends)):
                postpends[i] = postpends[i].replace("$" + sub_var,
                                                    sub_vars[sub_var])

        try:
            current_paths = os.environ[path_var]
        except KeyError:
            current_paths = ""
        current_paths = current_paths.split(":")

        # display_error("\n\n" + path_var + "\n----------------")
        # display_error("Current Paths: " + str(current_paths))
        # display_error("     prepends: " + str(prepends))
        # display_error("    postpends: " + str(postpends))

        actual_prepends = list()
        for new_path in prepends:
            if new_path not in current_paths:
                actual_prepends.append(new_path)

        actual_postpends = list()
        for new_path in postpends:
            if new_path not in current_paths:
                actual_postpends.append(new_path)

        new_paths = actual_prepends + current_paths + actual_postpends

        output.append("export " + path_var + "=" + ":".join(new_paths))

    return ";".join(output)


# ------------------------------------------------------------------------------
def format_scripts_for_shell(scripts, variables):
    """
    Generates the list of scripts to run as bash commands.

    :param scripts: A list of scripts.
    :param variables: A dict of string substitutions to perform.

    :return: A string containing the raw bash shell commands read from the use
             package file.
    """

    output = list()

    replace_keys = list(variables.keys())
    replace_keys = sort_list_of_strings_by_length(replace_keys, True)

    for cmd in scripts:
        cmd = cmd[0]
        for key in replace_keys:
            cmd = cmd.replace("$" + key, variables[key])
        output.append(cmd)

    return ";".join(output)


# ------------------------------------------------------------------------------
def format_cmds_for_shell(cmds, variables):
    """
    Generates the free-form bash commands.

    :param cmds: A list of key/value tuples that contain the commands.
    :param variables: A dict of string substitutions to perform.

    :return: A string containing the raw bash shell commands read from the use
             package file.
    """

    output = list()

    replace_keys = list(variables.keys())
    replace_keys = sort_list_of_strings_by_length(replace_keys, True)

    for cmd in cmds:
        cmd = cmd[0]
        for key in replace_keys:
            cmd = cmd.replace("$" + key, variables[key])
        output.append(cmd)

    return ";".join(output)


# ------------------------------------------------------------------------------
def get_matching_aliases(new_aliases, existing_aliases):
    """
    Given a list of new aliases and existing aliases, returns a list of existing
    aliases that are also in new_aliases.

    :param new_aliases: A dictionary of new aliases being created.
    :param existing_aliases: A dictionary of existing aliases.

    :return: A dictionary where the key is the existing alias and the value is
             the existing value for any aliases that are being modified.
    """

    output = dict()

    # Build a list of the new alias names
    for existing_alias in existing_aliases.keys():
        if existing_alias in new_aliases.keys():
            output[existing_alias] = existing_aliases[existing_alias]

    return output


# ------------------------------------------------------------------------------
def get_matching_env_vars(new_env_vars):
    """
    For the env vars listed in the use_pkg_obj, get a list of their current
    values. Returns a dictionary.

    :param new_env_vars: A dictionary containing the new env vars to be set.

    :return: A dict where the key is each env var name that exists in the
             current shell that is being modified by the use package, and the
             value is its value prior to being modified.
    """

    output = dict()

    for new_var in new_env_vars:

        try:
            existing_var_value = os.environ[new_var]
        except KeyError:
            existing_var_value = None

        if existing_var_value:
            output[new_var] = existing_var_value

    return output


# ------------------------------------------------------------------------------
def get_matching_paths(path_prepends,
                       path_postpends):
    """
    If the existing shell has any paths that are being modified, returns those
    path variables along with their pre-modification values.

    :param path_prepends: A dict of paths that are being modified via prepends.
    :param path_postpends: A dict of paths that are being modified via
           postpends.

    :return: A dictionary where the key is the name of the existing path that is
             being modified, and the value is the original value of this path
             before being modified..
    """

    output = dict()

    # Build a merged list of path variable names
    path_vars = list(path_prepends.keys())
    path_vars.extend(list(path_postpends.keys()))
    path_vars = list(set(path_vars))

    for path_var in path_vars:

        if path_var in os.environ:
            output[path_var] = os.environ[path_var]

    return output


# ------------------------------------------------------------------------------
def write_history(use_pkg_name,
                  use_pkg_file,
                  branch,
                  new_aliases,
                  new_env_vars,
                  new_path_prepends,
                  new_path_postpends,
                  use_scripts,
                  unuse_scripts,
                  use_cmds,
                  unuse_cmds,
                  modified_aliases,
                  modified_env_vars,
                  modified_path_vars):
    """
    Writes the actions being taken by the current use package to a temp history
    file. Also includes any existing aliases, env vars, and paths that may be
    modified in the process.

    :param use_pkg_name: The name of the use package (does not include .use)
    :param use_pkg_file: The full name of the use package.
    :param branch: A string representing the branch for this use package.
    :param new_aliases: A list of key/value tuples listing the aliases being set
           in this use package.
    :param new_env_vars: A list of key/value tuples listing the env vars being
           set in this use package.
    :param new_path_prepends: A list of key/value tuples listing the new path
           prepends in this use package.
    :param new_path_postpends: A list of key/value tuples listing the new path
           postpends in this use package.
    :param use_scripts: A list of key/value tuples listing the bash shell
           use scripts being run by this use package.
    :param unuse_scripts: A list of key/value tuples listing the bash shell
           unuse scripts being run by this use package.
    :param use_cmds: A list of the single line use cmds.
    :param unuse_cmds: A list of the single line unuse cmds.
    :param modified_aliases: A list of key/value tuples listing the existing
           aliases that will be overwritten by the new aliases in this use
           package.
    :param modified_env_vars: A list of key/value tuples listing the existing
           env vars that will be overwritten by the new env vars in this use
           package.
    :param modified_path_vars: A list of key/value tuples listing the existing
           path vars that will be modified by the new path settings in this
           use package.

    :return: Nothing
    """

    # Make sure the history file exists and that we can find it
    try:
        history_file = os.environ[USE_PKG_HISTORY_FILE_ENV]
    except KeyError:
        display_error("No history file. Did you forget to run setup first?")
        sys.exit(1)
    if not os.path.exists(history_file):
        display_error("History file",
                      history_file,
                      "does not exist. Did setup fail?")
        sys.exit(1)

    # Open the history file as a configparser object
    hist_obj = configparser.ConfigParser()
    hist_obj.read(history_file)

    # If there is already a completed use for the current branch, then an error
    # has occurred (the unuse did not get run)
    if hist_obj.has_section(branch):
        msg = "The branch '" + branch
        msg += "' still exists. Auto-unuse may have failed."
        display_error(msg)
        sys.exit(1)

    # Create the branch section
    hist_obj.add_section(branch)

    # Add the data
    hist_obj.set(branch, "timestamp", str(int(time.time())))
    hist_obj.set(branch, "name", use_pkg_name)
    hist_obj.set(branch, "use_package", use_pkg_file)
    hist_obj.set(branch, "new_aliases", str(new_aliases))
    hist_obj.set(branch, "new_env_vars", str(new_env_vars))
    hist_obj.set(branch, "new_path_prepends", str(new_path_prepends))
    hist_obj.set(branch, "new_path_postpends", str(new_path_postpends))
    hist_obj.set(branch, "use_scripts", str(use_scripts))
    hist_obj.set(branch, "unuse_scripts", str(unuse_scripts))
    hist_obj.set(branch, "use_cmds", str(use_cmds))
    hist_obj.set(branch, "unuse_cmds", str(unuse_cmds))
    hist_obj.set(branch, "existing_aliases", str(modified_aliases))
    hist_obj.set(branch, "existing_env_vars", str(modified_env_vars))
    hist_obj.set(branch, "existing_path_vars", str(modified_path_vars))

    # Write out the new history file
    with open(history_file, "w") as f:
        hist_obj.write(f)


# ------------------------------------------------------------------------------
def read_history():
    """
    Reads in the history file given by history_file.

    :return: A config parser object containing the history.
    """

    # Make sure the history file exists and that we can find it
    try:
        history_file = os.environ[USE_PKG_HISTORY_FILE_ENV]
    except KeyError:
        display_error("No history file. Did you forget to run setup first?")
        sys.exit(1)
    if not os.path.exists(history_file):
        display_error("History file",
                      history_file,
                      "does not exist. Did setup fail?")
        sys.exit(1)

    # Open the history file as a configparser object
    hist_obj = configparser.ConfigParser()
    hist_obj.read(history_file)

    return hist_obj


# ------------------------------------------------------------------------------
def use(use_pkg_name, raw_aliases):
    """
    Uses a new package (given by use_pkg_name). Processes this file and exports
    the contents converted into bash commands.

    :param use_pkg_name: A name of the use package (not the file name, just
           the package name. (Eg: clarisse-3.6sp2, and not clarisse-3.6sp2.use).
    :param raw_aliases: The contents of the stdin.

    :return: Nothing
    """

    # Find the use package file from this use package name
    use_pkg_file = get_use_package_path_from_env(use_pkg_name)
    if use_pkg_file is None:
        display_error("No use package named: " + use_pkg_name)
        return

    # Read this use package file (both delimited and undelimited)
    use_obj_delim, use_obj_undelim = verify_and_read_use_pkg(use_pkg_file)

    # Extract the various bits of data we need from this config
    branch = get_use_package_branch(use_obj_undelim)
    aliases = get_use_package_items(use_obj_delim, "alias")
    env_vars = get_use_package_items(use_obj_delim, "env")
    path_prepends = get_use_package_path_appends(use_obj_delim, True)
    path_postpends = get_use_package_path_appends(use_obj_delim, False)
    use_scripts = get_use_package_use_scripts(use_obj_undelim)
    unuse_scripts = get_use_package_unuse_scripts(use_obj_undelim)
    use_cmds = get_use_package_use_cmds(use_obj_undelim)
    unuse_cmds = get_use_package_unuse_cmds(use_obj_undelim)

    # Validate the permissions of the use and unuse scripts.
    if ENFORCE_CALLED_SCRIPT_PERMISSIONS:
        for script in use_scripts:
            if not validate_permissions(script[0], LEGAL_PERMISSIONS):
                handle_permission_violation(script[0])
        for script in unuse_scripts:
            if not validate_permissions(script[0], LEGAL_PERMISSIONS):
                handle_permission_violation(script[0])

    # Unuse the previous version of this package (if it exists)
    try:
        history_file = os.environ[USE_PKG_HISTORY_FILE_ENV]
    except KeyError:
        history_file = None

    # Open the history file as a configparser object and remove the previous
    # instance of this same branch.
    if history_file:

        hist_obj = configparser.ConfigParser()
        hist_obj.read(history_file)

        if hist_obj.has_section(branch):
            use_pkg_name = hist_obj.get(branch, "name")
            unuse(use_pkg_name, raw_aliases)

    substitutions = get_built_in_vars(use_pkg_file,
                                      settings["auto_version_offset"])

    # Extract the data from the package file and reformat it into a series of
    # bash shell commands that will be passed back as a single, semi-colon
    # delimited command.
    bash_cmd = list()
    bash_cmd.append(format_aliases_for_shell(aliases, substitutions))
    bash_cmd.append(format_env_vars_for_shell(env_vars, substitutions))
    bash_cmd.append(format_paths_for_shell(path_prepends,
                                           path_postpends,
                                           substitutions))
    bash_cmd.append(format_scripts_for_shell(use_scripts, substitutions))
    bash_cmd.append(format_cmds_for_shell(use_cmds, substitutions))
    bash_cmd = ";".join(bash_cmd)
    while ";;" in bash_cmd:
        bash_cmd = bash_cmd.replace(";;", ";")
    bash_cmd = bash_cmd.strip(";")

    # Verify that the use scripts exist
    for use_script in use_scripts:
        use_script = use_script[0]
        if not os.path.exists(use_script):
            msg = "use script: " + use_script + " does not exist. Exiting."
            display_error(msg)
            sys.exit(1)

    # Verify that the unuse scripts exist
    for unuse_script in unuse_scripts:
        unuse_script = unuse_script[0]
        if not os.path.exists(unuse_script):
            msg = "unuse script: " + unuse_script + " does not exist. Exiting."
            display_error(msg)
            sys.exit(1)

    # Verify the use scripts and unuse scripts have the correct permissions
    if ENFORCE_APP_PERMISSIONS:
        for use_script in use_scripts:
            use_script = use_script[0]
            if not validate_permissions(use_script, LEGAL_PERMISSIONS):
                if DISPLAY_PERMISSIONS_VIOLATIONS:
                    msg = "Script: " + use_script + " must be owned by root"
                    msg += "and only writable by root."
                    display_error(msg)
                sys.exit(1)

        for unuse_script in unuse_scripts:
            unuse_script = unuse_script[0]
            if not validate_permissions(unuse_script, LEGAL_PERMISSIONS):
                if DISPLAY_PERMISSIONS_VIOLATIONS:
                    msg = "Script: " + unuse_script + " must be owned by root"
                    msg += "and only writable by root."
                    display_error(msg)
                sys.exit(1)

    # Next we will have to build the history info. This is basically a list of
    # what we changed, and what its previous value was so that we can
    # potentially change it back.

    # Reformat the existing aliases to be a dictionary
    existing_aliases = format_existing_aliases(raw_aliases)

    # Get a list of aliases in the current shell that match those being reset
    modified_aliases = get_matching_aliases(aliases, existing_aliases)

    # Get a list of env vars in the current shell that match those being reset
    modified_env_vars = get_matching_env_vars(env_vars)

    # Get a list of existing paths that match those being changed.
    modified_path_vars = get_matching_paths(path_prepends, path_postpends)

    # Write out the history
    write_history(use_pkg_name=use_pkg_name,
                  use_pkg_file=use_pkg_file,
                  branch=branch,
                  new_aliases=aliases,
                  new_env_vars=env_vars,
                  new_path_prepends=path_prepends,
                  new_path_postpends=path_postpends,
                  use_scripts=use_scripts,
                  unuse_scripts=unuse_scripts,
                  use_cmds=use_cmds,
                  unuse_cmds=unuse_cmds,
                  modified_aliases=modified_aliases,
                  modified_env_vars=modified_env_vars,
                  modified_path_vars=modified_path_vars)

    # Export the bash command
    export_shell_command(bash_cmd)


# ------------------------------------------------------------------------------
def get_used():
    """
    Reads the history file and returns a list of all used packages in the
    current shell.

    :return: A list of used package names.
    """

    used_pkg_names = list()

    hist_obj = read_history()
    branches = hist_obj.sections()
    for branch in branches:
        used_pkg_names.append(hist_obj.get(branch, "name"))

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
def unuse_aliases(hist_obj,
                  branch,
                  raw_aliases):
    """
    Undoes the aliases set by the use cmd. It follows the following logic:

    If the alias does not exist in the current shell, or if the alias still
    exists in the current shell but is different than the value set by the use
    package, then something has actively changed it since we ran the use
    command. We do not want to override this decision, so do nothing.

    If the alias still exists in the current shell but is the same as the
    value set by the use package, then nothing has actively changed it since
    we ran the use command. We should then consider the following three options
    in order:

    a) If a subsequent use command set the alias to the same value, we should do
       nothing.

    b) If the alias did not exist prior to us running the use package, we should
       unset this alias so that it no longer exists.

    c) If the alias did exist prior to us running the use package, then we
       should reset this alias to that value.

    :param hist_obj: A config parser object containing the use history for the
           current shell.
    :param branch: The name of the use branch we are un-using.
    :param raw_aliases: The stdIn that contains the aliases as they exist in the
           current shell.

    :return: A string of semi-colon separated commands to either reset or
             unset the aliases that were set by the use command.
    """

    output = list()

    # Format the existing aliases into key/value tuples
    shell_aliases = format_existing_aliases(raw_aliases)

    new_aliases = hist_obj.get(branch, "new_aliases")
    new_aliases = ast.literal_eval(new_aliases)

    prev_aliases = hist_obj.get(branch, "existing_aliases")
    prev_aliases = ast.literal_eval(prev_aliases)

    # Step through each of the aliases that were set by the use package we are
    # now un-using.
    for alias in new_aliases:

        # Find the matching alias in the current shell's aliases. If it does not
        # exist, just continue to the next alias
        if alias not in shell_aliases.keys():
            continue

        # If it does exist, check its current value. If it is different than
        # what this use package had set it to, just move on to the next alias
        if shell_aliases[alias] != new_aliases[alias]:
            continue

        # If we get here, then the alias exists in the current shell and is
        # identical to the value set by the use package.

        # Check to see if a subsequent use package has touched this same alias.
        timestamp = int(hist_obj.get(branch, "timestamp"))
        for other_section in hist_obj.sections():
            other_timestamp = int(hist_obj.get(other_section, "timestamp"))
            if other_section != branch and other_timestamp > timestamp:
                other_new_aliases = hist_obj.get(other_section, "new_aliases")
                other_new_aliases = ast.literal_eval(other_new_aliases)
                if alias in other_new_aliases.keys():
                    continue

        # If the alias does not exist in the prev_aliases, unset the alias.
        if alias not in prev_aliases.keys():
            output.append("unalias " + alias + ";")
            continue

        # If the alias does exist in the old_aliases, reset the alias to that
        # value.
        output.append("alias " + alias + "='" + prev_aliases[alias] + "';")

    return ";".join(output)


# ------------------------------------------------------------------------------
def unuse_env_vars(hist_obj, branch):
    """
    Undoes the env vars set by the use cmd. It follows the following logic:

    If the var does not exist in the current shell, or if the var still
    exists in the current shell but is different than the value set by the use
    package, then something has actively changed it since we ran the use
    command. We do not want to override this decision, so do nothing.

    If the var still exists in the current shell but is the same as the
    value set by the use package, then nothing has actively changed it since
    we ran the use command. We should then consider the following three options
    in order:

    a) If a subsequent use command set the var to the same value, we should do
       nothing.

    b) If the var did not exist prior to us running the use package, we should
       unset this var so that it no longer exists.

    c) If the var did exist prior to us running the use package, then we
       should reset this var to that value.

    :param hist_obj: A config parser object containing the use history for the
           current shell.
    :param branch: The name of the use branch we are un-using.

    :return: A string of semi-colon separated commands to either reset or
             unset the vars that were set by the use command.
    """

    output = list()

    new_vars = hist_obj.get(branch, "new_env_vars")
    new_vars = ast.literal_eval(new_vars)

    prev_vars = hist_obj.get(branch, "existing_env_vars")
    prev_vars = ast.literal_eval(prev_vars)

    # Step through each of the aliases that were set by the use package we are
    # now un-using.
    for var in new_vars:

        # Find the matching alias in the current shell's aliases. If it does not
        # exist, just continue to the next alias
        if var not in os.environ:
            continue

        # If it does exist, check its current value. If it is different than
        # what this use package had set it to, just move on to the next alias
        if os.environ[var] != new_vars[var]:
            continue

        # If we get here, then the alias exists in the current shell and is
        # identical to the value set by the use package.

        # Check to see if a subsequent use package has touched this same alias.
        timestamp = int(hist_obj.get(branch, "timestamp"))
        for other_section in hist_obj.sections():
            other_timestamp = int(hist_obj.get(other_section, "timestamp"))
            if other_section != branch and other_timestamp > timestamp:
                other_new_vars = hist_obj.get(other_section, "new_aliases")
                other_new_vars = ast.literal_eval(other_new_vars)
                if var in other_new_vars.keys():
                    continue

        # If the alias does not exist in the prev_aliases, unset the alias.
        if var not in prev_vars.keys():
            output.append("unset " + var + ";")
            continue

        # If the alias does exist in the old_aliases, reset the alias to that
        # value.
        output.append("export " + var + "='" + prev_vars[var] + "';")

    return ";".join(output)


# ------------------------------------------------------------------------------
def unuse_paths(hist_obj,
                branch):
    """
    Remove any paths that were added to path variables during the use command.

    Un-using paths follows the following logic:

    If a path was added to a path variable by a use command, remove this path.
    But only do it if:

    a) The path was not already present for this variable in the shell prior to
       adding it via the use command.

    b) No other use command since has added this exact same path to this exact
       same path variable.

    If removing the path would result in an empty variable, remove the variable
    itself.

    :param hist_obj: A configparser object containing the history for this
           shell.
    :param branch: The name of the use branch we are un-using.

    :return: A bash shell string removing the paths (or removing the whole var
             if needed).
    """

    # Build a dict where the key is the unuse path variable names and its values
    # are a list of all of the actual paths that were added to it.
    path_prepends = hist_obj.get(branch, "new_path_prepends")
    path_prepends = ast.literal_eval(path_prepends)
    path_postpends = hist_obj.get(branch, "new_path_postpends")
    path_postpends = ast.literal_eval(path_postpends)
    unuse_paths_dict = merge_dict_of_lists(path_prepends, path_postpends)

    # Get the timestamp of this use package
    timestamp = int(hist_obj.get(branch, "timestamp"))

    # Check the history file to see if any of these paths were already present
    # in the path variables prior to the use package being used.
    history_paths = hist_obj.get(branch, "existing_path_vars")
    history_paths = ast.literal_eval(history_paths)

    for path_var in unuse_paths_dict.keys():
        if path_var in history_paths.keys():
            remove_paths = list()
            for actual_path in unuse_paths_dict[path_var]:
                if actual_path in history_paths[path_var]:
                    remove_paths.append(actual_path)
            for remove_path in remove_paths:
                unuse_paths_dict[path_var].remove(remove_path)

    # Check any subsequent use packages to see if they have set the exact same
    # path for the exact same variable
    for other_branch in hist_obj.sections():
        other_timestamp = int(hist_obj.get(other_branch, "timestamp"))
        if other_branch != branch and other_timestamp > timestamp:

            # Merge the prepends and postpends of this section into a dict
            path_prepends = hist_obj.get(other_branch,
                                         "new_path_prepends")
            path_prepends = ast.literal_eval(path_prepends)
            path_postpends = hist_obj.get(other_branch,
                                          "new_path_postpends")
            path_postpends = ast.literal_eval(path_postpends)
            other_paths_dict = merge_dict_of_lists(path_prepends,
                                                   path_postpends)

            for path_var in unuse_paths_dict.keys():
                if path_var in other_paths_dict.keys():
                    remove_paths = list()
                    for actual_path in unuse_paths_dict[path_var]:
                        if actual_path in unuse_paths_dict[path_var]:
                            remove_paths.append(actual_path)
                    for remove_path in remove_paths:
                        unuse_paths_dict[path_var].remove(remove_path)

    # Now convert this into new shell commands to set the path vars
    bash_cmd = list()

    for path_var in unuse_paths_dict.keys():

        # Get the current paths set in the shell for this variable
        try:
            shell_paths = os.environ[path_var]
        except KeyError:
            shell_paths = ""

        # Split the shell path into a list, taking into account escaped colons
        shell_paths = shell_paths.replace(r"\:", "_!USECMDBS+COLON!_")
        shell_paths = shell_paths.split(":")
        for i in range(len(shell_paths)):
            shell_paths[i] = shell_paths[i].replace("_!USECMDBS+COLON!_", r"\:")

        # Step though each unuse path and remove it from the shell path
        for unuse_path in unuse_paths_dict[path_var]:
            if unuse_path in shell_paths:
                shell_paths.remove(unuse_path)

        # If there are any paths left, set the variable to equal that
        if len(shell_paths) > 0:
            bash_cmd.append("export " + path_var + "=" + ":".join(shell_paths))

        # Otherwise just remove the variable completely
        else:
            bash_cmd = ["unset " + path_var]

    return ";".join(bash_cmd)


# ------------------------------------------------------------------------------
def unuse(use_pkg_name,
          raw_aliases):
    """
    Given a use_pkg_name this will find the most recent version in the history
    file and try to undo whatever that use command did (but being aware not to
    step on any identical settings that may have been set as a consequence of
    another use package that has been run since that time).

    :param use_pkg_name: The name of the use package we are un-using.
    :param raw_aliases: The list of raw alias strings.

    :return: Nothing.
    """

    # Make sure the history file exists and that we can find it
    try:
        history_file = os.environ[USE_PKG_HISTORY_FILE_ENV]
    except KeyError:
        display_error("No history file. Did you forget to run setup first?")
        sys.exit(1)
    if not os.path.exists(history_file):
        display_error("History file",
                      history_file,
                      "does not exist. Did setup fail?")
        sys.exit(1)

    # Open the history file as a configparser object
    hist_obj = configparser.ConfigParser()
    hist_obj.read(history_file)

    # Find the use branch from the use package name
    branch = None
    for possible_branch in hist_obj.sections():
        if hist_obj.get(possible_branch, "name") == use_pkg_name:
            branch = possible_branch
            break
    if not branch:
        return

    cmd = list()
    # ##########################################################################
    # A full unuse does the following:
    # ##########################################################################
    #
    # 1) removes any added paths - unless any other use package before or after
    #    has also added that same path.
    # --------------------------------------------------------------------------
    result = unuse_paths(hist_obj, branch)
    if result:
        cmd.append(result)

    # 2) resets any changed aliases back to what it was- unless that alias is
    #    different than what it was changed to (i.e. another process has changed
    #    it since the use command) - OR - a subsequent use command has touched
    #    this same alias (even if it is to change it to the same value).
    # --------------------------------------------------------------------------
    result = unuse_aliases(hist_obj, branch, raw_aliases)
    if result:
        cmd.append(result)

    # 3) resets any changed env vars back to what it was - unless that env var
    #    is different than what it was changed to (i.e. another process has
    #    changed it since the use command) - OR - a subsequent use command has
    #    touched this same env variable (even if it is to change it to the same
    #    value).
    # --------------------------------------------------------------------------
    result = unuse_env_vars(hist_obj, branch)
    if result:
        cmd.append(result)

    # 4) add the unuse scripts.
    unuse_scripts = hist_obj.get(branch, "unuse_scripts")
    unuse_scripts = ast.literal_eval(unuse_scripts)
    if unuse_scripts:

        # Validate the permissions of the use and unuse scripts.
        if ENFORCE_CALLED_SCRIPT_PERMISSIONS:
            for script in unuse_scripts:
                if not validate_permissions(script[0], LEGAL_PERMISSIONS):
                    handle_permission_violation(script[0])

        for i in range(len(unuse_scripts)):
            unuse_script = unuse_scripts[i][0]
            unuse_scripts[i] = unuse_script
            if not os.path.exists(unuse_script):
                msg = "Script: " + unuse_script + " does not exist."
                display_error(msg)
                sys.exit(1)
            if ENFORCE_APP_PERMISSIONS:
                if not validate_permissions(unuse_script, LEGAL_PERMISSIONS):
                    if DISPLAY_PERMISSIONS_VIOLATIONS:
                        handle_permission_violation(unuse_script)
                    sys.exit(1)

        cmd.extend(unuse_scripts)

    # 5) add any unuse cmds
    unuse_cmds = hist_obj.get(branch, "unuse_cmds")
    unuse_cmds = ast.literal_eval(unuse_cmds)
    if unuse_cmds:
        for i in range(len(unuse_cmds)):
            unuse_cmd = unuse_cmds[i][0]
            unuse_cmds[i] = unuse_cmd
        cmd.extend(unuse_cmds)

    # Clean up the history file
    hist_obj.remove_section(branch)
    with open(os.environ[USE_PKG_HISTORY_FILE_ENV], "w") as f:
        hist_obj.write(f)

    # # Export the shell command to run this command
    cmd = ";".join(cmd)
    while ";;" in cmd:
        cmd = cmd.replace(";;", ";")
    cmd = cmd.strip(";")
    export_shell_command(cmd)


# ------------------------------------------------------------------------------
def get_prev_unuse_pkg_from_new_use_pkg(use_pkg_name):
    """
    Given a use package name, get the unuse package name (if it exists).

    :param use_pkg_name: The name of the current use package.

    :return: The name of the unuse package (if one exists).
    """

    try:
        history_file = os.environ[USE_PKG_HISTORY_FILE_ENV]
    except KeyError:
        export_shell_command("")
        return

    hist_obj = configparser.ConfigParser()
    hist_obj.read(history_file)

    # Find the use package file from this use package name
    use_pkg_file = get_use_package_path_from_env(use_pkg_name)
    if use_pkg_file is None:
        export_shell_command("")
        return

    # Read this use package file (both delimited and undelimited)
    use_obj_delim, use_obj_undelim = verify_and_read_use_pkg(use_pkg_file)

    # Extract the various bits of data we need from this config
    branch = get_use_package_branch(use_obj_undelim)

    # Get the unuse package name from the history file
    if not hist_obj.has_section(branch):
        export_shell_command("")
        return

    unuse_pkg_name = hist_obj.get(branch, "name")
    export_shell_command(unuse_pkg_name)


# ------------------------------------------------------------------------------
def setup():
    """
    Does the setup for the current shell. Needs to be run once per shell before
    the system is usable.

    :return: An environmental variable USE_PKG_HISTORY_FILE_ENV with a path to a
             text file that contains the history of use commands for the current
             session.
    """

    # Check to see if there is already a use history file for this shell.
    # Create one if needed.
    try:
        use_history_file = os.environ[USE_PKG_HISTORY_FILE_ENV]
    except KeyError:
        f, use_history_file = tempfile.mkstemp(suffix=".usehistory", text=True)

    # Store this file name in the form of an environmental variable.
    output = "export " + USE_PKG_HISTORY_FILE_ENV + "=" + use_history_file

    legal_path_found = False
    for path in settings["pkg_av_search_paths"]:
        if os.path.exists(path) and os.path.isdir(path):
            legal_path_found = True
    for path in settings["pkg_bv_search_paths"]:
        if os.path.exists(path) and os.path.isdir(path):
            legal_path_found = True

    if not legal_path_found:
        display_error("No use package directories found. I looked for:",
                      ":".join(settings["pkg_av_search_paths"]),
                      "and",
                      ":".join(settings["pkg_bv_search_paths"]))
        sys.exit(1)

    # Store the auto version use package search paths
    output += ";export " + USE_PKG_AV_SEARCH_PATHS_ENV
    output += "=" + ":".join(settings["pkg_av_search_paths"])

    # Store the baked version use package search paths
    output += ";export " + USE_PKG_BV_SEARCH_PATHS_ENV
    output += "=" + ":".join(settings["pkg_bv_search_paths"])

    # Save the existing use packages to an env var
    output += ";"
    output += cmd_to_write_use_pkg_files_to_env(settings["pkg_av_search_paths"],
                                                settings["pkg_bv_search_paths"],
                                                settings["auto_version_offset"],
                                                settings["do_recursive_search"])

    # Export these env variables.
    export_shell_command(output)


# ==============================================================================
# ==============================================================================
if __name__ == "__main__":

    # Make sure this script is owned by root and only writable by root.
    if ENFORCE_APP_PERMISSIONS:
        if not validate_permissions(os.path.abspath(__file__),
                                    LEGAL_PERMISSIONS):
            handle_permission_violation(os.path.abspath(__file__))

    # Only handle specific types of requests
    if sys.argv[1] not in LEGAL_COMMANDS:
        display_error("Unknown command: " + sys.argv[1])
        display_usage()
        sys.exit(1)

    # Read the env and stuff its settings into the constants
    settings = read_user_settings_from_env()

    # SETUP
    # ===========================
    if sys.argv[1] == "setup":
        setup()
        sys.exit(0)

    # ===========================
    if sys.argv[1] == "refresh":
        setup()
        sys.exit(0)

    # ===========================
    if sys.argv[1] == "unuse_package_from_use_package":
        get_prev_unuse_pkg_from_new_use_pkg(sys.argv[2])

    # ===========================
    if sys.argv[1] == "complete_use":
        complete_use(sys.argv[2])

    # ===========================
    if sys.argv[1] == "complete_unuse":
        complete_unuse(sys.argv[2])

    # ===========================
    if sys.argv[1] == "use":
        if len(sys.argv) != 3:
            display_error("use: Wrong number of arguments.")
            sys.exit(1)
        stdin = list(sys.stdin)
        use(sys.argv[2], stdin)

    # ===========================
    if sys.argv[1] == "used":
        used()

    # ===========================
    if sys.argv[1] == "unuse":
        stdin = list(sys.stdin)
        if len(sys.argv) > 2:
            unuse(sys.argv[2], stdin)

    # ===========================
    # Just for debugging.
    if sys.argv[1] == "test":
        pass
