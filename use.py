#!/usr/bin/env python3

import configparser
import json
import os
import sys

import completions
import display
import permissions
import setup

DEBUG = True


# ----------------------------------------------------------------------------------------------------------------------
def debug(*msgs):
    """
    If the module level global value of DEBUG is set to True, this will attempt to print a debug statement.

    :param msgs: an arbitrary number of messages to print to the stderr. Note, each msg will be printed on a new line.

    :return: Nothing.
    """

    if DEBUG:
        for msg in msgs:
            display.display_error(msg)


# ----------------------------------------------------------------------------------------------------------------------
def sort_by_length_into_new_list(list_to_sort) -> list:
    """
    Sorts the given list by the length of the strings in that list.

    :param list_to_sort: The list we want to sort.

    :return: A new list ordered by length.
    """
    for item in list_to_sort:
        if not isinstance(item, str):
            raise TypeError("sort by length requires a list of strings.")

    return sorted(list_to_sort, key=len, reverse=True)


# ----------------------------------------------------------------------------------------------------------------------
def get_built_in_vars(use_pkg_path,
                      path_offset):
    """
    This system has a few built-in variables that can be referenced in the .use files. These variables will then be
    replaced with their values with a simple text replacement. This function defines these variables and returns them in
    the format of a dictionary.

    At the moment, the variables the system understands are:

    VERSION <- the version number of the current use package.
    USE_PKG_PATH <- a path to where the use package is.
    VERSION_PATH <- a path up to where the version is.
    PRE_VERSION_PATH <- a path up to the version, but not including the version.

    :param use_pkg_path: The path to the use package we want to get the version from.
    :param path_offset: The number of paths to step up through to find the version number. Defaults to the global
           variable AUTO_VERSION_OFFSET. Can be either a positive or negative value. Only the absolute value is used.

    :return: A dict where the key is the variable name, and the value is the value.
    """

    output = dict()

    version_path = setup.get_version_path(use_pkg_path, path_offset)

    output["PRE_VERSION_PATH"] = os.path.split(version_path)[0]
    output["USE_PKG_PATH"] = os.path.split(use_pkg_path)[0]
    output["VERSION_PATH"] = version_path
    output["VERSION"] = setup.get_version(use_pkg_path, path_offset)

    return output


# ----------------------------------------------------------------------------------------------------------------------
def get_use_pkg_file_from_use_pkg_name(use_pkg_name):
    """
    Given a use package name, return the path to that use package file. If not use package file exists, returns None.

    :param use_pkg_name: The name of the use package.

    :return: a path to the use package file.
    """

    use_pkg_file = completions.get_use_package_path_from_env(use_pkg_name)
    if use_pkg_file is None:
        return None
    return use_pkg_file


# ----------------------------------------------------------------------------------------------------------------------
def read_use_pkg(use_pkg_file):
    """
    Opens a use package file (given by use_pkg_file).

    :param use_pkg_file: The full path to the use package file.

    :return: A configParser object.
    """

    use_pkg_obj = configparser.ConfigParser(allow_no_value=True,
                                            delimiters="=",
                                            empty_lines_in_values=True)

    # Force configparser to maintain capitalization of keys
    use_pkg_obj.optionxform = str

    try:
        use_pkg_obj.read(use_pkg_file)
    except configparser.DuplicateOptionError as e:
        display.display_error("Duplicate entries in .use config file:", use_pkg_file)
        display.display_error(e.message.split(":")[1])
        display.display_error("Exiting")
        sys.exit(1)

    return use_pkg_obj


# ----------------------------------------------------------------------------------------------------------------------
def read_use_pkg_without_delimiters(use_pkg_file):
    """
    Opens a use package file (given by use_pkg_file). This disables the delimiter so that items read are read exactly
    as entered (instead of trying to process key/value pairs).

    :param use_pkg_file: The full path to the use package file.

    :return: A configParser object.
    """

    use_pkg_obj = configparser.ConfigParser(allow_no_value=True,
                                            delimiters="\n",
                                            empty_lines_in_values=True)

    # Force configparser to maintain capitalization of keys
    use_pkg_obj.optionxform = str

    try:
        use_pkg_obj.read(use_pkg_file)
    except configparser.DuplicateOptionError as e:
        display.display_error("Duplicate entries in .use config file:", use_pkg_file)
        display.display_error(e.message.split(":")[1])
        display.display_error("Exiting")
        sys.exit(1)

    return use_pkg_obj


# ----------------------------------------------------------------------------------------------------------------------
def get_use_package_item_list(use_pkg_obj,
                              section,
                              substitutions) -> list:
    """
    Returns a list of the items in the section given by "section". Assumes that these are merely lists (vs. key/value
    pairs) and strips out the empty value to return only what would be the keys.

    :param use_pkg_obj: The config parser object.
    :param section: The section to extract the list of items from.
    :param substitutions: A dictionary of substitutions to perform.

    :return: A list of key/value tuples containing all of the bash commands.
    """

    try:
        output = use_pkg_obj.items(section, raw=True)
    except configparser.NoSectionError:
        return []

    for i in range(len(output)):
        output[i] = output[i][0]

    sorted_substitution_keys = sort_by_length_into_new_list(list(substitutions.keys()))
    for i in range(len(output)):
        for substitution_key in sorted_substitution_keys:
            output[i] = output[i].replace("$" + substitution_key, substitutions[substitution_key])

    return output


# ----------------------------------------------------------------------------------------------------------------------
def get_use_package_key_value_pairs(use_pkg_obj,
                                    section,
                                    substitutions) -> dict:
    """
    Returns all of the items from a specific section of the use_pkg_obj.

    :param use_pkg_obj: The config parser object, delimited.
    :param section: The section from which to extract the key value pairs
    :param substitutions: A dictionary of substitutions to perform.

    :return: A dict containing all of the items, where the key is the name of the item and value is the value it is
             being set to.
    """

    output = dict()
    try:
        items = use_pkg_obj.items(section)
    except (configparser.NoSectionError, configparser.NoOptionError):
        return output

    for item in items:
        output[item[0]] = item[1]

    sorted_substitution_keys = sort_by_length_into_new_list(list(substitutions.keys()))
    for key in output.keys():
        for substitution_key in sorted_substitution_keys:
            output[key] = output[key].replace("$" + substitution_key, substitutions[substitution_key])

    return output


# ----------------------------------------------------------------------------------------------------------------------
def get_use_package_path_appends(use_pkg_obj,
                                 substitutions,
                                 do_prepend=True) -> dict:
    """
    Path prepends and postpends are a special case because there may be multiple sections - one for each path variable -
    and we don't know how many there are ahead of time. Returns a dictionary keyed with the path variable and where the
    value is the path to either prepend or postpend. The path variable is actually embedded in the section name. For
    example:

    [path-prepend-varname]

    where "varname" is the name of the path variable to prepend to.

    :param use_pkg_obj: The config parser object.
    :param substitutions: A dictionary of substitutions to perform.
    :param do_prepend: If True, look for prepends. Otherwise, look at postpends.

    :return: A dictionary where the key is the path variable, and the value is a LIST of paths to either prepend or
             postpend.
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

        sorted_substitution_keys = sort_by_length_into_new_list(list(substitutions.keys()))
        for key in output.keys():
            for substitution_key in sorted_substitution_keys:
                for i in range(len(output[key])):
                    output[key][i] = output[key][i].replace("$" + substitution_key, substitutions[substitution_key])

    return output


# ----------------------------------------------------------------------------------------------------------------------
def format_existing_aliases_into_dict(raw_aliases) -> dict:
    """
    Given a list of strings containing the alias definitions, formats it into a list of key/value tuples.

    :param raw_aliases: A list of strings containing all of the current aliases.

    :return: A dictionary where the key is the alias name and the value is the alias definition.
    """

    reformatted_aliases = dict()

    for raw_alias in raw_aliases:
        raw_alias = raw_alias.split("alias ")[1]
        key = raw_alias.split("=")[0]
        value = raw_alias.split("=")[1].rstrip("\n")
        reformatted_aliases[key] = value.strip("'")

    return reformatted_aliases


# ----------------------------------------------------------------------------------------------------------------------
def get_matching_aliases(new_aliases, existing_aliases):
    """
    Given a list of new aliases and existing aliases, returns a list of existing aliases that are also in new_aliases.

    :param new_aliases: A dictionary of new aliases being created.
    :param existing_aliases: A dictionary of existing aliases.

    :return: A dictionary where the key is the existing alias and the value is the existing value for any aliases that
             are being modified.
    """

    output = dict()

    # Build a list of the new alias names
    for existing_alias in existing_aliases.keys():
        if existing_alias in new_aliases.keys():
            output[existing_alias] = existing_aliases[existing_alias]

    return output


# ----------------------------------------------------------------------------------------------------------------------
def get_matching_env_vars(new_env_vars) -> dict:
    """
    For the env vars listed in the use_pkg_obj, get a list of their current values. Returns a dictionary.

    :param new_env_vars: A dictionary containing the new env vars to be set.

    :return: A dict where the key is each env var name that exists in the current shell that is being modified by the
             use package, and the value is its value prior to being modified.
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


# ----------------------------------------------------------------------------------------------------------------------
def get_matching_paths(path_prepends,
                       path_postpends) -> dict:
    """
    If the existing shell has any paths that are being modified, returns those path variables along with their
    pre-modification values.

    :param path_prepends: A dict of paths that are being modified via prepends.
    :param path_postpends: A dict of paths that are being modified via postpends.

    :return: A dictionary where the key is the name of the existing path that is being modified, and the value is the
             original value of this path before being modified..
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


# ----------------------------------------------------------------------------------------------------------------------
def write_history(shell_obj,
                  use_pkg_name,
                  use_pkg_file,
                  branch,
                  new_aliases,
                  new_env_vars,
                  new_path_prepends,
                  new_path_postpends,
                  use_shell_cmds,
                  unuse_shell_cmds,
                  original_aliases,
                  original_env_vars,
                  original_path_vars):
    """
    Writes the actions being taken by the current use package to a series of env variables in the shell. These settings
    can then be used to undo the changes made by the use command. Included are the original values of any shell alias',
    variables, and paths that are modified by the use command (once again so that they may be reverted to via an unuse
    command.

    :param shell_obj: The shell object responsible for formatting commands for the current shell.
    :param use_pkg_name: The name of the use package (does not include .use)
    :param use_pkg_file: The full name of the use package.
    :param branch: A string representing the branch for this use package.
    :param new_aliases: A dict of values listing the aliases being set in this use package.
    :param new_env_vars: A list of key/value tuples listing the env vars being set in this use package.
    :param new_path_prepends: A list of key/value tuples listing the new path prepends in this use package.
    :param new_path_postpends: A list of key/value tuples listing the new path postpends in this use package.
    :param use_shell_cmds: A list of the single line use cmds.
    :param unuse_shell_cmds: A list of the single line unuse cmds.
    :param original_aliases: A list of key/value tuples listing the existing aliases that will be overwritten by the new
           aliases in this use package.
    :param original_env_vars: A list of key/value tuples listing the existing env vars that will be overwritten by the
           new env vars in this use package.
    :param original_path_vars: A list of key/value tuples listing the existing path vars that will be modified by the
           new path settings in this use package.

    :return: Nothing
    """

    # The main env var is called USE_BRANCHES, and for each use command, an entry is added in the form:
    # branch1,use_pkg_name1,use_pkg_file1:branch2:use_pkg_name2,use_pkg_file2: ... etc.
    # These entries are appended to the end of the list so that the env represents a chronological order of use
    # commands.

    # Associated with this env var is a set of custom env vars PER ENTRY in the USE_BRANCHES var. These are named:
    # USE_<BRANCHNAME>_NEW_ALIASES
    # USE_<BRANCHNAME>_NEW_ENV_VARS
    # USE_<BRANCHNAME>_NEW_PATH_PREPENDS
    # USE_<BRANCHNAME>_NEW_PATH_POSTPENDS
    # USE_<BRANCHNAME>_USE_SHELL_CMDS
    # USE_<BRANCHNAME>_UNUSE_SHELL_CMDS
    # USE_<BRANCHNAME>_ORIGINAL_ALIASES
    # USE_<BRANCHNAME>_ORIGINAL_ENV_VARS
    # USE_<BRANCHNAME>_ORIGINAL_PATH_VARS

    cmd = list()

    # Get the contents of the existing branches already used
    use_branches_env = os.getenv("USE_BRANCHES", "")
    #
    # # Check to see if the branch is already present in USE_BRANCHES. If so, then an error has occurred since an unuse
    # # should have happened first to remove this branch.
    # if use_branches_env.startswith(branch + ",") or ":" + branch + "," in use_branches_env:
    #     msg = "The branch '" + branch + "' still exists in this shell. "
    #     msg += "Auto-unuse may have failed. "
    #     msg += "Unable to run use command. "
    #     msg += "Try creating a new shell and running use in that shell instead."
    #     display.display_error(msg)
    #     sys.exit(1)

    # Append the branch to the USE_BRANCHES env var.
    use_branches_env += ":" + branch + "," + use_pkg_name + "," + use_pkg_file
    use_branches_env = use_branches_env.lstrip(":")
    cmd.append(shell_obj.format_env("USE_BRANCHES", use_branches_env))

    branch_upper = branch.upper()

    # Store the new aliases
    cmd.append(shell_obj.format_env("USE_" + branch_upper + "_NEW_ALIASES", json.dumps(new_aliases)))

    # Store the new env vars
    cmd.append(shell_obj.format_env("USE_" + branch_upper + "_NEW_ENV_VARS", json.dumps(new_env_vars)))

    # Store the new path prepends
    cmd.append(shell_obj.format_env("USE_" + branch_upper + "_NEW_PATH_PREPENDS", json.dumps(new_path_prepends)))

    # Store the new path postpends
    cmd.append(shell_obj.format_env("USE_" + branch_upper + "_NEW_PATH_POSTPENDS", json.dumps(new_path_postpends)))

    # Store the use shell cmds
    cmd.append(shell_obj.format_env("USE_" + branch_upper + "_USE_SHELL_CMDS", json.dumps(use_shell_cmds)))

    # Store the unuse shell cmds
    cmd.append(shell_obj.format_env("USE_" + branch_upper + "_UNUSE_SHELL_CMDS", json.dumps(unuse_shell_cmds)))

    # Store the original aliases
    cmd.append(shell_obj.format_env("USE_" + branch_upper + "_ORIGINAL_ALIASES", json.dumps(original_aliases)))

    # Store the original env vars
    cmd.append(shell_obj.format_env("USE_" + branch_upper + "_ORIGINAL_ENV_VARS", json.dumps(original_env_vars)))

    # Store the original path vars
    cmd.append(shell_obj.format_env("USE_" + branch_upper + "_ORIGINAL_PATH_VARS", json.dumps(original_path_vars)))

    # Export the shell command
    shell_obj.export_shell_command(cmd)


# ----------------------------------------------------------------------------------------------------------------------
def use(shell_obj,
        use_pkg_name,
        raw_aliases,
        settings):
    """
    Uses a new package (given by use_pkg_name). Processes this file and exports the contents converted into bash
    commands.

    :param shell_obj: A shell object to handle shell specific formatting.
    :param use_pkg_name: A name of the use package (not the file name, just the package name. (Eg: clarisse-3.6sp2, and
           not clarisse-3.6sp2.use).
    :param raw_aliases: The contents of the stdin which should hold all of the existing aliases. This is used so that we
           can store what an alias was before we changed it (to set it back when we unuse).
    :param settings: A dictionary containing the settings

    :return: Nothing
    """

    # Find the use package file from this use package name
    use_pkg_file = get_use_pkg_file_from_use_pkg_name(use_pkg_name)
    if use_pkg_file is None:
        display.display_error("No use package named: " + use_pkg_name)
        sys.exit(1)

    permissions.validate_use_pkg_permissions(use_pkg_file)
    use_obj = read_use_pkg(use_pkg_file)
    use_raw_obj = read_use_pkg_without_delimiters(use_pkg_file)

    substitutions = get_built_in_vars(use_pkg_file, settings["auto_version_offset"])

    branch = get_use_package_item_list(use_obj, "branch", substitutions)[0]
    aliases = get_use_package_key_value_pairs(use_obj, "alias", substitutions)
    env_vars = get_use_package_key_value_pairs(use_obj, "env", substitutions)
    path_prepends = get_use_package_path_appends(use_obj, substitutions, True)
    path_postpends = get_use_package_path_appends(use_obj, substitutions, False)
    use_shell_cmds = get_use_package_item_list(use_raw_obj, "use-shell-cmds", substitutions)
    unuse_shell_cmds = get_use_package_item_list(use_raw_obj, "unuse-shell-cmds", substitutions)

    # Check to see if the branch is already present in USE_BRANCHES. If so, then an error has occurred since an unuse
    # should have happened first to remove this branch.
    use_branches_env = os.getenv("USE_BRANCHES", "")
    if use_branches_env.startswith(branch + ",") or ":" + branch + "," in use_branches_env:
        msg = "The branch '" + branch + "' still exists in this shell. "
        msg += "Auto-unuse may have failed. "
        msg += "Unable to run use command. "
        msg += "Try creating a new shell and running use in that shell instead."
        display.display_error(msg)
        sys.exit(1)

    shell_cmds = list()

    for alias in aliases.keys():
        shell_cmds.append(shell_obj.format_alias(alias, aliases[alias]))

    for env_var in env_vars.keys():
        shell_cmds.append(shell_obj.format_env(env_var, env_vars[env_var]))

    # Merge the list of prepend path variables and postpend path variable names into a single, de-duplicated list. So
    # now we have a list of all path variables that we will be modifying.
    path_var_names = list(path_prepends.keys())
    path_var_names.extend(path_postpends.keys())
    path_var_names = list(set(path_var_names))

    # Go through this list and for each variable name, get a list of prepends AND postpends to apply to this variable.
    for path_var_name in path_var_names:

        # Build the list of paths to prepend to this var
        try:
            prepends = path_prepends[path_var_name].copy()
        except KeyError:
            prepends = list()

        # Build the list of paths to postpend to this var
        try:
            postpends = path_postpends[path_var_name]
        except KeyError:
            postpends = list()

        # Remove any actual paths from the postpends if they also exist in the prepends (prepends win).
        postpends = [path for path in postpends if path not in prepends]

        # Get a list of existing paths for this variable (empty list if the variable does not exist)
        try:
            existing = os.environ[path_var_name].split(":")
        except KeyError:
            existing = list()

        # Build a list of existing paths where we remove any of the new paths we are prepending or postpending. This
        # essentially means that if we are prepending or postpending a path that is already a part of the existing var
        # then this path will be removed from the existing var before being added again.
        existing_with_new_paths_removed = [path for path in existing if path not in prepends]
        existing_with_new_paths_removed = [path for path in existing_with_new_paths_removed if path not in postpends]

        # Take the prepends list, and extend it with the existing paths.
        prepends.extend(existing_with_new_paths_removed)

        # Now postpend the postpends list.
        prepends.extend(postpends)

        # Add this command to the shell commands.
        shell_cmds.append(shell_obj.format_path_var(path_var_name, prepends))

    for use_cmd in use_shell_cmds:
        shell_cmds.append(use_cmd)

    # Convert the list of existing aliases to a dictionary
    existing_aliases = format_existing_aliases_into_dict(raw_aliases)

    # Get a list of the new aliases from the use package that already exist in the shell.
    original_aliases = get_matching_aliases(aliases, existing_aliases)

    # Get a list of the new env vars from the use package that already exist in the shell.
    original_env_vars = get_matching_env_vars(env_vars)

    # Get a list of the new path vars from the use package that already exist in the shell.
    original_path_vars = get_matching_paths(path_prepends, path_postpends)

    write_history(shell_obj=shell_obj,
                  use_pkg_name=use_pkg_name,
                  use_pkg_file=use_pkg_file,
                  branch=branch,
                  new_aliases=aliases,
                  new_env_vars=env_vars,
                  new_path_prepends=path_prepends,
                  new_path_postpends=path_postpends,
                  use_shell_cmds=use_shell_cmds,
                  unuse_shell_cmds=unuse_shell_cmds,
                  original_aliases=original_aliases,
                  original_env_vars=original_env_vars,
                  original_path_vars=original_path_vars)

    shell_obj.export_shell_command(shell_cmds)


# ----------------------------------------------------------------------------------------------------------------------
def get_branch_from_use_pkg_name(use_pkg_name):
    """
    Given a use package name, returns the branch name associated with that use package.

    :param use_pkg_name: The name of the use package.

    :return: The branch name from this use package.
    """

    # Find the use package file from this use package name
    use_pkg_file = get_use_pkg_file_from_use_pkg_name(use_pkg_name)
    if use_pkg_file is None:
        display.display_error("No use package named: " + use_pkg_name)
        sys.exit(1)

    # Read the use package file
    use_obj = read_use_pkg(use_pkg_file)

    # Extract the branch
    branch = get_use_package_item_list(use_obj, "branch", {})[0]

    return branch
