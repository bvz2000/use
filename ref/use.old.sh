#!/bin/bash

# Make sure that the first argument is either "use" or "unuse" or "used" or 
# "setup" or "config"
if [ "$1" != "use" -a "$1" != "unuse" -a "$1" != "used" -a "$1" != "setup" -a "$1" != "config" ]; then
    echo "Error: You must specify the first argument as either:
         'use' 
         'unuse' 
         'used'
         'setup'
         'config'"
    return 1
fi

# NOTE: This script is intended to be SOURCED if called with "use", "unuse", 
# "used" or "setup". In these cases do not run it. If called with "config" it
# must be run and not sourced.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [ "$1" == "use" ] || [ "$1" == "unuse" ] || [ "$1" == "used" ] || [ "$1" == "setup" ]; then
        echo "This script must be sourced, not run"
        exit 1
    fi
else
    if [ "$1" == "config" ]; then
        echo "This script must be run, not sourced"
        return 1    
    fi
fi

# Path where the use packages live (in case it isn't defined in a shell env)
# (Always make sure the path ends with a slash)
USEPKGPATH="/opt/use/"
[[ $USEPKGPATH != */ ]] && USEPKGPATH="$USEPKGPATH"/

# If there is no variable named "USE_PKG_PATH", create it and set to $USEPKGPATH
if [ -z "$USE_PKG_PATH" ]; then
    export USE_PKG_PATH=$USEPKGPATH
else # It exists, but make sure it ends with a slash
    [[ $USE_PKG_PATH != */ ]] && USE_PKG_PATH="$USE_PKG_PATH"/
fi

# If the USE_PKG_PATH path does not exist, bail
if [ ! -d "$USE_PKG_PATH" ]; then
    echo "Unable to locate use path: $USE_PKG_PATH"
    return 1
fi



# ==============================================================================
# setup
# ==============================================================================

# If this is a setup, (ha!) then just define the tab complete function and 
# register it - this sets up the tab-completion.
if [ "$1" == "setup" ]; then

    # Function to set up tab completion for the use command
    _use () {
        local word="${COMP_WORDS[$COMP_CWORD]}"
        local files=( `compgen -f -X "!*.use" $USE_PKG_PATH` )
        local output=()
        for file in "${files[@]}"; do
            fileBaseName=`basename $file .use`
            if [[ $fileBaseName =~ ^$word.* ]] || [ "$word" == "" ]; then
                output+=("$fileBaseName")
            fi
        done
        COMPREPLY=( ${output[@]} )
    }

    # Function to set up tab completion for the unuse command
    _unuse () {
        local word="${COMP_WORDS[$COMP_CWORD]}"
        local usedScripts=( `source $BASH_SOURCE used` )
        local output=()
        for item in "${usedScripts[@]}"; do
            if [[ $item =~ ^$word.* ]] || [ "$word" == "" ]; then
                output+=("$item")
            fi
        done
        COMPREPLY=( ${output[@]} )
    }

    # Call functions to set up tab-completions
    # complete -F _use use.sh
    complete -F _use use
    complete -F _unuse unuse

    # Create alias' for each of the possible commands
    alias use="source $BASH_SOURCE use"
    alias unuse="source $BASH_SOURCE unuse"
    alias used="source $BASH_SOURCE used"
    alias useconfig="$BASH_SOURCE config"

    return 0
    
fi



# ==============================================================================
# config
# ==============================================================================

# If this is a config (i.e. the user is using the tool to create a new use
# package) then run a "wizard" to gather info and then create the associated
# files.
if [ "$1" == "config" ]; then

    # This needs to run as root
    if [[ $EUID -ne 0 ]]; then
       echo "This script must be run as root" 
       exit 1
    fi   
     
    # Gather the info we need to create the directories
    read -p "Enter app developer (i.e. 'microsoft'): " developer
    read -p "Enter app name (i.e. 'office'): " appname
    read -p "Enter app version (i.e. '2018.2.10'): " version
    read -p "Enter path where these apps will be installed (i.e. '/opt/apps'): " installPath
    read -p "Enter the name of the executable path relative to the top level path of the app (i.e. 'bin/office.sh'): " execPath
    read -p "Enter the category for this app (i.e. 'office'): " category
    read -p "Enter a path to an icon for this app (i.e. '~/Downloads/office.svg'): " iconPath
    
    # Create the paths to the app, use package, and desktop file
    appPath="$installPath/$developer/$appname/$version/"
    usePkg="$USE_PKG_PATH$appname-$version.use"
    desktopFile="$appPath$appname-$version.desktop"
    
    # If the app path does not exist, create it (with the user's permission)
    if [ ! -d $appPath ]; then
        echo
        echo
        echo "I am about to create the following directory:"
        echo $appPath
        echo
        echo "Do you wish to continue?"
        read -p "Continue? (Y/N): " confirm && [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]] || exit 0
        mkdir $appPath
        echo
        echo "$appPath created"
    else
        echo
        echo
        echo "The directory $appPath already exists, no need to create it."
    fi

    # Copy the icon to the app path (if it does not already exist)
    filename=$(basename -- "$iconPath")
    extension="${filename##*.}"
    if [ -f $iconPath ]; then
        if [ ! -f $appPath$appname.$extension ]; then
            cp "$iconPath" $appPath$appname.$extension
        fi
    fi
        
    # Create the .desktop file (if it does not already exist)
    if [ ! -f $desktopFile ]; then
        echo
        echo
        echo "I am about to create the following .desktop file:"
        echo $desktopFile
        echo
        echo "Do you wish to continue?"
        read -p "Continue? (Y/N): " confirm && [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]] || exit 0
        echo "[Desktop Entry]" > $desktopFile
        echo "Version=$version" >> $desktopFile
        echo "Terminal=false" >> $desktopFile
        echo "Icon=$appPath$appname.$extension" >> $desktopFile
        echo "Type=Application" >> $desktopFile
        echo "Categories=$category;" >> $desktopFile
        echo "Exec=$appPath$execPath" >> $desktopFile
        echo "Name=$appname-$version" >> $desktopFile
        echo
        echo "$desktopFile created"
    else
        echo
        echo
        echo "The .desktop file $desktopFile already exists, no need to create it."
    fi
    
    # Make a symbolic link to the .desktop in /usr/share/applications
    if [ ! -f "/usr/share/applications/$appname-$version.desktop" ]; then
        if [ -f $desktopFile -a -d "/usr/share/applications/" ]; then
            ln -s $desktopFile "/usr/share/applications/$appname-$version.desktop"
            echo "symlink created in /usr/share/applications/$appname-$version.desktop"
        fi
    fi
     
    # If the use package does not exist, create it (with the user's permission)   
    if [ ! -f $usePkg ]; then
        echo
        echo
        echo "I am about to create the following use package file:"
        echo $usePkg
        echo
        echo "Do you wish to continue?"
        read -p "Continue? (Y/N): " confirm && [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]] || exit 0
        echo "# Set the name of the command we want to run" > $usePkg
        echo "command=$appname" >> $usePkg
        echo >> $usePkg
        echo "# Set the path to the executable that will be run when the above command is called" >> $usePkg
        echo "executablePath=$appPath$execPath" >> $usePkg
        echo >> $usePkg
        echo "# Set a path (optional) that we want to prepend to the PATH variable" >> $usePkg
        echo "prependPath=" >> $usePkg
        echo >> $usePkg
        echo "# Set a path (optional) that we want to postpend to the PATH variable" >> $usePkg
        echo "postpendPath=" >> $usePkg
        echo >> $usePkg
        echo "# Set any number of (optional) arbitrary shell commands to execute, separated by semicolons" >> $usePkg
        echo "arbitraryCode=" >> $usePkg
        echo
        echo "$usePkg created."
    else
        echo
        echo
        echo "The use package $usePkg already exists, no need to create it."
    fi
        
    echo
    echo
    echo "Config complete."
    
    exit 0
fi



# ==============================================================================
# used
# ==============================================================================

# If they want a list of currently used packages, just display that.
if [ $1 == "used" ]; then    # Start by splitting the text on colons
    IFS=':' read -ra CMDS <<< "$USE_used_packages"
    for i in "${CMDS[@]}"; do
        echo "$i"
    done
    return 0
fi



# ==============================================================================
# use and unuse
# ==============================================================================

# Step through all of the files in the USE_PKG_PATH dir
found=false
for entry in "$USE_PKG_PATH"/*.use; do

    filename=$(basename $entry)
    arg="$2.use"

    # If the current file matches the arg passed (plus ".use")...
    if [ "$filename" == $arg ]; then

        # Since we offer the option of running arbitrary code, for security
        # reasons we need to make sure the .use file is owned by root and can
        # only be written to by root.
        
        # Check to make sure the file is owned by root
        if [ `stat -c '%U' $entry` != "root" ]; then
            echo "Cannot use $entry."
            echo "Cannot utilize use files that are not owned by root for security purposes."
            return 1
        fi

        # Check to make sure the file is only writable by root. The permissions 
        # of all .use files MUST be: -rw-r--r--
        if [ `stat -c '%a' $entry` != "644" ]; then
            echo "Cannot use $entry."
            echo "Cannot utilize use files that have permissions other than -rw-r--r-- for security purposes."
            return 1
        fi

        # Extract the data from this .use file that we need
        aliasCommand=`grep ^command $entry | cut -d "=" -f 2- | awk '{$1=$1};1'`
        executablePath=`grep ^executablePath $entry | cut -d "=" -f 2- | awk '{$1=$1};1'`
        prependPath=`grep ^prependPath $entry | cut -d "=" -f 2- | awk '{$1=$1};1'`
        postpendPath=`grep ^postpendPath $entry | cut -d "=" -f 2- | awk '{$1=$1};1'`
        arbitraryCode=`grep ^postpendPath $entry | cut -d "=" -f 2- | awk '{$1=$1};1'`

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



# ==============================================================================
# use
# ==============================================================================

if [ "$1" == "use" ]; then

    # Set the alias to the command based on the USE_command variable
    alias $aliasCommand="$executablePath"

    # If there is a prepend path, add that to the beginning of the PATH variable
    if [ -d "$prependPath" ]; then
        if [ "$prependPath" != "" ]; then
            if [ -z "$PATH" ]; then
                export PATH=$prependPath
            else:
                [[ ":$PATH:" != *":$prependPath:"* ]] && PATH="$prependPath:${PATH}"
            fi
        fi
    elif [ "$prependPath" != "" ]; then
        echo "USE WARNING ($aliasCommand): prependPath $prependPath does not exist."
    fi

    # If there is a postpend path, add that to the end of the PATH variable
    if [ -d "$postpendPath" ]; then
        if [ "$postpendPath" != "" ]; then
            if [ -z "$PATH" ]; then
                export PATH=$postpendPath
            else:
                [[ ":$PATH:" != *":$postpendPath:"* ]] && PATH="${PATH}:$postpendPath"
            fi
        fi
    elif [ "$postpendPath" != "" ]; then
        echo "USE WARNING ($aliasCommand):: postpendPath $postpendPath does not exist."
    fi

    # If there are any arbitrary commands to run, run those
    if [ "$arbitraryCode" != "" ]; then

        # Start by splitting the text on semicolons
        IFS=';' read -ra CMDS <<< "$arbitraryCode"
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
    
    # If this application doesn't have a .desktop file in 
    # /usr/share/applications, then link the .desktop file from the app (if it
    # exists) and put it there. The script will look for this .desktop file
    # parallel to the executable, and then up one directory, and then up one
    # more directory as so on till it finds the .desktop file or winds up at
    # root. Because this requires root permissions, just show the user the
    # command they would have to run to make it work.
    if [ ! -f "/usr/share/applications/$2.desktop" ]; then
        testPath=$executablePath
        while [ "$testPath" != "" ]; do
            testPath=$( echo ${testPath%/*} )
            if [ -f "$testPath/$2.desktop" ]; then
                echo "If you want to create a dekstop file for this app,"
                echo "type the following command (assuming you have sudo"
                echo "priviledges):"
                echo
                echo "sudo ln -s $testPath/$2.desktop /usr/share/applications/$2.desktop"
                break
            fi
        done
    fi
    
    # Let the user know that we set the new command
    echo "Setting '$aliasCommand' to point to '$executablePath'"

fi



# ==============================================================================
# unuse
# ==============================================================================

if [ "$1" == "unuse" ]; then
    unalias $aliasCommand

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

fi




# Clean up by removing the above env variables
unset aliasCommand
unset executablePath
unset prependPath
unset postpendPath
unset arbitraryCode

