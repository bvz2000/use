#!/usr/bin/env python

import ast
import configparser
import os
import sys
import tempfile


#LEGAL_COMMANDS = ["setup",
#                  "complete",
#                  "use",
#                  "used",
#                   "unuse",
#                   "which",
#                   "config",
#                   "writehistory",
#                   "processStdIn"]
legalPermissionsL = [644, 744, 754, 755, 654, 655, 645]
enforcePermissions = False
displayPermissionViolations = False
defaultUsePkgPathsL = ["/opt/use", "/home/bvz/Documents/dev/use/"]


# --------------------------------------------------------------------------------------------------
def exportStdIn():
    """
    Takes the StdIn exports it to StdOut as a python list.

    :return: Nothing.
    """

    exportShellCommand(str(sys.stdin))


# --------------------------------------------------------------------------------------------------
def display_usage():
    """
    Prints the usage string. Note: because most of the output of this script is intended to be
    processed by a calling shell script using 'eval', the usage string will be printed to stdErr
    to prevent it from being processed as a command.

    :return: Nothing.
    """

    displayError("Usage")


# --------------------------------------------------------------------------------------------------
def displayError(*msgsL):
    """
    Displays a message to the stdErr

    :param msgsL: An arbitrary list of items to display. Each item will be converted to a string
           before being displayed. All items will be displayed on a single line.

    :return: Nothing.
    """

    message = ""
    for item in msgsL:
        message += str(item) + " "
    print(message.strip(" "), file=sys.stderr)


# --------------------------------------------------------------------------------------------------
def exportShellCommand(cmd):
    """
    Exports the command for the calling bash shell script to process. Pretty simple, it just prints
    the command.

    :param cmd: The command to pass back to the calling shell script.

    :return: Nothing.
    """

    # Pretty easy, just print it to stdOut.
    print(cmd)


# --------------------------------------------------------------------------------------------------
def validatePermissions(path, shellPermissionBitsL):
    """
    Given a file name, verifies that the file is matches the permissions passed by a list given in
    shellPermissionBitsL.

    :param path: A path to the file to be validates.
    :param shellPermissionBitsL: A list of permissions that are allowed. These should be passed as a
           list of integers exactly as they would be used in a shell 'chmod' command.
           For example: 644

    :return: True if the file matches any of the passed permission bits.  False otherwise.
    """

    # Contract
    assert(os.path.exists(path))
    assert(not(os.path.isdir(path)))
    assert(type(shellPermissionBitsL) is list)

    # Verify that the file is owned by root and is only writable by root.
    if os.stat(path).st_uid != 0:
        return False

    if int(oct(os.stat(path).st_mode)[-3:]) not in shellPermissionBitsL:
        return False

    return True


# --------------------------------------------------------------------------------------------------
def handlePermissionViolation(fileName):
    """
    Handles a permission violation for a particular file. Normally we just display an error message
    and exit. But during development this is burdensome. So in that case, we might want to either
    display the error but not exit, or not even display an error.

    :param fileName: The name of the file that violated the permissions.

    :return: Nothing.
    """

    if displayPermissionViolations:
        displayError(fileName, " must be owned by root and only writable by root. Exiting.")
    if enforcePermissions:
        sys.exit(1)


# --------------------------------------------------------------------------------------------------
def complete(stub, searchPathsL):
    """
    Given a stub, collects all of the use packages that start with this text. Exports these items to
    stdOut as a newline-delimited string.

    This is the corresponding bash function needed to provide tab completion using this feature:
    _funcName () {
        local files=`./thisScript.py complete "${COMP_WORDS[$COMP_CWORD]}"`
        COMPREPLY=( ${files[@]} )
    }

    :param stub: The characters we are matching
    :param searchPathsL: The paths where use packages might live

    :return: Nothing
    """

    outputL = list()
    usePackagesL = listUsePackages(searchPathsL)
    for usePackage in usePackagesL:
        if usePackage.startswith(stub):
            output = os.path.splitext(usePackage)[0]
            outputL.append(output)
    exportShellCommand("\n".join(outputL))


# --------------------------------------------------------------------------------------------------
def listUsePackages(searchPathsL):
    """
    Returns a list of all use packages anywhere in the passed searchPathsL (list)

    :param searchPathsL: A list of paths where the use packages could live.

    :return: A list of use package names (deduplicated)
    """

    usePackagesL = list()
    for searchPath in searchPathsL:
        fileNamesL = os.listdir(searchPath)
        for fileName in fileNamesL:
            if fileName.endswith(".use"):
                usePackagesL.append(fileName)
    return list(set(usePackagesL))


# --------------------------------------------------------------------------------------------------
def getMatchingUsePkgs(usePkgName, searchPathsL):
    """
    Given a baseName, tries to find matching baseName.use files in the searchPaths Returns a list
    of full path to these files, resolving any symlinks along the way. Returns an empty list if the
    file does not exist anywhere in the searchPaths.

    :param usePkgName: The base name of the use package. I.e. "clarisse" if you were looking for
           clarisse.use
    :param searchPathsL: A list of paths where the use packages could live.

    :return: A list of full paths to (resolved) use package files that match this name. Empty if no
             matches.
    """

    usePackagesL = list()
    for searchPath in searchPathsL:
        usePkg = os.path.join(searchPath, usePkgName + ".use")
        if os.path.exists(usePkg):
            usePackagesL.append(os.path.realpath(usePkg))

    return usePackagesL


# --------------------------------------------------------------------------------------------------
def getActualUsePackage(usePkgName, usePkgSearchPathsL):
    """
    Given a specific usePkgName, returns the first one it can find among all that may match this
    name.

    :param usePkgName: The name of the use package.
    :param usePkgSearchPathsL: All the paths where this use package might live.

    :return: a use package object (configparser object)
    """

    # Find the use package file from this use package name
    # Find use package file name on disk. If more than one, let the user know but just choose one
    # and keep going
    usePackagesL = getMatchingUsePkgs(usePkgName, usePkgSearchPathsL)
    if not usePackagesL:
        displayError("Cannot find", usePkgName, "in", str(usePkgSearchPathsL))
        sys.exit(1)
    if len(usePackagesL) > 1:
        displayError("More than one use package matches this name. Using:", usePackagesL[0])
    return usePackagesL[0]


# --------------------------------------------------------------------------------------------------
def openAndVerifyUsePkgFileName(usePkgFileName):
    """
    Opens a use package file (given by usePkgFileName). Verifies the package's permissions first.

    :param usePkgFileName: The full path to the use package file.

    :return: Tuple of config objects, the first elem is a configparser object delimited by '=',
             the second is undelimited.
    """

    # Verify the security of this file
    if not validatePermissions(usePkgFileName, legalPermissionsL):
        handlePermissionViolation(usePkgFileName)

    # Read this use package file (both delimited and undelimited)
    delimitedUse = readUsePkg(usePkgFileName, "=")
    undelimitedUse = readUsePkg(usePkgFileName, "\n")

    # Return both
    return delimitedUse, undelimitedUse


# --------------------------------------------------------------------------------------------------
def use_alias(usePkgObj):
    """
    Generates the alias commands.

    :param usePkgObj: The '=' delimited use package object.

    :return: A string containing the bash shell command to set the alias'.
    """

    aliasL = reformatKeyValuePairsWithQuotes(getAliases(usePkgObj))
    aliasStr = ";".join(["alias " + item for item in aliasL])
    return aliasStr


# --------------------------------------------------------------------------------------------------
def getExistingAlias(usePkgObj):
    """
    For the alias' listed in the usePkgObj, get a list of their current values. Return this as a
    dictionary.

    :param usePkgObj: The '=' delimited use package object.

    :return: A dictionary of key/value pairs for each alias. If an alias is undefined, then the
             value will be blank.
    """

    # Create a dict to store the existing alias'
    outputD = dict()

    # Get the newly defined alias'
    aliasL = getAliases(usePkgObj)

    # For each of these alias' try to find that same value in the current shell
    for aliasT in aliasL:

        # Check to see if the alias already exists
        aliasName = aliasT[0]
        try:
            aliasValue = os.environ[aliasName]
        except KeyError:
            aliasValue = ""

        # Add that alias to the dict
        outputD[aliasName] = aliasValue

    return outputD




# --------------------------------------------------------------------------------------------------
def use_env(usePkgObj):
    """
    Generates the environmental variables.

    :param usePkgObj: The '=' delimited use package object.

    :return: A string containing the bash shell command to set the env variables.
    """

    envL = reformatKeyValuePairs(getEnv(usePkgObj))
    envStr = ";".join(["export " + item for item in envL])
    return envStr


# --------------------------------------------------------------------------------------------------
def use_path(usePkgObj):
    """
    Generates a new PATH variable with the prepend items prepended to the beginning and the postpend
    items appended to the end (removes them from the rest of PATH if they already exist).

    :param usePkgObj: The undelimited use package object.

    :return: A string containing the bash shell command to set the PATH env variable.
    """

    pathPrependsL = getPathPrepend(usePkgObj)
    pathPostpendsL = getPathPostpend(usePkgObj)
    existingPath = os.environ["PATH"]

    # Remove the prepend paths if they are already in the PATH
    for pathPrepend in pathPrependsL:
        existingPath = existingPath.replace(pathPrepend, "")

    # Remove the postpend paths if they are already in the PATH
    for pathPostpend in pathPostpendsL:
        existingPath = existingPath.replace(pathPostpend, "")

    # Add each prepend to the PATH
    for pathPrepend in pathPrependsL:
        existingPath = pathPrepend + ":" + existingPath

    # Add each postpend to the PATH
    for pathPostpend in pathPostpendsL:
        existingPath = existingPath + ":" + pathPostpend

    # Remove any doubled up : symbols
    while "::" in existingPath:
        existingPath = existingPath.replace("::", ":")

    return "PATH=" + existingPath


# --------------------------------------------------------------------------------------------------
def use_cmds(usePkgObj):
    """
    Generates the free-form bash commands.

    :param usePkgObj: The undelimited use package object.

    :return: A string containing the raw bash shell commands read from the use package file.
    """

    cmdsL = getCommands(usePkgObj)
    cmdsStr = ";".join([item for item in cmdsL])
    return cmdsStr


# --------------------------------------------------------------------------------------------------
def use(usePkgName, usePkgSearchPathsL, aliasL):
    """
    Uses a new package (given by usePkgName). Processes this file and exports the contents converted
    into bash commands.

    :param usePkgName: A name of the use package (not the file name, just the package name. Eg:
           clarisse-3.6sp2, and not clarisse-3.6sp2.use).
    :param usePkgSearchPathsL: A list of paths where the use package might live.
    :param aliasL: A python list of the existing alias' in the current shell.

    :return: Nothing
    """

    # Find the use package file from this use package name
    usePkgFileName = getActualUsePackage(usePkgName, usePkgSearchPathsL)

    # Read this use package file (both delimited and undelimited)
    delimitedUse, undelimitedUse = openAndVerifyUsePkgFileName(usePkgFileName)

    # Extract the data from the package file and reformat it into a series of bash shell commands
    bashCmd = ""
    bashCmd += use_alias(delimitedUse) + ";"
    bashCmd += use_env(delimitedUse) + ";"
    bashCmd += use_path(undelimitedUse) + ";"
    bashCmd += use_cmds(undelimitedUse)
    while ";;" in bashCmd:
        bashCmd.replace(";;", ";")

    displayError(getExistingAlias(delimitedUse))

    # Write out the history
    writeHistory(usePkgName, usePkgSearchPathsL, aliasL)

    # Export the bash command
    exportShellCommand(bashCmd)


# --------------------------------------------------------------------------------------------------
def readUsePkg(usePkgFileName, *delimiters):
    """
    Reads in the contents of a use package and returns it in the form of a configparser object
    (.ini file)

    :param usePkgFileName: The use package to read.
    :param delimiters: A list of different delimiters to use. If empty, then the default of "\n"
           will be used.

    :return: A configparser object.
    """

    if not delimiters:
        delimiters = tuple("\n")
    useConfig = configparser.ConfigParser(allow_no_value=True, delimiters=delimiters)
    useConfig.optionxform = str # Force configparser to maintain capitalization of keys
    useConfig.read(usePkgFileName)

    return useConfig


# --------------------------------------------------------------------------------------------------
def getAliases(useConfig):
    """
    Returns all of the alias commands from the useConfig

    :param useConfig: The config parser object.

    :return: Nothing
    """

    try:
        return useConfig.items("alias")
    except configparser.NoSectionError:
        return []


# --------------------------------------------------------------------------------------------------
def getEnv(useConfig):
    """
    Returns all of the env settings from the useConfig

    :param useConfig: The config parser object.

    :return: Nothing
    """

    try:
        return useConfig.items("env")
    except configparser.NoSectionError:
        return []


# --------------------------------------------------------------------------------------------------
def getPathPrepend(useConfig):
    """
    Returns the paths to prepend to $PATH from the useConfig

    :param useConfig: The config parser object. This should be one that is read without delimiters

    :return: Nothing
    """

    try:
        return reformatNoValueSecition(useConfig.items("path-prepend"))
    except (configparser.NoSectionError, configparser.NoOptionError):
        return []


# --------------------------------------------------------------------------------------------------
def getPathPostpend(useConfig):
    """
    Returns the paths to postpend to $PATH from the useConfig

    :param useConfig: The config parser object. This should be one that is read without delimiters

    :return: A list containing all of the lines in the path-postpend section.
    """

    try:
        return reformatNoValueSecition(useConfig.items("path-postpend"))
    except (configparser.NoSectionError, configparser.NoOptionError):
        return []


# --------------------------------------------------------------------------------------------------
def getCommands(useConfig):
    """
    Returns any additional shell commands to run from the useConfig

    :param useConfig: The config parser object. This should be one that is read without delimiters

    :return: A list containing all of the lines in the cmds section
    """

    try:
        return reformatNoValueSecition(useConfig.items("cmds"))
    except configparser.NoSectionError:
        return []


# --------------------------------------------------------------------------------------------------
def writeHistory(usePkgName, usePkgSearchPathsL, aliasL):
    """
    Writes the current use command to the temp history file.

    :param usePkgName: The name of the use package for which we are storing history
    :param usePkgSearchPathsL: A list of paths where the use packages may be found.
    :param aliasL: A list of all the alias' in the current shell.

    :return: Nothing
    """

    # Make sure the history file exists and that we can find it
    try:
        historyFile = os.environ["USE_HISTORY_FILE"]
    except KeyError:
        displayError("No history file. Did you forget to run setup first?")
        sys.exit(1)
    if not os.path.exists(historyFile):
        displayError("History file", historyFile, "does not exist. Did setup fail?")
        sys.exit(1)

    displayError(aliasL.split("\n"))

    # Get the actual use package file name
    usePkgFileName = getActualUsePackage(usePkgName, usePkgSearchPathsL)

    # Open it up in both delimited and undelimited formats
    delimitedUsePkgObj = readUsePkg(usePkgFileName, "=")
    unDelimitedUsePkgObj = readUsePkg(usePkgFileName, "\n")

    # Build the history dict
    outputD = dict()
    outputD["usePkgName"] = usePkgName
    outputD["alias"] = getAliases(delimitedUsePkgObj)
    outputD["env"] = getEnv(delimitedUsePkgObj)
    outputD["path-prepend"] = getPathPrepend(unDelimitedUsePkgObj)
    outputD["path-postpend"] = getPathPostpend(unDelimitedUsePkgObj)
    outputD["cmds"] = getCommands(unDelimitedUsePkgObj)

    # Open the history command for appending and write out the history string
    f = open(historyFile, "a")
    f.write(str(outputD) + "\n")
    f.close()


# --------------------------------------------------------------------------------------------------
def reformatKeyValuePairsWithQuotes(valuesL):
    """
    Given a list of tuples, returns a list of strings with key=value pairs. Returns the value in
    double quotes (as required by the bash alias command).

    :param valuesL: The list of tuples

    :return: A list of strings of key=value pairs where the value is enclosed in quotes (as required
             by the bash alias command).
    """

    outputL = list()
    for item in valuesL:
        outputL.append(item[0] + '="' + item[1] + '"')
    return outputL


# --------------------------------------------------------------------------------------------------
def reformatKeyValuePairs(valuesL):
    """
    Given a list of tuples, returns a list of strings with key=value pairs.

    :param valuesL: The list of tuples

    :return: A list of strings of key=value pairs.
    """

    outputL = list()
    for item in valuesL:
        outputL.append(item[0] + "=" + item[1])
    return outputL


# --------------------------------------------------------------------------------------------------
def reformatNoValueSecition(valuesL):
    """
    When reading a section that has a simple list (i.e. just text without delimiters or key/value
    pairs), configparser loads the data in a list of tuples. This reconstructs it into a list of
    strings to match how a normal key/value section is presented.

    :param valuesL: The list of tuples to reconstruct.

    :return: A list of strings.
    """

    outputL = list()
    for item in valuesL:
        outputL.append(item[0])
    return outputL


# --------------------------------------------------------------------------------------------------
def used():
    """
    Reads the history file and returns a list of all used packages in the current shell.

    :return: Nothing.
    """

    # Open the history file
    try:
        use_history_file = os.environ["USE_HISTORY_FILE"]
    except KeyError:
        displayError("Unable to locate a use history file")
        sys.exit(1)

    # Read in the whole file into a single list
    f = open(use_history_file, "r")
    lines = f.readlines()
    f.close()

    # Step through the list and convert it to
    used_pkg_names = list()
    for line in lines:
        used_pkg_names.append(ast.literal_eval(line)["usePkgName"])

    # Remove duplicates
    used_pkg_names = list(set(used_pkg_names))
    used_pkg_names.sort()

    # Export the shell command to display these items
    exportShellCommand('printf "' + r'\n'.join(used_pkg_names) + r'\n' + '"')


# --------------------------------------------------------------------------------------------------
def setup():
    """
    Does the setup for the current shell. Needs to be run once per shell before the system is
    usable.

    :return: An environmental variable USE_HISTORY_FILE with a path to a text file that contains the
             history of use commands for the current session.
    """

    # Check to see if there is already a use history file for this shell. Create one if needed.
    try:
        use_history_file = os.environ["USE_HISTORY_FILE"]
    except KeyError:
        f, use_history_file = tempfile.mkstemp(suffix=".usehistory", text=True)

    # Store this file name in the form of an environmental variable.
    output ="export USE_HISTORY_FILE=" + use_history_file

    # Read in the existing USE_PKG_PATH
    try:
        usePkgPath = os.environ["USE_PKG_PATH"]
    except KeyError:
        usePkgPath = ":".join(defaultUsePkgPathsL)

    # Convert it into a list
    usePkgPathsL = usePkgPath.split(":")

    legalPathFound = False
    for path in usePkgPathsL:
        if os.path.exists(path) and os.path.isdir(path):
            legalPathFound = True

    if not legalPathFound:
        displayError("No use package directory found. I looked for:", ":".join(usePkgPathsL))
        sys.exit(1)

    # Store the use package paths
    output += ";export USE_PKG_PATH=" + ":".join(usePkgPathsL)

    # Export these env variables.
    exportShellCommand(output)




# ==================================================================================================
# ==================================================================================================
if __name__ == "__main__":

    # Make sure this script is owned by root and only writable by root.
    # TODO: Wrap this to check for assertion error
    if not validatePermissions(os.path.abspath(__file__), legalPermissionsL):
        handlePermissionViolation(os.path.abspath(__file__))

    LEGAL_COMMANDS = {
        "setup": setup,
        "complete": complete,
        "use":
        "used":
        "unuse":
        "which":
        "config":
        "writehistory":
        "processStdIn":
    }

    # Only handle specific types of requests
    if sys.argv[1] not in LEGAL_COMMANDS:
        displayError("Unknown command.")
        display_usage()
    else:
        LEGAL_COMMANDS.get

    try:
        funcname = LEGAL_COMMANDS[sys.argv[1]]
    except KeyError:
        displayError()
    funcname()

    # SETUP
    # ===========================
    if sys.argv[1] == "setup":
        setup()
        sys.exit(0)

    # Read some system-wide env variables (this MUST come after we run setup)
    try:
        use_pkg_path = os.environ["USE_PKG_PATH"]
    except KeyError:
        displayError("Missing USE_PKG_PATH env variable (where use packages live). Exiting.")
        sys.exit(1)
    if ":" in use_pkg_path:
        usePackageSearchPathsL = use_pkg_path.split(":")
    else:
        usePackageSearchPathsL = [use_pkg_path]

    # ===========================
    if sys.argv[1] == "complete":
        complete(sys.argv[2], usePackageSearchPathsL)

    # ===========================
    if sys.argv[1] == "use":
        use(sys.argv[3], usePackageSearchPathsL, ast.literal_eval(sys.argv[2]))

    # ===========================
    if sys.argv[1] == "used":
        used()

    # ===========================
    if sys.argv[1] == "unuse":
        use(sys.argv[3], sys.argv[2])

    # ===========================
    if sys.argv[1] == "writehistory":
        writeHistory(sys.argv[2], usePackageSearchPathsL)

    # ===========================
    if sys.argv[1] == "processStdIn":
        exportStdIn()
