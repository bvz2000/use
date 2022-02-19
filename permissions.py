import os.path
import sys

import display

# A list of legal permissions for use packages (those that do not have one of these permissions will not be allowed to
# run for security purposes)
LEGAL_PERMISSIONS = [644, 744, 754, 755, 654, 655, 645]

# Whether to enforce these permissions. Should almost always be set to False when doing development. Whether to set
# these to True for actual production is up to your sense of comfort. The idea behind setting restrictive permissions
# is that this system may call arbitrary commands that may be invisible to the end user if they are not actively
# examining the .use files and checking the provenance of any scripts that these arbitrary commands run.
#
# That said, if someone has compromised your system and installed user-level malicious code, you probably have bigger
# problems than having this system execute this code. Still, the best practice would be to set all of the following
# permission checking flags to True (Note: ALLOW_ARBITRARY_COMMANDS, when set to True, actually is less secure, but it
# is also very useful, therefore it is suggested to leave that enabled unless you really know you do not want to use
# this feature).
#
# There are three options:

# Enforce app permissions means this usemain.py file must be owned by root and only writable by root.
ENFORCE_APP_PERMISSIONS = False

# Enforce use pkg permissions means that any use packages must be owned by root and only writable by root.
ENFORCE_USE_PKG_PERMISSIONS = False

# Allow arbitrary commands, if True, will allow the user to stack any shell commands into a use package and they will
# be run on use and unuse. If False, then this functionality will be disabled.
ALLOW_ARBITRARY_COMMANDS = True

# Show errors for use packages or files that do not meet the permissions requirements, or simply ignore them silently.
DISPLAY_PERMISSIONS_VIOLATIONS = True


# ----------------------------------------------------------------------------------------------------------------------
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
        display.display_error(file_name, "must be owned by root and only writable by root. Exiting.")
    sys.exit(1)


# ----------------------------------------------------------------------------------------------------------------------
def validate_permissions(path, legal_shell_permission_bits):
    """
    Given a file name, verifies that the file is matches the permissions passed by a list given in shellPermissionBitsL.

    :param path: A path to the file to be validates.
    :param legal_shell_permission_bits: A list of permissions that are allowed. These should be passed as a list of
           integers exactly as they would be used in a shell 'chmod' command. For example: 644

    :return: True if the file matches any of the passed permission bits.  False otherwise.
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


# ----------------------------------------------------------------------------------------------------------------------
def validate_use_pkg_permissions(use_pkg_file):
    """
    Makes sure that the passed use package file has the correct permissions.

    :param use_pkg_file: A use package file to verify.

    :return: Nothing.
    """

    # Validate the permissions of the use and unuse scripts.
    if ENFORCE_USE_PKG_PERMISSIONS:
        if not validate_permissions(use_pkg_file, LEGAL_PERMISSIONS):
            handle_permission_violation(use_pkg_file)


# ----------------------------------------------------------------------------------------------------------------------
def validate_app_permissions():
    """
    Makes sure the current python script (permissions) has the correct permissions.

    :return: Nothing.
    """

    if ENFORCE_APP_PERMISSIONS:
        app_path = os.path.split(os.path.abspath(__file__))[0]

        for filename in os.listdir(app_path):
            if not os.path.isdir(filename):
                if not validate_permissions(os.path.abspath(__file__), LEGAL_PERMISSIONS):
                    handle_permission_violation(os.path.abspath(__file__))


# ----------------------------------------------------------------------------------------------------------------------
def validate_arbitrary_shell_permissions():
    """
    Returns whether or not arbitrary shell commands may be run.

    :return: Nothing.
    """

    return ALLOW_ARBITRARY_COMMANDS
