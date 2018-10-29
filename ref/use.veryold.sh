#!/usr/bin/env bash
# TODO: There are hard-coded paths in there. They should be abstracted out.

# Make sure that the first argument is either "use" or "unuse" or "used" or "setup"
if [ "$1" != "use" -a "$1" != "unuse" -a "$1" != "used" -a "$1" != "setup" ]; then
    echo "You must specify the first argument as either 'use', 'unuse', 'used', or 'setup'"
    return 1
fi

# If this is a setup, (ha!) then just define the tab complete function and register it
if [ "$1" == "setup" ]; then

    _use () {
        local word="${COMP_WORDS[$COMP_CWORD]}"
        local files=( `compgen -f -X "!*.use" /opt/use/` )
        local output=()
        for file in "${files[@]}"; do
            fileBaseName=`basename $file .use`
            if [[ $fileBaseName =~ ^$word.* ]] || [ "$word" == "" ]; then
                output+=("$fileBaseName")
            fi
        done
        COMPREPLY=( ${output[@]} )
    }

    _unuse () {
        local word="${COMP_WORDS[$COMP_CWORD]}"
        local usedScripts=( `source /opt/scripts/use.sh used` )
        local output=()
        for item in "${usedScripts[@]}"; do
            if [[ $item =~ ^$word.* ]] || [ "$word" == "" ]; then
                output+=("$item")
            fi
        done
        COMPREPLY=( ${output[@]} )
    }

    complete -F _use use.sh
    complete -F _use use
    complete -F _unuse unuse

    alias use="source $BASH_SOURCE use"
    alias unuse="source $BASH_SOURCE unuse"
    alias used="source $BASH_SOURCE used"

    return 0
fi

# If they want a list of currently used packages, just display that.
if [ $1 == "used" ]; then    # Start by splitting the text on colons
    IFS=':' read -ra CMDS <<< "$USE_used_packages"
    for i in "${CMDS[@]}"; do
        echo "$i"
    done
    return 0
fi

# If there is no variable named "USE_PKG_PATH", create one and set it to /opt/use
if [ -z "$USE_PKG_PATH" ]; then
    export USE_PKG_PATH="/opt/use"
fi

# If the USE_PKG_PATH does not exist, bail
if [ ! -d "$USE_PKG_PATH" ]; then
    echo "Unable to locate use path: $USE_PKG_PATH"
    return 1
fi

# Step through all of the files in the USE_PKG_PATH dir
found=false
for entry in "$USE_PKG_PATH"/*.use
do
    filename=$(basename $entry)
    arg="$2.use"

    # If the current file matches the arg passed (plus ".use")...
    if [ "$filename" == $arg ]; then

        # Check to make sure the file is owned by root
        if [ `stat -c '%U' $entry` != "root" ]; then
            echo "Cannot use $entry."
            echo "Cannot utilize use files that are not owned by root for security purposes."
            return 1
        fi

        # Check to make sure the file is only writable by root. The permissions of all .use
        # files MUST be: -rw-r--r--
        if [ `stat -c '%a' $entry` != "644" ]; then
            echo "Cannot use $entry."
            echo "Cannot utilize use files that have permissions other than -rw-r--r-- for security purposes."
            return 1
        fi

        # Source the file
        source $entry $1

        # Indicate that we found a match and stop looking for any other matches
        found=true
        break
    fi
done

# If we didn't find the associated use file, bail
if [ $found == false ]; then
    echo "$2 not found in $USE_PKG_PATH"
    return 2
fi

if [ "$1" == "use" ]; then

    # Set the alias to the command based on the USE_command variable
    alias $USE_command="$USE_executablePath"

    # If there is a prepend path, add that to the beginning of the path variable
    if [ "$USE_prependPath" != "" ]; then
        [[ ":$PATH:" != *":$USE_prependPath:"* ]] && PATH="$USE_prependPath:${PATH}"
    fi

    # If there is a postpend path, add that to the end of the path variable
    if [ "$USE_postpendPath" != "" ]; then
        [[ ":$PATH:" != *":$USE_postpendPath:"* ]] && PATH="${PATH}:$USE_postpendPath"
    fi

    # If there are any arbitrary commands to run, run those
    if [ "$USE_arbitraryCode" != "" ]; then

        # Start by splitting the text on semicolons
        IFS=';' read -ra CMDS <<< "$USE_arbitraryCode"
        for i in "${CMDS[@]}"; do
            eval $i
        done
    fi

    # Remember that we are using this package
    if [ -z "$USE_used_packages" ]; then
        USE_used_packages=$2
    else
        [[ ":$USE_used_packages:" != *":$2:"* ]] && export USE_used_packages="$USE_used_packages:$2"
    fi

    # Let the user know that we set the new command
    echo "Setting '$USE_command' to point to '$USE_executablePath'"

    # Clean up by removing the above env variables
    unset USE_command
    unset USE_prependPath
    unset USE_postpendPath
    unset USE_arbitraryCode

fi

if [ "$1" == "unuse" ]; then
    unalias $USE_command

    # Now remove the package name from the list of used packages

    # Start by splitting the text on semicolons
    IFS=':' read -ra CMDS <<< "$USE_used_packages"
    unset USE_used_packages
    for i in "${CMDS[@]}"; do
        if [ "$i" != "$2" ]; then
            if [ -z "$USE_used_packages" ]; then
                USE_used_packages="$i"
            else
                USE_used_packages="$USE_used_packages:$i"
            fi
        fi
    done

    # Clean up by removing the above env variables
    unset USE_command
    unset USE_prependPath
    unset USE_postpendPath
    unset USE_arbitraryCode

fi