#!/usr/bin/env python3

import sys


# ----------------------------------------------------------------------------------------------------------------------
def display_usage():
    """
    Prints the usage string. Note: because most of the output of this script is intended to be processed by a calling
    shell script using 'eval', the usage string will be printed to stdErr to prevent it from being processed as a
    command.

    :return: Nothing.
    """

    display_error("Usage")


# ----------------------------------------------------------------------------------------------------------------------
def display_error(*msgs,
                  quit_after_display=False):
    """
    Displays a message to the stdErr

    :param msgs: An arbitrary list of items to display. Each item will be converted to a string before being displayed.
    All items will be displayed on a single line.
    :param quit_after_display: If true, then the system will exit after displaying the message. Defaults to False.

    :return: Nothing.
    """

    message = ""
    for item in msgs:
        message += str(item) + " "
    print(message.strip(" "), file=sys.stderr)

    if quit_after_display:
        sys.exit(0)
