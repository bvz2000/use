#!/usr/bin/env python3

import os


# ----------------------------------------------------------------------------------------------------------------------
def used(shell_obj):
    """
    Reads the history env var and returns a list of all used packages in the current shell.

    :param shell_obj: The object responsible for formatting commands for the shell.

    :return: Nothing.
    """

    used_pkg_names = list()

    history_env = os.getenv("USE_BRANCHES", "")
    if history_env:
        branches = history_env.split(":")
        for branch in branches:
            used_pkg_names.append(branch.split(",")[1])

    cmd = ['printf "' + r'\n'.join(used_pkg_names) + r'\n' + '"']
    shell_obj.export_shell_command(cmd)
