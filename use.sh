#!/bin/bash

# This script must be SOURCED.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "This script must be sourced, not run"
    exit 1
fi

# Get the path to this shell script
me=`realpath $BASH_SOURCE`

# Get the path to the python script
python_script="`dirname $me`/use.py"




# ==============================================================================
# setup
# ==============================================================================

# If this is a setup, (ha! joke!) then get a path to the history file and also
# define the tab complete function.
if [ "$1" == "setup" ]; then

    # Run the python setup
    eval `$python_script setup`

    # Function to set up tab completion for the use command
    _use () {
        local files=`$python_script complete "${COMP_WORDS[$COMP_CWORD]}"`
        COMPREPLY=( ${files[@]} )
    }

#    # Function to set up tab completion for the unuse command
#    _unuse () {
#        local word="${COMP_WORDS[$COMP_CWORD]}"
#        local usedScripts=( `source $BASH_SOURCE used` )
#        local output=()
#        for item in "${usedScripts[@]}"; do
#            if [[ $item =~ ^$word.* ]] || [ "$word" == "" ]; then
#                output+=("$item")
#            fi
#        done
#        COMPREPLY=( ${output[@]} )
#    }

    # Call functions to set up tab-completions for use and unuse
    # complete -F _use use.sh
    complete -F _use use
    complete -F _unuse unuse

    # Create alias' for each of the possible commands
    alias use="source $me use"
    alias unuse="source $me unuse"
    alias used="source $me used"
    alias useconfig="$me config"

    return 0

fi

# ==============================================================================
# use
# ==============================================================================

if [ "$1" == "use" ]; then

    # Call the python script for all of the data we need
    #aliasList=`alias | $python_script processStdIn`
    eval `alias | $python_script use $2`

fi


# ==============================================================================
# used
# ==============================================================================

if [ "$1" == "used" ]; then

    # Call the python script to get a list of used packages
    eval `$python_script used`

fi