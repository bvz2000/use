#!/usr/bin/env python3

import os

import envmapping


# ----------------------------------------------------------------------------------------------------------------------
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


# ----------------------------------------------------------------------------------------------------------------------
def get_use_package_names_and_paths_from_env():
    """
    Returns a dictionary of use package names and their full paths from the env. If more than one use package has the
    exact same name, only one will be returned. Which particular one is returned is undefined.

    :return: A dict of full paths to (resolved) use package files keyed on their name (which may or may not include an
             added version number).
    """

    output = dict()
    env = os.environ[envmapping.USE_PKG_AVAILABLE_PACKAGES_ENV]
    env = env.split(":")
    for item in env:
        output[item.split("@")[0]] = item.split("@")[1]
    return output


# ----------------------------------------------------------------------------------------------------------------------
def get_use_package_names_from_env():
    """
    Returns a list of use package names only from the env. If more than one use package has the exact same name, only
    one will be returned. Which particular one is returned is undefined.

    :return: A list of use package names (de-duplicated)
    """

    use_pkgs = get_use_package_names_and_paths_from_env()
    return use_pkgs.keys()


# ----------------------------------------------------------------------------------------------------------------------
def complete_use(stub):
    """
    Given a stub, collects all of the use packages that start with this text. Exports these items to stdOut as a
    newline-delimited string.

    This is the corresponding bash function needed to provide tab completion using this feature:
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
    print("\n".join(outputs))


# ----------------------------------------------------------------------------------------------------------------------
def complete_unuse(stub):
    """
    Given a stub, collects all of the use packages that have already been used that start with this stub.

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
    use_pkgs = os.getenv("USE_BRANCHES", "")
    use_pkgs = use_pkgs.split(":")
    if use_pkgs == ['']:
        return
    for use_pkg in use_pkgs:
        branch, usepackage, path = use_pkg.split(",")
        if usepackage.startswith(stub):
            outputs.append(usepackage)
    print("\n".join(outputs))
