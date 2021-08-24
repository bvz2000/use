#!/usr/bin/env python3

import ast
import os

import display
import permissions

DEBUG = False


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
def merge_dict_of_lists(dict_a,
                        dict_b,
                        deduplicate=False):
    """
    Given two dictionaries who's contents are lists, merges them. If the same key appears in both, then the lists will
    be merged into a single key. If the key only appears in one or the other, then that entire dictionary entry will be
    added to the output as is.

    :param dict_a: The first dictionary who's values are a list.
    :param dict_b: The second dictionary who's values are a list.
    :param deduplicate: If True, then when lists are merged, any duplicate items will be removed.

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


# ----------------------------------------------------------------------------------------------------------------------
def get_subsequent_use_packages(branch) -> dict:
    """
    Given a branch, returns a list of use packages that were invoked AFTER this particular branch's use package was run.

    :param branch: The name of the branch in the history which defines the point after which we want to return results.

    :return: A dictionary containing all of the use packages that were run AFTER the use package associated with the
             branch that was passed. The key is the branch name, and the value is a two item list containing the use
             package name and the use package file path. Note: This dictionary is in no particular order. The only
             guarantee is that all of its elements represent use packages invoked since the one that is associated with
             branch.
    """

    output = dict()

    use_branches = os.getenv("USE_BRANCHES", "")
    use_branches = use_branches.split(":")

    store = False
    for use_branch in use_branches:
        if store:
            output[use_branch.split(",")[0]] = [use_branch.split(",")[1], use_branch.split(",")[2]]
        elif use_branch.split(",")[0] == branch:
            store = True

    return output


# ----------------------------------------------------------------------------------------------------------------------
def remove_paths_from_path_var(shell_obj,
                               path_var,
                               paths_to_remove) -> str:
    """
    Given a path var and a list of paths to remove, removes those paths from the path var. If removing those paths would
    result in an empty path variable, removes the path variable all together.

    :param shell_obj: An object responsible for formatting commands for the current shell type.
    :param path_var: The path var to remove paths from.
    :param paths_to_remove: A list of paths to remove from the path var.

    :return: Nothing.
    """

    # Get the current value of the path var.
    current_path_var_values = os.getenv(path_var, "")

    # If there are no current path var values, then bail.
    if not current_path_var_values:
        return ""
    current_path_var_values = current_path_var_values.split(":")
    if not current_path_var_values:
        return ""

    # Remove the paths
    for path_to_remove in paths_to_remove:
        try:
            current_path_var_values.remove(path_to_remove)
        except ValueError:
            pass

    # If the current_path_var_values is an empty list, remove the path var, otherwise reset it to the new values
    if not current_path_var_values:
        shell_cmds = [shell_obj.unset_env_var(path_var)]
    else:
        shell_cmds = [shell_obj.format_path_var(path_var, current_path_var_values)]

    shell_obj.export_shell_command(shell_cmds)


# ----------------------------------------------------------------------------------------------------------------------
def unuse_paths(shell_obj,
                branch):
    """
    Remove any paths that were added to path variables during the use command.

    Un-using paths follows the following logic:

    If a path was added to a path variable by a use command, remove this path. But ONLY do it if:

    a) The path was not already present for this variable in the shell prior to adding it via the use command.

    b) No other use command since has added this exact same path to this exact same path variable.

    If removing the path would result in an empty variable, remove the variable itself.

    :param shell_obj: An object responsible for formatting commands for the current shell type.
    :param branch: The name of the use branch we are un-using.

    :return: Nothing.
    """

    # Build a dict to hold all of the path vars modified by the use package we are un-using now (along with the actual
    # paths added to these path vars).
    new_paths = dict()
    new_path_vars = os.getenv("USE_" + branch.upper() + "_NEW_PATH_PREPENDS", "{}")
    new_path_vars = ast.literal_eval(new_path_vars)
    new_paths = merge_dict_of_lists(new_paths, new_path_vars)
    new_path_vars = os.getenv("USE_" + branch.upper() + "_NEW_PATH_POSTPENDS", "{}")
    new_path_vars = ast.literal_eval(new_path_vars)
    new_paths = merge_dict_of_lists(new_paths, new_path_vars)

    # Build a dict to hold any of these path vars that existed before the use package had modified them (along with the
    # original values of these path vars).
    original_paths = dict()
    original_path_vars = os.getenv("USE_" + branch.upper() + "_ORIGINAL_PATH_VARS", "{}")
    original_path_vars = ast.literal_eval(original_path_vars)
    original_paths = merge_dict_of_lists(original_paths, original_path_vars)

    # Build a list of all path vars modified by subsequent use packages (along with the paths added to these vars)
    subsequent_paths = dict()
    subsequent_branches = get_subsequent_use_packages(branch)
    for subsequent_branch in subsequent_branches.keys():
        # Get the paths set by the subsequent branch
        subsequent_path_vars = os.getenv("USE_" + subsequent_branch.upper() + "_NEW_PATH_PREPENDS", "{}")
        subsequent_path_vars = ast.literal_eval(subsequent_path_vars)
        subsequent_paths = merge_dict_of_lists(subsequent_paths, subsequent_path_vars)
        subsequent_path_vars = os.getenv("USE_" + subsequent_branch.upper() + "_NEW_PATH_POSTPENDS", "")
        subsequent_path_vars = ast.literal_eval(subsequent_path_vars)
        subsequent_paths = merge_dict_of_lists(subsequent_paths, subsequent_path_vars)

    # Evaluate each path var separately
    for path_var in new_paths.keys():

        new_path_values = new_paths[path_var]
        try:
            original_path_values = original_paths[path_var]
        except KeyError:
            original_path_values = list()
        try:
            subsequent_path_values = subsequent_paths[path_var]
        except KeyError:
            subsequent_path_values = list()

        # Build a list of paths that we will be removing from the path var. Start by assuming that we will remove all
        # the paths that the use package that we are un-using had added.
        # Now remove from this any identical paths that were in subsequent use packages (if a subsequent use package
        # added the exact same path to the exact same path var, then we don't want to remove it).
        paths_to_remove = [path for path in new_path_values if path not in subsequent_path_values]

        # Now remove from this any identical paths that had already existed in this variable before the use package had
        # tried to add them (if the use package tries to add a path to a path var, and that path is already there, it
        # does nothing. So we should not remove it when un-using).
        paths_to_remove = [path for path in paths_to_remove if path not in original_path_values]

        remove_paths_from_path_var(shell_obj, path_var, paths_to_remove)


# ----------------------------------------------------------------------------------------------------------------------
def format_existing_aliases_into_dict(raw_aliases) -> dict:
    """
    Given a raw set of aliases, re-formats them into a dictionary.

    :param raw_aliases: A list of "raw aliases" in the form of strings. These are formatted like "alias test='value'"

    :return: A dictionary where the key is the alias name and the value is the contents of the alias
    """

    output = dict()

    for alias in raw_aliases:
        alias_name = alias.split("=")[0].split(" ")[1]
        output[alias_name] = alias.split("=")[1].strip("\n").strip("'")

    return output


# ----------------------------------------------------------------------------------------------------------------------
def unuse_aliases(shell_obj,
                  branch,
                  raw_aliases):
    """
    Undoes the aliases set by the use package we are un-using. It follows the following logic:

    If the alias does not exist in the current shell, or if the alias still exists in the current shell but is different
    than the value set by the use package, then something has actively changed it since we ran the use command. We do
    not want to override this decision, so do nothing.

    If the alias still exists in the current shell but is the same as the value set by the use package, then it is still
    possible that a subsequent use command has touched it since the use command we are un-using was issued. Check for
    this case, and if it turns out to be what has happened, do nothing.

    If the alias exists in the current shell and has the same value that the use package had set it to and no subsequent
    use package has set it to the same value, then do two final checks:

    a) If the alias did not exist prior to us running the use package, we should unset this alias so that it no longer
       exists.

    b) If the alias did exist prior to us running the use package, then we should reset this alias to that value.

    :param shell_obj: An object responsible for formatting commands for the current shell type.
    :param branch: The name of the use branch we are un-using.
    :param raw_aliases: The stdIn that contains the aliases as they exist in the current shell.

    :return: A string of semi-colon separated commands to either reset or
             unset the aliases that were set by the use command.
    """

    # Build a dict to hold all of the aliases modified by the use package we are un-using now (along with the actual
    # values of these aliases).
    new_aliases = os.getenv("USE_" + branch.upper() + "_NEW_ALIASES", "{}")
    new_aliases = ast.literal_eval(new_aliases)

    # Build a dict to hold any of these aliases that existed before the use package had modified them (along with the
    # original values of these aliases).
    original_aliases = os.getenv("USE_" + branch.upper() + "_ORIGINAL_ALIASES", "{}")
    original_aliases = ast.literal_eval(original_aliases)

    # Build a dict of all aliases modified by subsequent use packages (along with the values set for these aliases)
    subsequent_aliases = dict()
    subsequent_branches = get_subsequent_use_packages(branch)
    for subsequent_branch in subsequent_branches.keys():
        # Get the aliases set by the subsequent branch
        subsequent_alias_vars = os.getenv("USE_" + subsequent_branch.upper() + "_NEW_ALIASES", "{}")
        subsequent_alias_vars = ast.literal_eval(subsequent_alias_vars)
        subsequent_aliases = merge_dict_of_lists(subsequent_aliases, subsequent_alias_vars)

    # Build a dict of the existing aliases
    current_aliases = format_existing_aliases_into_dict(raw_aliases)

    # Evaluate each alias separately
    for alias_name in new_aliases.keys():

        # Get the value of the alias as set by the use package.
        new_alias_value = new_aliases[alias_name]

        # Get the current value of the alias. If it is no longer in the current shell, then something else has changed
        # it and we don't want to touch it. Just bail.
        try:
            current_alias_value = current_aliases[alias_name]
        except KeyError:
            continue

        # Check to see if the current value of the alias is different than what it was set to by the use package we are
        # un-using. If it is different, then something else has touched the alias since we set it via the use package,
        # so we don't want to touch it. Just bail.
        if current_alias_value != new_alias_value:
            continue

        # The current value matches the value set by the use package. Check to see if any subsequent use packages have
        # touched this alias in any way (if so, once again we don't want to touch it then, so bail).
        if alias_name in subsequent_aliases.keys():
            continue

        # Apparently nothing has touched this alias since we set it via the use package (there is a big exception here
        # in that another, non-use script or process may have set this alias to be exactly what this use package set it
        # to. There is no way to test for this event so we just have to hope that that was not the case. It seems like
        # it would be an edge case to be sure. Since nothing else has touched it (we think) set this value back to what
        # it was before the use package changed it. If it did not exist, remove the alias.
        if alias_name in original_aliases:
            shell_obj.export_shell_command([shell_obj.format_alias(alias_name, original_aliases[alias_name])])
        else:
            shell_obj.export_shell_command([shell_obj.unalias(alias_name)])


# ----------------------------------------------------------------------------------------------------------------------
def unuse_env_vars(shell_obj,
                   branch):
    """
    Undoes the env vars set by the use package we are un-using. It follows the following logic:

    If the env var does not exist in the current shell, or if the env var still exists in the current shell but is
    different than the value set by the use package, then something has actively changed it since we ran the use
    command. We do not want to override this decision, so do nothing.

    If the env var still exists in the current shell but is the same as the value set by the use package, then it is
    still possible that a subsequent use command has touched it since the use command we are un-using was issued. Check
    for this case, and if it turns out to be what has happened, do nothing.

    If the env var exists in the current shell and has the same value that the use package had set it to and no
    subsequent use package has set it to the same value, then do two final checks:

    a) If the env var did not exist prior to us running the use package, we should remove this var so that it no longer
       exists.

    b) If the env var did exist prior to us running the use package, then we should reset this var to that value.

    :param shell_obj: An object responsible for formatting commands for the current shell type.
    :param branch: The name of the use branch we are un-using.

    :return: Nothing.
    """

    # Build a dict to hold all of the env vars modified by the use package we are un-using now (along with the actual
    # values of these vars).
    new_vars = os.getenv("USE_" + branch.upper() + "_NEW_ENV_VARS", "{}")
    new_vars = ast.literal_eval(new_vars)

    # Build a dict to hold any of these env vars that existed before the use package had modified them (along with the
    # original values of these vars).
    original_vars = os.getenv("USE_" + branch.upper() + "_ORIGINAL_ENV_VARS", "{}")
    original_vars = ast.literal_eval(original_vars)

    # Build a dict of all env vars modified by subsequent use packages (along with the values set for these vars)
    subsequent_vars = dict()
    subsequent_branches = get_subsequent_use_packages(branch)
    for subsequent_branch in subsequent_branches.keys():
        # Get the env vars set by the subsequent branch
        subsequent_env_vars_vars = os.getenv("USE_" + subsequent_branch.upper() + "_NEW_ENV_VARS", "{}")
        subsequent_env_vars_vars = ast.literal_eval(subsequent_env_vars_vars)
        subsequent_vars = merge_dict_of_lists(subsequent_vars, subsequent_env_vars_vars)

    # Evaluate each env var separately
    for env_var_name in new_vars.keys():

        # Get the value of the env var as set by the use package.
        new_env_var_value = new_vars[env_var_name]

        # Get the current value of the env var. If it is no longer in the current shell, then something else has changed
        # it and we don't want to touch it. Just bail.
        current_env_var_value = os.getenv(env_var_name, None)
        if current_env_var_value is None:
            return

        # Check to see if the current value of the env var is different than what it was set to by the use package we
        # are un-using. If it is different, then something else has touched the env var since we set it via the use
        # package, so we don't want to touch it. Just bail.
        if current_env_var_value != new_env_var_value:
            return

        # The current value matches the value set by the use package. Check to see if any subsequent use packages have
        # touched this env var in any way (if so, once again we don't want to touch it then, so bail).
        if env_var_name in subsequent_vars.keys():
            return

        # Apparently nothing has touched this env var since we set it via the use package (there is a big exception here
        # in that another, non-use script or process may have set this var to be exactly what this use package set it
        # to. There is no way to test for this event so we just have to hope that that was not the case. It seems like
        # it would be an edge case to be sure. Since nothing else has touched it (we think) set this value back to what
        # it was before the use package changed it. If it did not exist, remove the env var.
        if env_var_name in original_vars:
            shell_obj.export_shell_command([shell_obj.format_env(env_var_name, original_vars[env_var_name])])
        else:
            shell_obj.export_shell_command([shell_obj.unset_env_var(env_var_name)])


# ----------------------------------------------------------------------------------------------------------------------
def run_unuse_cmds(shell_obj,
                   branch):
    """
    Simply runs any unuse shell commands that were added by the user to the use package.

    :param shell_obj: An object responsible for formatting commands for the current shell type.
    :param branch: The name of the use branch we are un-using.

    :return: Nothing.
    """

    unuse_shell_cmds = os.getenv("USE_" + branch.upper() + "_UNUSE_SHELL_CMDS", "{}")
    unuse_shell_cmds = ast.literal_eval(unuse_shell_cmds)
    for cmd in unuse_shell_cmds:
        shell_obj.export_shell_command([cmd])


# ----------------------------------------------------------------------------------------------------------------------
def unuse(shell_obj,
          branch_name,
          raw_aliases):
    """
    Given a use_pkg_name this will find the most recent version in the history and try to undo whatever that use command
    did. This process tries not to step on any identical settings that may have been set as a consequence of another use
    package that has been run since that time, OR any manual changes to the environment set by the user. There are
    limitations to this process though. If the user sets an alias, env var, or path to an identical setting to the use
    package (but does it manually or via another script after running the use package) this process will "undo" that.
    Though that said, technically they did not actually do anything since those settings are identical to what was
    already set. That said, the end user will justifiably not see it that way. Hopefully this is a fairly edge case that
    does not come up often.

    :param shell_obj: An object responsible for formatting commands for the current shell type.
    :param branch_name: The name of the branch of the use package we are un-using.
    :param raw_aliases: The list of raw alias strings.

    :return: Nothing.
    """

    branches = os.getenv("USE_BRANCHES", "").split(":")
    if branches == ['']:
        return

    branch_names = list()
    for branch in branches:
        branch_names.append(branch.split(",")[0])

    # If this branch does not exist in the history, do nothing
    if branch_name not in branch_names:
        return

    # A full unuse does the following:

    # 1) removes any added paths to any path variables - unless any other use package before or after has also added
    #    that same path, or the path already existed in that path variable.
    unuse_paths(shell_obj, branch_name)

    # 2) resets any changed aliases back to what it was- unless that alias is different than what it was changed to
    #    (i.e. another process has changed it since the use command) - OR - a subsequent use command has touched this
    #    same alias (even if it is to change it to the same value).
    unuse_aliases(shell_obj, branch_name, raw_aliases)

    # 3) resets any changed env vars back to what it was - unless that env var is different than what it was changed to
    #    (i.e. another process has changed it since the use command) - OR - a subsequent use command has touched this
    #    same env variable (even if it is to change it to the same value).
    unuse_env_vars(shell_obj, branch_name)

    # 4) run the raw unuse commands from the use package. These are just arbitrary shell commands that the user has
    #    added to the use package. There is no validation done. These are simply just run.
    if permissions.validate_arbitrary_shell_permissions():
        run_unuse_cmds(shell_obj, branch_name)

    # 5) remove the env vars specific to this branch
    cleanup_cmds = list()
    cleanup_cmds.append("unset USE_" + branch_name.upper() + "_ORIGINAL_PATH_VARS")
    cleanup_cmds.append("unset USE_" + branch_name.upper() + "_USE_SHELL_CMDS")
    cleanup_cmds.append("unset USE_" + branch_name.upper() + "_ORIGINAL_ALIASES")
    cleanup_cmds.append("unset USE_" + branch_name.upper() + "_UNUSE_SHELL_CMDS")
    cleanup_cmds.append("unset USE_" + branch_name.upper() + "_ORIGINAL_ENV_VARS")
    cleanup_cmds.append("unset USE_" + branch_name.upper() + "_NEW_PATH_POSTPENDS")
    cleanup_cmds.append("unset USE_" + branch_name.upper() + "_NEW_PATH_PREPENDS")
    cleanup_cmds.append("unset USE_" + branch_name.upper() + "_NEW_ENV_VARS")
    cleanup_cmds.append("unset USE_" + branch_name.upper() + "_NEW_ALIASES")
    shell_obj.export_shell_command(cleanup_cmds)

    # 6) and, finally, remove this branch from the USE_BRANCHES env.
    use_branches_env = os.getenv("USE_BRANCHES", "")
    use_branches_env = use_branches_env.split(":")
    new_use_branches = list()
    for use_branch in use_branches_env:
        if use_branch.split(",")[0] != branch_name:
            new_use_branches.append(use_branch)
    new_use_branches = ":".join(new_use_branches)
    shell_obj.export_shell_command(["export USE_BRANCHES=" + new_use_branches])
