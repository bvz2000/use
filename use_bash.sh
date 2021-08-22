#!/bin/bash

# MacOS does not have the realpath command installed by default. This is a
# small workaround as posted by Geoff Nixon at
# https://stackoverflow.com/questions/3572030/bash-script-absolute-path-with-os-x

userealpath() {
  OURPWD=$PWD
  cd "$(dirname "$1")"
  LINK=$(readlink "$(basename "$1")")
  while [ "$LINK" ]; do
    cd "$(dirname "$LINK")"
    LINK=$(readlink "$(basename "$1")")
  done
  REALPATH="$PWD/$(basename "$1")"
  cd "$OURPWD"
  echo "$REALPATH"
}

# This script must be SOURCED (only for some functions)
if [ "$1" != "desktop" ]; then

    if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
        echo "This script must be sourced, not run"
        exit 1
    fi
fi

# Get the path to this shell script
me=`userealpath $BASH_SOURCE`

# Get the path to the python script
python_script="`dirname $me`/usemain.py"


# If this is a refresh command (-refresh or --refresh is in the args) do that and quit.
#if [ "$2" == "-refresh" ]; then
#    echo "Well fuck"
#    echo `$python_script bash refresh`
#    exit 0
#fi





# ==============================================================================
# setup
# ==============================================================================

# If this is a setup, (ha! joke!) then get a path to the history file and also
# define the tab complete_use function.
if [ "$1" == "setup" ]; then

    # Run the python setup
    eval `$python_script bash setup`

    # Function to set up tab completion for the use command
    _use () {
        local files=`$python_script bash complete_use "${COMP_WORDS[$COMP_CWORD]}"`
        COMPREPLY=( ${files[@]} )
    }

    # Function to set up tab completion for the use command
    _unuse () {
        local pkgs=`$python_script bash complete_unuse "${COMP_WORDS[$COMP_CWORD]}"`
        COMPREPLY=( ${pkgs[@]} )
    }

    # Call functions to set up tab-completions for use and unuse
    # complete_use -F _use use.sh
    complete -F _use use
    complete -F _unuse unuse

    # Create alias' for each of the possible commands
    alias use="source $me use"
    alias unuse="source $me unuse"
    alias used="source $me used"
    alias useRefresh="source $me refresh"
    # alias useconfig="$me config"
    # alias useSymlinkLatest="source $me update"
    # alias useUpdateDesktops="$me desktop"

    return 0

fi


# ==============================================================================
# refresh
# ==============================================================================

# If this is a refres, then just build a new list of all of the use packages.
if [ "$1" == "refresh" ]; then

    # Run the python setup
    eval `$python_script bash refresh`

fi

# ==============================================================================
# use
# ==============================================================================

if [ "$1" == "use" ]; then

    # Note: we pipe the alias command into the script because that is how we inform
    # the script of the current alias values.

    # We have to start by un-using the branch
    #unuse_pkg=`$python_script bash get_branch_from_use_pkg_name $2`
    #eval `alias | $python_script bash unuse $unuse_pkg`
    eval `alias | $python_script bash unuse $2`

    # Then use the new use package
    eval `alias | $python_script bash use $2`

fi


# ==============================================================================
# used
# ==============================================================================

if [ "$1" == "used" ]; then

    eval `$python_script bash used`

fi


# ==============================================================================
# unuse
# ==============================================================================

if [ "$1" == "unuse" ]; then

    eval `alias | $python_script bash unuse $2`

fi


# ==============================================================================
# update-latest
# ==============================================================================

if [ "$1" == "symlink" ]; then

    if [[ $EUID -ne 0 ]]; then
       echo "This script must be run as root. Note: Running with sudo will"
       echo "NOT work! You have to become root using 'su' and then re-run this"
       echo "command."
    else
        eval `alias | $python_script bash symlink_latest`
    fi

fi


# ==============================================================================
# update-desktop
# ==============================================================================

if [ "$1" == "desktop" ]; then

    if [[ $EUID -ne 0 ]]; then
       echo "This script must be run as root."
    else
        $python_script bash update_desktop $2
    fi

fi
