#!/usr/bin/env python3

import os
import sys

import completions
import display
import envmapping
import permissions
import setup
import shell
import use
import used
import unuse


LEGAL_COMMANDS = [
    "complete_unuse",
    "complete_use",
    "config",
    "setup",
    "refresh",
    "unuse",
    "get_branch_from_use_pkg_name",
    "use",
    "used",
    "which",
    "symlink_latest",
    "update_desktop",
    "test",
]

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
# using an env variable set below. More than one path may be supplied by using
# the format: /path/number/1/:/path/number/2/:/path/number/3/ etc.
DEFAULT_USE_PKG_AV_PATHS = "/opt/apps/"

# Where to look for baked version use packages. This setting can be overridden
# by using an env variable set below. More than one path may be supplied by
# using the format: /path/number/1/:/path/number/2/:/path/number/3/ etc.
DEFAULT_USE_PKG_BV_PATHS = "/opt/use/"

# Whether to search sub-directories of the use package paths. This setting can
# be overridden by using an env variable set below.
DEFAULT_DO_RECURSIVE_SEARCH = True


# ----------------------------------------------------------------------------------------------------------------------
def read_user_settings_from_env():
    """
    Reads some specific settings from the env. If they are missing, then it uses the built in constants.

    :return: a dictionary containing the values of the env settings. If any of these settings are missing from the env,
             then the globals will be substituted.
    """

    output = dict()

    # Auto Version Search paths (converted to a list)
    output["pkg_av_search_paths"] = os.getenv(envmapping.USE_PKG_AV_SEARCH_PATHS_ENV, DEFAULT_USE_PKG_AV_PATHS)
    output["pkg_av_search_paths"] = output["pkg_av_search_paths"].split(":")

    # Baked Version Search paths (converted to a list)
    output["pkg_bv_search_paths"] = os.getenv(envmapping.USE_PKG_BV_SEARCH_PATHS_ENV, DEFAULT_USE_PKG_BV_PATHS)
    output["pkg_bv_search_paths"] = output["pkg_bv_search_paths"].split(":")

    # Whether to search recursively, converted to a boolean
    output["do_recursive_search"] = os.getenv(envmapping.USE_PKG_SEARCH_RECURSIVE_ENV, str(DEFAULT_DO_RECURSIVE_SEARCH))
    if output["do_recursive_search"].upper() not in ["TRUE", "FALSE"]:
        msg = "Environmental variable: " + envmapping.USE_PKG_SEARCH_RECURSIVE_ENV
        msg += " must be either 'True' or 'False'. Exiting."
        display.display_error(msg)
        sys.exit(1)
    if output["do_recursive_search"].upper() == "TRUE":
        output["do_recursive_search"] = True
    else:
        output["do_recursive_search"] = False

    # Get the default offset for auto versions, converted to an integer
    output["auto_version_offset"] = os.getenv(envmapping.USE_PKG_AUTO_VERSION_OFFSET_ENV, DEFAULT_AUTO_VERSION_OFFSET)
    try:
        output["auto_version_offset"] = int(output["auto_version_offset"])
    except ValueError:
        msg = "Environmental variable: " + envmapping.USE_PKG_AUTO_VERSION_OFFSET_ENV
        msg += " must be an integer. Exiting."
        display.display_error(msg)
        sys.exit(1)

    return output


# ----------------------------------------------------------------------------------------------------------------------
def main():
    """
    Main entry point for the python portion of the app.

    sys.argv[1] is the name of the shell type (bash, tcsh, etc.) that is being used.

    sys.argv[2] is the name of the command that is to be run.

    :return: Nothing.
    """

    # Make sure this script is owned by root and only writable by root.
    permissions.validate_app_permissions()

    # Create a shell object to handle shell specific tasks
    shell_obj = shell.Shell(sys.argv[1])

    # Only handle specific types of requests
    if sys.argv[2] not in LEGAL_COMMANDS:
        display.display_error("Unknown command: " + sys.argv[2])
        display.display_usage()
        sys.exit(1)

    # Read the env and stuff its settings into the constants
    settings = read_user_settings_from_env()

    # ===========================
    if sys.argv[2] == "setup":
        setup.setup(shell_obj, settings)
        sys.exit(0)

    # ===========================
    if sys.argv[2] == "refresh":
        setup.setup(shell_obj, settings)
        sys.exit(0)

    # ===========================
    if sys.argv[2] == "complete_use":
        completions.complete_use(sys.argv[3])

    # ===========================
    if sys.argv[2] == "complete_unuse":
        completions.complete_unuse(sys.argv[3])

    # ===========================
    if sys.argv[2] == "use":
        if len(sys.argv) != 4:
            display.display_error("use: Wrong number of arguments.")
            sys.exit(1)
        stdin = list(sys.stdin)  # List of existing aliases in the shell. Used to store for history and unuse purposes.
        use.use(shell_obj, sys.argv[3], stdin, settings)

    # ===========================
    if sys.argv[2] == "used":
        used.used(shell_obj)

    # ===========================
    if sys.argv[2] == "unuse":
        stdin = list(sys.stdin)  # List of existing aliases in the shell. Used to store for history and unuse purposes.
        if len(sys.argv) > 3:
            branch_name = use.get_branch_from_use_pkg_name(sys.argv[3])
            unuse.unuse(shell_obj, branch_name, stdin)

    # ===========================
    if sys.argv[2] == "get_branch_from_use_pkg_name":
        branch_name = use.get_branch_from_use_pkg_name(sys.argv[3])
        print(branch_name)


if __name__ == "__main__":
    main()
