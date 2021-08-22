#!/usr/bin/env python3

import os.path
import sys

import display
import permissions
import envmapping


# ----------------------------------------------------------------------------------------------------------------------
def get_version_path(use_pkg_path,
                     path_offset):
    """
    Gets the version path from the use pkg path. Note: This is different than getting the version. This returns a full
    path to the version, not just the version number itself. It uses the path_offset to find which parent dir is the
    version dir. This may be either a positive or negative number (only the absolute value is used). For example, if the
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


# ----------------------------------------------------------------------------------------------------------------------
def get_version(use_pkg_path,
                path_offset):
    """
    Gets the version number automatically from the path. It uses the path_offset to find which parent dir is the version
    dir. May be either a positive or negative number (only the absolute value is used). For example, if the offset is 2
    and the path to the use pkg is:

    /opt/apps/isotropix/clarisse/2.0sp1/wrapper/clarisse.use

    then the version will be found two steps up the path from the use file, (in this case, "2.0sp1").

    :param use_pkg_path: The path to the use package we want to get the version from.
    :param path_offset: The number of paths to step up through to find the version number. Can be either a positive or
           negative value (only the absolute value is used).

    :return: A string containing the version.
    """

    remaining_path = get_version_path(use_pkg_path, path_offset)

    return os.path.split(remaining_path)[1]


# ----------------------------------------------------------------------------------------------------------------------
def evaluate_use_pkg_file(file_n,
                          dir_n,
                          auto_version,
                          auto_version_offset,
                          enforce_use_pkg_permissions):
    """
    Given a path to a file, evaluates whether it is a use pkg file or not. If it is, returns a tuple containing the use
    package name (including version, and a path to this use package).

    :param file_n: A path to a file.
    :param dir_n: The path where the file is located.
    :param auto_version: If True, then the version number will be added just before the .use. This version number will
           be extracted from the path. It will be added in the format: "-<version>". For example: if the path to a .use
           file is /opt/apps/isotropix/clarisse/3.6sp7/wrapper/clarisse.use, then an offset of 2 would make the
           resulting use package become clarisse-3.6sp7.use (where the version is "3.7sp7").
    :param auto_version_offset: The offset that indicates which parent directory defines the version number. 1 = use
           package directory. 2 = parent of use package directory, 3 = grandparent, etc.
    :param enforce_use_pkg_permissions: If true, then the use package will have its permissions checked and an error
           raised if it does not have the correct permissions.

    :return: A tuple where the first element is the name of the use package file (munged to include the version number
             if auto_version is true), and the second value is the path to the use package file. If the file is not a
             valid use package or if it fails permission validation, returns None.
    """

    if file_n.endswith(".use"):
        full_p = os.path.join(dir_n, file_n)
        if enforce_use_pkg_permissions:
            if not permissions.validate_permissions(full_p, permissions.LEGAL_PERMISSIONS):
                permissions.handle_permission_violation(full_p)
                return None
        if auto_version:
            version = get_version(full_p, auto_version_offset)
            file_n = os.path.splitext(file_n)[0]
            file_n += "-" + version + os.path.splitext(file_n)[1]
        else:
            file_n = os.path.splitext(file_n)[0]
        return file_n, full_p
    return None


# ----------------------------------------------------------------------------------------------------------------------
def find_all_use_pkg_files(search_paths,
                           auto_version,
                           auto_version_offset,
                           recursive):
    """
    Searches the given paths and locates any use packages in these paths:

    :param search_paths: A list of paths where the use packages could live.
    :param auto_version: If True, then the version number will be added just before the .use. This version number will
           be extracted from the path. So if the path has the string "4.0sp1" in it, then that string will be extracted
           and added to the name of the use package. It will be added in the format: "-<version>". For example: if the
           path is /opt/apps/isotropix/clarisse/3.6sp7 then "clarisse.use" would be reported to actually be
           clarisse-3.6sp7.use (where the version is "3.6sp7" and was extracted from the path).
    :param auto_version_offset: The offset that indicates which parent directory defines the version number. 1 = use
           package directory. 2 = parent of use package directory, 3 = grandparent of use package directory, etc. For
           example, if the path to the use package is /opt/apps/isotropix/clarisse/3.6sp7/wrapper/clarisse.use then
           an offset of 2 would return the value "3.6sp7".
    :param recursive: If true, then all sub-dirs of the search paths will be
           traversed as well.

    :return: A dictionary of use package file names where the key is the name of the use package, and the value is the
             full path to this use package.
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
                                                       auto_version_offset,
                                                       permissions.ENFORCE_USE_PKG_PERMISSIONS)
                        if result:
                            use_pkg_files[result[0]] = result[1]

            else:
                files_n = os.listdir(search_path)
                for file_n in files_n:
                    result = evaluate_use_pkg_file(file_n,
                                                   search_path,
                                                   auto_version,
                                                   auto_version_offset,
                                                   permissions.ENFORCE_USE_PKG_PERMISSIONS)
                    if result:
                        use_pkg_files[result[0]] = result[1]

    return use_pkg_files


# ----------------------------------------------------------------------------------------------------------------------
def make_write_use_pkgs_to_env_shellcmd(shell_obj,
                                        av_search_paths,
                                        bv_search_paths,
                                        auto_version_offset,
                                        recursive):
    """
    Finds all of the use packages and then creates a shell command that writes their names to an env var in the format:

    name1@path1:name2@path2:...:nameN@pathN

    where "name" is the name of the use package, and path is the path to the use package config file.

    :param shell_obj: An object to handle shell specific tasks.
    :param av_search_paths: A list of paths where the auto version use packages
           could live.
    :param bv_search_paths: A list of paths where the baked version use packages
           could live.
    :param auto_version_offset: The offset that indicates which parent directory
           defines the version number. 1 = use package directory. 2 = parent
           of use package directory, 3 = grandparent, etc.
    :param recursive: If true, then all sub-dirs of the search paths will be
           traversed as well.

    :return: A string that is the shell command to create the env var.
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

    # Transfer all the baked use packages to the auto use packages dict (so we only have a single dict to deal with)
    # This will also deal with duplicate use package names between baked use packages and auto use packages, where the
    # auto-use package always wins.
    for key in bv_use_pkgs.keys():
        if key not in av_use_pkgs.keys():
            av_use_pkgs[key] = bv_use_pkgs[key]

    # Convert the dict to be a list in the form of ["key1@value1", "key2@value2", ... "keyN@valueN"]
    for use_pkg in av_use_pkgs.keys():
        use_pkg_files.append(use_pkg + "@" + av_use_pkgs[use_pkg])

    output = shell_obj.format_path_var(envmapping.USE_PKG_AVAILABLE_PACKAGES_ENV, use_pkg_files)

    return output


# ----------------------------------------------------------------------------------------------------------------------
def setup(shell_obj,
          settings):
    """
    Does the setup for the current shell. Needs to be run once per shell before the system is usable.

    :param shell_obj: An object to handle shell specific tasks.
    :param settings: The settings dictionary.

    :return: Nothing.
    """

    output = list()

    # # Check to see if there is already a use history file for this shell.
    # # Create one if needed.
    # try:
    #     use_history_file = os.environ[USE_PKG_HISTORY_FILE_ENV]
    # except KeyError:
    #     f, use_history_file = tempfile.mkstemp(suffix=".usehistory", text=True)
    #
    # # Store this file name in the form of an environmental variable.
    # output.append(shell.format_env(USE_PKG_HISTORY_FILE_ENV, use_history_file))
    # # output = "export " + USE_PKG_HISTORY_FILE_ENV + "=" + use_history_file

    legal_path_found = False

    # Start by validating that we have actually found some legal search paths. (making sure that we handle cases where
    # the user passed in a "~" instead of an explicit path)
    for path in settings["pkg_av_search_paths"]:
        path = os.path.expanduser(path)
        if os.path.exists(path) and os.path.isdir(path):
            legal_path_found = True
    for path in settings["pkg_bv_search_paths"]:
        path = os.path.expanduser(path)
        if os.path.exists(path) and os.path.isdir(path):
            legal_path_found = True

    if not legal_path_found:
        display.display_error("No use package directories found. I looked for:",
                              ":".join(settings["pkg_av_search_paths"]),
                              "and",
                              ":".join(settings["pkg_bv_search_paths"]))
        sys.exit(1)

    # Store the auto version use package search paths in an env var
    # output.append(shell.format_path_var(USE_PKG_AV_SEARCH_PATHS_ENV, settings["pkg_av_search_paths"]))

    # Store the baked version use package search paths in an env var
    # output.append(shell.format_path_var(USE_PKG_BV_SEARCH_PATHS_ENV, settings["pkg_bv_search_paths"]))

    # Save the existing use packages to an env var
    output.append(make_write_use_pkgs_to_env_shellcmd(shell_obj,
                                                      settings["pkg_av_search_paths"],
                                                      settings["pkg_bv_search_paths"],
                                                      settings["auto_version_offset"],
                                                      settings["do_recursive_search"]))

    # Export these env variables.
    shell_obj.export_shell_command(output)
