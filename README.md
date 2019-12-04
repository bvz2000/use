# use
A command line tool (and support structure) that switches between different installed versions of an app. This allows multiple versions of the same app to be installed (and used) at the same time. It is designed to work under UNIX-like systems like Linux and MacOS. It *may* work with WSL (Windows Subsystem for Linux) but is untested.

This toolset is based on a system that we use where I work.  This is my own interpretation and implementation.

# Installation
TODO

# Environment
Use understands the following environmental variables:

USE_PKG_PATHS: This is a list of directories to search for use package files.

USE_PKG_SEARCH_RECURSIVE: If this is set to true or 1, then sub-directories of the dirs listed above will also be searched. Otherwise, only those dirs listed above (and no sub-directories) will be searched. If this env variable is missing, then it will default to True.

# How the system works from an end-user perspective:
Assume you have two (or more) versions of an app (say, Blender-2.78 and Blender-2.79) on your system.

Say you want to run version 2.78. In a terminal window, you would type: "use blender-2.78". This sets up the current shell so that if you type "blender", you will launch Blender version 2.78.

If you want to run version 2.89, then you would type "user blender-2.79". From this point forward (and in this shell only) typing "blender" would launch Blender version 2.79.

In addition to the afore mentioned "use" command, here are also the following 4 additional commands:

"used" - Displays a list of the currently "used" packages in the current shell.
"unuse" - Removes a currently used package from the current shell (so that it cannot be run by typing its command
in that shell anymore).
"setup" - Initializes the whole use system. This needs to be run once per shell (usually as part of the .bashrc file).
"config" - Automates the process of creating a new use package.

All of these commands are handled by a single shell script: use.sh.  This shell script accepts the individual commands (use, unuse, used, setup, and config) as command line arguments.  The shell script also handles tab-completion (the user merely has to type the first few letters of a use package name and a list of matching packages will be displayed).

Individual application packages are managed by small text files that end in ".use".  One of these files must exist for every version of every application manged by the system. The "config" argument helps automate the creation of these files.

Note: The actual location of the applications being managed by this system is completely arbitrary. Also, this system only works under the bash shell.

# Under the hood
The actual use.sh command cannot be run. It must be sourced in order for the system to work.  This is made easier by the "setup" command which creates three alias' in the current shell. These alias' are: "use", "unuse", and "used". In addition, one other alias is created (useconfig) that runs a wizard that helps create the .use files for each application.

The short description of how the system works is that it simply sets some environmental variables and alias' in the current shell (which is why it needs to be sourced). The script reads the settings from the .use file passed to it as an argument.