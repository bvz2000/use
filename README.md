# use

Use is a command line tool that, on a basic level, simply makes modifications to your currently open shell. These changes can be the creation/modification of environmental variables, command aliases, path variables, and the running of arbitrary shell commands or even whole scripts.

In terms of functionality, this ability to make arbitrary and extensive changes to your current shell means you can do a number of useful things:

- Install multiple versions of an application, and choose which version to run at any particular time simply by typing `use app-name-version`. 
  - For example, typing `use blender-2.79` would set aliases and paths in the current shell such that executing the command `blender` would run version 2.79 of Blender. 
  - Similarly, typing `use blender-2.80` in a different shell would set aliases and paths in that shell such that executing the command `blender` in that shell would run version 2.8 of Blender.

- Allow multiple versions of an application to run at the same time.
  - As described above, each shell can run its own version of an application. This would allow more than one version to be running at the same time.
  
- Have different versions of plugins available for an application depending on the end user's needs.
  - For example, an application like Maya could use the released version of a plugin in one shell, and the development version in another shell. Simply by typing `use plugin-v1` or `use plugin-dev` (for example), you can control what plugins are active for any particular session.
  
- Have a released version of a tool active in one shell, and the development version of the same tool in another.
  - For example, if you are developing a command-line tool that is being used in your organization, you can have the majority of users using the released version by typing `use tool-v1.0`. But a few users could use the beta version simply by typing `use tool-v1.1b`. And you, as the developer, could be using your local development version by typing `use tool-dev`.
  
- Change the configuration of existing tools based on the settings of environmental variables.
  - For example, you may have a tool that connects to one web based service based on some environmental variable settings being set one way, and a different service based on these variables being set a different way.
  - By typing `use setting-website-a` in the current shell, the next time your run your tool it would then connect to web service A. 
  - By typing `use setting-website-b` in the next shell, the next time your run your tool in that shell, it would then connect to web service B. 

These are just a few simple examples. Essentially any changes that you can make manually to a shell to control the environment and change the behavior of the shell itself can be encoded in a use package and invoked with a single command.

If you are familiar with Python programming, a decent analogy would be Python Virtual Environments. The 'use' system allows for similar customizations of your entire environment but in a way that is both simple and comprehensive.

'Use' is designed to work under UNIX-like systems like Linux and MacOS. It *may* work with WSL (Windows Subsystem for Linux) but is untested. It is currently only set up to work under the BASH shell, but it would be relatively trivial to add other shells if there was some demand for this.

This toolset is based on a system that we use where I work.  This is my own interpretation and implementation.

---
# Installation
Use has no dependencies other than bash and the standard python 3 installation.

Download the .zip file and unzip it in some location that makes sense to you. For example, download and unzip into the directory:

`/opt/scripts`  <- This is just an example, you may install it anywhere you wish.

Then add this line to your .bashrc file:

`source /opt/scripts/use_bash.sh setup`

(changing the path to match where you unzipped the files).

Your shells are now ready to start using the 'use' command.

*A note for MacOS users: For some inexplicable reason MacOS does not ship with python 3 (Note: python 2 is end of life as of Jan 1st, 2020). You will have to install python 3 in order for this tool to work.*
 
*Additionally, if your default version of python remains python 2.X (which it probably should for compatability reasons), you **may** have to either use a virtual env with python 3 **OR** modify the first line of `use.py` to read: `/usr/bin/env python3`.*

*If you get an error on a line that looks like `print(message.strip(" "), file=sys.stderr)` then you most likely are running version 2.X of python and will need to make the modifications described above.*


---
# Examples of how the system works from an end-user perspective:

#### Example #1: Manage multiple versions of an application.
Assume you have two (or more) versions of an app (for example, maya-2018.3 and maya-2018.4) on your system.

Say you want to run version 2018.4. In a terminal window, you would type: "use maya-2018.4". This sets up the current shell (and current shell only) so that if you type "maya", you will launch Maya version 2018.4.

Now say something seems broken in this particular release. Downgrading to running version 2018.3 is easy. You would merely type "use maya-2018.3". From this point forward (and in this shell only) typing "maya" would launch Maya version 2018.3.

This is extendable to any number of versions. If you had 100 different versions of Maya on your system, merely by typing `use maya-<version>` would allow you to choose to run that specific version.

This also allows you to run multiple instances of the same application but with different versions simultaneously. One shell can be used to launch version 2018.3. Another shell can be used to launch version 2018.4. Both can be active at the same time (allowing you to, for example, compare the behavior between versions, or duplicate data from one to another).

#### Example #2: Manage multiple versions of plugins for an application

Let's say you had a set of plugins that Maya relied on, but which had different versions with differing pros and cons. Perhaps version 1.0 of a plugin works well with jpg images, but has trouble with png files. At the same time, let's assume that version 1.1 handles these png files without issue, but cannot load the jpg files that version 1.0 has no difficulties with. In this case, you could create a use package for each of these plugins, and invoke the one you are likely to need in the shell prior to running Maya.

For example, you could type both `use plugin-v1.0` and `use maya-2018.4` in a shell. Now when you run `maya` you will get a copy of maya version 2018.4 running and it will load plugin version 1.0.

But later you might type both `use plugin-v1.1` and `use maya-2018.4` in a shell. Now when you run `maya` you will *still* get maya version 2018.4, but the plugin it will load will be version 1.1 instead.

In this way, by ganging up multiple different use packages, you can exert fine control over the exact configuration of the toolsets you want to run at any particular time. You can have differing, specific toolchains set up for differing tasks, but where many of the same tools are used in each pipeline.

*Note, there are convenience methods that are available that remove the need to manually type a whole long list of use commands in each shell. In effect, they can gang up multiple use commands under a single "master" command. This mechanism is described in more detail below.*

#### Example #3: Manage libraries under development at the same time as released versions.

Let's now assume you are developing a set of tools or plugins for Maya yourself named "maya-plugin". Let's assume you have already released versions 1.0 and 1.1 to your team of artists.

By creating a use package for each of the released versions as well as the various development versions, your artists can choose which particular version of "maya-plugin" to have active in their current maya session.

For example, most of your art team would type `use maya-plugin-v1.1` in their shell. Then whenever they invoke the maya-plugin inside of Maya, they will be running the latest released version of the plugin. 

A small number of these artists might type `use maya-plugin-v1.0` in their shell because they are on a deadline and do not want to risk changing up to a newer version of the plugin right before they have to deliver a final product.

An even smaller number of these artists might type `use maya-plugin-v1.2.1beta` in their shells. In these few cases, they would be using (and presumably testing) the beta version of the tool prior to widespread release. 

As before, these artists can control *per-shell* which version they want to run. This means they could even have most of their shells (and production work) running using the most recent released version of the toolset, but still have one or two shells testing the beta version.

Similarly, you as the developer could type `use maya-plugin-dev` in your shell and you would be using the raw development code, bugs and all. Again, this is configurable *per shell* so that you can run the production version, the beta version, and the development version all at the same time. And switch from one to the other simply by invoking a single use command. You could even have an artist use the development version (`use maya-plugin-dev`) to see if it fixes a specific bug they may be having at that moment.

#### Example #4: Modifying Your Environment so that Tools Behave Differently

Assume you have a tool that reads environmental variables to control how it behaves. Specifically, let's assume that the env variable: DATABASE_URL contains the URL for a cloud based database, and that your tool uses this environmental variable to decide which database to connect to.

By setting up different use packages which define this environmental variable with unique URL's, you can change which database your tool connects to *per shell*.

For example, typing `use database-A` in a shell would then have your tool automatically connect to database A in that shell. Typing `use database-B` in another shell would then have your tool automatically connect to database B in this second shell.

There is no limit to the number of environmental variables you can set or modify in a single use command. The above example was incredibly simple. It could easily have included setting ten or more variables via a single use command, and that would offer very fine control over the functionality of your tool under different circumstances.

# Additional commands:
In addition to the previously mentioned "use" command, there are also the following commands:

`used` - Displays a list of the currently "used" packages in the current shell.

`unuse` - Removes a currently used package from the current shell (it essentially removes all of the modifications made to the shell by the original use command).

`set-desktop` - If run as root, this will add a .desktop file to a Linux based system that will run the app managed by the use package. ***This is still under active development and may change in the future. The command is currently not functional.***

`setup` - Initializes the whole use system. This needs to be run once per shell (This is usually done as part of the .bashrc file and as such becomes more or less invisible to the end user).

---
# Under the hood
### use_bash.sh and use.py

All of the use commands are handled by a single shell script: use_bash.sh.  This shell script accepts the individual commands (use, unuse, used, setup) as command line arguments.  The shell script also handles tab-completion (the user merely has to type the first few letters of a use package name, hit 'tab', and a list of matching packages will be displayed). The shell script is only responsible for handing the use request off to a python script (use.py) which does the actual processing. This python script then returns a bash command in the form of a string which the shell script then executes.

The actual use_bash.sh command cannot be executed in the normal way. It must actually be sourced in order for the system to work (i.e `source use_bash.sh`).  This is so that the changes being made by this script are actually propagated into the shell in which the use command is being run. This is made easier by the "setup" command which creates three alias' in the current shell that automatically source the use_bash.sh script and include the necessary command line arguments. These alias' are: "use", "unuse", and "used".

The setup command MUST be run once for each shell where you intend to invoke the use or unuse commands. Since this would be annoying to have to remember to type each time you create a new shell, it is recommended that you add the following command to your .bashrc file (this particular example assumes you unzipped the downloaded files to `/opt/scripts`, but you may actually install the use system anywhere on your system you deem fit. Adjust the following line to the path where you unzipped the downloaded files):

`source /opt/scripts/use_bash.sh setup`
 
--
### Use Packages
The use system end user data (the custom environments the end user wishes to manage) is comprised of small text files that end in ".use" (also known as 'use packages').

One of these files must exist for every version of every application or library or environment you wish to be manged by the use system. 

#
### Use Package Format
Individual .use files (use packages) are formatted as a standard, windows-style .ini file. 

The following is an example use package file. Note that normally you would not set one up with all of the contents being shown here. This example is over-provisioned simply to show what kinds of options are available. Lower down in this document I show some more common examples of use packages.

```
[branch]
blender

[env]
SOME_BLENDER_RELATED_ENV_VAR=some_value
SOME_OTHER_VAR=some_other_value

[alias]
blender=$USE_PKG_PATH/blender.sh
bl=$VERSION_PATH/wrapper/blender.sh
some_other_alias=ls -al

[desktop]
desktop=$USE_PKG_PATH/clarisse.desktop

[path-prepend-IX_SHELF_CONFIG_FILE]
/some/path/that/I/want/to/prepend/to/the/IX_SHELF_CONFIG_FILE/var
/This/is/a/second/path/to/prepend/to/this/var

[path-postpend-IX_SHELF_CONFIG_FILE]
$PRE_VERSION_PATH/$VERSION/app/shelves/shelf.cfg

[use-scripts]
/some/script/to/run/when/use/is/invoked.sh

[unuse-scripts]
/some/script/to/run/when/unuse/is/invoked.sh

[use-cmds]
use blender_tools-v1.0.1

[unuse-cmds]
unuse blender_tools-v1.0.1
```

- **branch** - (Required). 
  
  - This is a single line that names the particular use package, without a version number. Think of this as being the overall "name" of a particular use package ***family***, regardless of what specific version is being used. For example, Blender-2.70, Blender-2.80, and Blender-2.81 would all share the same branch named "blender".
  - Typically, this name is all lower case, though there is no specific requirement that it actually be lower case. The only purpose in having this convention to to cut down on issues where you can't remember whether you named a branch "Blender" or "blender".
  - Whenever a new member of a branch is used, any previous members of the branch (in this shell) are automatically unused. This means all of their settings are undone before the new settings are applied. For this reason, it is important that different families of tools have unique branch names that are fairly specific to that particular application or library. You would not, for example, want Maya and Blender to share a single branch named "3d". If you did, using `maya-2018.4` followed by using `blender-2.81` would mean that `maya-2018.4` would be unused - all of its settings would be removed from the current shell and you would no longer be able to run Maya in that shell.
- **env** - (Optional). 
  - This is a list of environmental variables to set in the form of: env = value. For example: TERM=xterm-256color
  - You may set as many env variables as desired in this section, with one assignment per line.
  - If an environmental variable does not exist in the current shell, it will be created. If it does exist, the value will be changed to the new value.
- **alias** - (Optional). 
  - This is a list of aliases to set in the form of: alias = value. For example: ll=ls -lh (Note: even though bash aliases are normally enclosed in quotes, do not include them here).
  - You may set as many aliases as desired in this section, with one assignment per line.
  - If an alias does not exist in the current shell, it will be created. If it does exist, its definition will be changed to the new value.
- **desktop** - (Optional). - UNDER DEVELOPMENT -
  - This is a path to a .desktop file for the current application (Linux only). This is used to automatically add .desktop files in Linux based systems when desktop command is issued. This command only needs to be issued once per installation of a new application, and only applies to GUI applications running under Linux.
- **path-prepend-PATH_VARIABLE** - (Optional). 
  - Path environment variables are a special case of environmental variables. You may add one section named: "path-prepend-PATH_VARIABLE" for each path variable you wish to prepend a value to. 
  - For example, if you wanted to prepend the paths `/opt/apps/scripts` and `/opt/apps/tools` to your **PYTHONPATH** variable, you would create a section called: `[path-prepend-PYTHONPATH]`. The contents of this section would have each of the previous two paths, one on each line. For example:
     ```
     [path-prepend-PYTHONPATH]
     /opt/apps/scripts/
     /opt/apps/tools/
     ```
   - If you wanted to prepend to another path (**MOZ_PLUGIN_PATH** for example) you would add another section called `[path-prepend-MOZ_PLUGIN_PATH]` and populate it with as many paths as you wanted to prepend to that variable. 
 For example, modifying both PYTHONPATH and MOZ_PLUGIN_PATH as described above, your .use file would include the following two sections:
     ```
     [path-prepend-PYTHONPATH]
     /opt/apps/scripts/
     /opt/apps/tools/

     [path-prepend-MOZ_PLUGIN_PATH]
     /opt/apps/mozilla/firefox/plugins
     ```
   - There is no limit to the number of these [path-prepend] sections you may create, nor any limit to the number of paths you may prepend in any single section.
- **path-postpend-PATH_VARIABLE**: (Optional). 
  - This works identically to the path-prepend sections, but any paths you include will be appended to the end of the path variables instead of being prepended to the beginning.
- **use-scripts**: (Optional). 
  - This is a simple list of scripts to call during the use process. 
  - These scripts may be any executable file (not simply limited to shell scripts). 
  - There is no limitation to what these scripts may do, but for security purposes they must be owned by root and only writable by root (this requirement may be modified by changing some constants in the use.py code - see below). 
  - Scripts will be sourced, not run, so they may affect the status of the current shell.
- **unuse-scripts**: (Optional). 
  - Like the use-scripts, this is a list of executables to call when running the unuse command. The same permissions requirements apply. 
- **use-cmds**: (Optional). 
  - This is a simple list of single line shell commands to execute during the use command. 
  - Be aware that in this section, no security checks are done. There is no good way to offer bullet proof security and allow the free-form running of arbitrary commands. If security is an issue, limit yourself to the use-scripts section above.
- **unuse-cmds**: (Optional). 
  - Identical to the use-cmds section, except these commands are executed during the unuse process.

#
### Built in Variables

Use packages have access to a number of built in variables.

- USE_PKG_PATH
  - This is the path to the directory that contains the use package itself.

- VERSION_PATH
  - This is the path to the directory that defines the version of the use package. This applies to auto-version use packages only.

- PRE_VERSION_PATH
  - This is the path to the directory immediately above the VERSION_PATH described above. Again, this applies auto-version use packages only.

- VERSION
  - The actual version number of the use package. As before, this applies to auto-version use packages only.

These variables may be accessed inside a .use package file by preceding them with a $. For example:

- $VERSION
- $USE_PKG_PATH
- $PRE_VERSION_PATH
- $VERSION_PATH

They may be used in any section of the .use file: [env], [alias], [path-prepend], [path-postpend], [use-scripts], [unuse-scripts], [use-cmds], [unuse-cmds], but not in [branch]. 

An example using this to set an alias for the application Blender would be:

`blender=$VERSION_PATH/app/blender`

This would be expanded to:

`blender=/opt/apps/blender/blender/2.80/app/blender`

By using these variables instead of hard-coding paths into the .use file, you make the entire use package relocatable without having to edit the .use file itself.

#
### Use Package Search Paths

The use system uses search paths to identify where to look for these use packages.  As such, these .use files must live somewhere in one of these search paths.
There are TWO types of search paths:

- auto-version search paths
- baked-version search paths

The functionality and differences between these two types of use packages is discussed below. These two search paths have default values:

- `/opt/apps` <- default path for auto-versions.
- `opt/use` <- default path for baked versions.



You may modify or add to these paths through the use of specific environmental variables (also described below).

Note: The actual applications and libraries that are managed by these use packages may live *anywhere* on the system or network. I have a preferred setup which I describe below, but the actual structure of where use packages and the files they represent is completely free-form. This means you may place the .use files anywhere on your network that you find suitable (as long as you include these locations in the search paths). Your applications, tools, libraries, and other items that are managed by these use packages may be anywhere on your network as well (and do *not* need to be added to any search paths in order for the use system to work).

#
### Versioning (auto versions and baked versions)

Each use package typically has a version attached to it (this is not strictly necessary and there may be cases in which you do not wish to include versions, but these cases are less common).

A version can be (nearly) any text and is not limited to numbers or using any particular format. For example, all of the following are valid versions:
- v1
- 1.0
- dev
- v4sp3
- dev
- BOO!

Versions are typically added to the end of the use package name after a hyphen. For example:
- blender-2.79
- maya-2018.4
- clam-dev

The only text not allowed as a version string is "latest" which is reserved for a possible future feature.

Versioning is split into two different types. These types are:

- auto-versioning
- baked-versioning

Use commands that are auto-versioned will, as the name suggests, have their version numbers automatically added to the use package name. For example, a use package file stored within the auto-version search path that is named `blender.use` could actually be presented to the user as `blender-2.80` (the '.use' extension is hidden from the user). The mechanism by which this happens is explained in greater detail below.

Use commands that have baked versions must have their versions as part of the file name. For example, a use package file stored within the baked-version search path that is named `blender.use` would be presented to the user exactly as it is named, and without any version (i.e. `blender`). If you want this use package to actually have a version, you need to make the version a part of the use package file name. In other words, if you wanted the version to be `2.80`, then the .use file would have to be named: `blender-2.80.use`.

Each type of versioning may be used on its own, or they can be used together. In other words, you may have some use packages that are auto-versioned and some that have baked versions.

Use packages that are auto-versioned **MUST** live somewhere in the auto-version search paths. In fact, that is how they are defined to be an 'auto-version' use package. 

Use packages that have baked versions **MUST** live somewhere in the baked-version search paths. Again, this is how they are defined to be a baked-version use package.

There is no difference in the internal structure of an auto-versioned use package and a baked version use package. Their distinction is purely a result of which search path they live in.

#
### Auto Versioning Details:

The easiest (and most flexible way) to handle versioning is to let the system auto-manage versions. In this case the version numbers are derived from the location of a use package (the version is extracted from the path to the use package).

These auto-versioned use packages must reside in a path that is part of the auto-version search paths.
 
To use the auto-versioning system, you would name your use package something like: `blender.use` and store it in a path that is within the auto-version search paths. Note that there is no version in the use package name. The version is then derived from directory in which the use package is stored. For example, if the use package is stored in the following directory:

  `opt/apps/blender/blender/2.80/wrapper`

then the use system will look at the path and automatically identify the version as being 2.80 by counting a specific number of paths up from where the use package was stored. 

When the end user interacts with the use system, this use package will be presented to the end user as: `blender-2.80`. The version number will have been automatically added on the fly (and the file extension ".use" is hidden).
 
The system uses an environmental variable called `USE_PKG_AUTO_VERSION_OFFSET` to determine where to look for the version number in a path. This contains a number which indicates how many directories up the path to look for the version number. By default, this is set to `2`, and represents an offset from where the use package is stored. So if the path to the use package is:

  `/opt/apps/isotropix/clarisse/4.0sp4/wrapper/clarisse.use`

  then the version (read from the path two steps up from the use package) would be `4.0sp4`, and the use package would be presented to the user as `clarisse-4.0sp4`.

#
### Baked Versioning Details:

The second way versions are handled is by simply baking the version number into the use package name itself (or foregoing versions all together).

For example, if you want to create a use package for maya 2018.3 via a baked use package, you would create a use file named `maya-2018.3.use`. Note: this file *must* reside in a path that is part of the baked-versions search paths. That is: a) how the use package will be found, and b) how it will be defined as a baked version use package. This use package will then be presented to the user as `maya-2018.3`.

If you wanted to have a use package for maya 2018.4, you would create another file named `maya-2018.4.use`. Again, this file must reside in a baked-versions search path. It would be presented to the user as `maya-2018.4`.

Along those lines, if you wanted a use package that does not use versions, you would simply create a use package named `maya.use`. It would be presented to the user as `maya`.

Essentially, baked versions are simply version numbers that are baked into the use package names.

#
### Environmental Variables
The use system understands the following environmental variables that can modify how the use system itself works. These variables are optional, but if they are used, must be set in the shell where the end user is invoking the use command:

##### USE_PKG_AUTO_VER_SEARCH_PATHS

This is a list of paths where the system will look for use packages that it will auto-version. Defaults to `/opt/apps/`. You may add as many paths in this variable as desired, all separated by a colon. Note: this path may *NOT* overlap with any of the paths in the USE_PKG_BAKED_VER_SEARCH_PATHS variable described below.

##### USE_PKG_BAKED_VER_SEARCH_PATHS

This is a list of paths where the system will look for use packages that have versions baked into their names. Defaults to `/opt/use/`. You may add as many paths in this variable as desired, all separated by a colon. Note: this path may *NOT* overlap with any of the paths in the USE_PKG_AUTO_VER_SEARCH_PATHS variable described above.

##### USE_PKG_SEARCH_RECURSIVE

A boolean determining whether to search sub-directories of the paths listed above. If False, then only the directories listed above (and none of their sub-directories) will be searched. If this environment variable is not set, defaults to `True`.

##### USE_PKG_AUTO_VERSION_OFFSET

Only applicable to auto-versioned use packages. Ignored for baked-version use packages. This variable defines where in the path to look for the version number - given as an offset from the location of the use package. For example, if the path to the use package is:

`/this/is/the/path/to/the/use/package/v001/wrapper/package.use`

then you would want to set the offset to 2, meaning it would look up the hierarchy by two levels and find `v001`. If this environment variable is not set, defaults to `2`.

##### USE_PKG_PACKAGES

This is a system variable that stores all of the use packages that were found on all of the search paths for the current shell. Do not modify this variable by hand.

##### USE_PKG_HISTORY_FILE

This is a system variable that stores the path to a temporary file that contains the history of use commands in the current shell. It is used to perform a smart 'unuse'. Do not modify this variable nor the linked file by hand.

---

# How I manage my apps (real world use cases)

The following section gives a few different scenarios on how one could format the use packages and the directories where these use packages are stored. 

### My directory structure

Let's start with how I manage my directory structure. Note: This is just an example of how you can manage your directories. You may use ***ANY*** directory structure that works for you.

I store all of my applications and some specific libraries in 

`/opt/apps/[vendor]/[appname]/[version]`

For example, Clarisse version 4.0-sp3 (A 3D content creation app from a company called Isotropix) would be stored in a directory:

`/opt/apps/isotropix/clarisse/4.0sp3/`

And Clarisse version 4.0-sp4 would be stored in:

`/opt/apps/isotropix/clarisse/4.0sp4/`

Within the directories I described above, I create two sub-directories. The first is named 'app', and the second is named 'wrapper'. 

'app' contains the application files as supplied by the vendor. I do my best never to make any modifications to these files, though sometimes it is unavoidable.

'wrapper' contains the .use package file (`clarisse.use` in this example), and any additional, custom files needed to run the app on my particular system. Since the specific flavor of Linux I am running (Manjaro at the time of this writing) is not certified for use with Clarisse, I need to install some custom libraries that I extracted from a CentOS installation. These are needed to run Clarisse on my system and, as such, will live in a lib directory inside of the wrapper directory. Launching Clarisse requires a few additional steps be taken at each run, so the actual app is wrapped in a shell script (also in the wrapper directory) called `clarisse.sh`.

To accomplish all of this, the wrapper directory contains the following (Note: this is a more complex example of a wrapper directory than is usual. Many wrapper directories consist of nothing more than the .use package file itself):

```
 \  
    \opt
       \apps
          \isotropix
             \clarisse
                \4.0sp4
                   \app
                        -- application files --
                   \wrapper
                      \lib
                         -- CentOS libraries --
                      clarisse.use
                      clarisse.sh
```

The use system itself is set up so that `/opt/apps/` is one of the auto-version search paths, and search recursively is enabled. This means that the `clarisse.use` file will be found and presented to the end user as `clarisse-4.0sp4`.

The `clarisse.use` file is as follows:

```
[branch]
clarisse

[alias]
clarisse=$USE_PKG_PATH/clarisse.sh

[path-postpend-IX_SHELF_CONFIG_FILE]
$VERSION_PATH/app/shelves/shelf.cfg
```

Notice the use of the built in variables like $VERSION_PATH and $USE_PKG_PATH that make this .use file relocatable. In other words, when A new version of Clarisse is released, I merely need to copy this .use file to the new wrapper directory and it will automatically work with the new version.

Clarisse uses an environmental variable named `IX_SHELF_CONFIG_FILE` to indicate where plugin definitions are loaded. I set this path in the .use package via the [path-postpend-IX_SHELF_CONFIG_FILE] section. Now when Clarisse is launched, it will load this particular configuration file. This will become important in the next section where I discuss loading plugins for Clarisse.

### Managing Different Plugins for Applications.

Clarisse has a python sdk and allows the user to write scripts that are accessible from a toolbar (which they refer to as a shelf).

One tool I have written is called CLAM (Which stands for **CL**arisse **A**sset **M**anagement). This is a set of python scripts that interface with another tool I have written called SQUIRREL (an asset management back end).

In order to use these tools I need to add them to my system.

First, I create a use package for SQUIRREL. Its contents are:

```
[branch]
squirrel

[path-prepend-PYTHONPATH]
$VERSION_PATH/modules

[path-prepend-PATH]
$VERSION_PATH/bin
```

The branch is defined as "squirrel".

I modify my PYTHONPATH to add the modules for the squirrel application (to allow me to import these in any other tools that want to make use of squirrel).

I modify my PATH variable to add the bin directory of the squirrel application. As a consequence, I can then call various command line applications associated with squirrel without having to supply a full path.

After squirrel, I create a another use package for CLAM. Its contents are:

```ini
[branch]
clam

[path-prepend-PYTHONPATH]
$VERSION_PATH/modules

[path-prepend-IX_SHELF_CONFIG_FILE]
$VERSION_PATH/shelves/shelf.cfg
```

The branch is defined as "clam".

I modify my PYTHONPATH to add the modules for clam (again, to allow for other tools to import these libraries.)

I also modify my IX_SHELF_CONFIG_FILE path to add a path to the specific shelf configuration file for clam. Recall that in the previous section I set a default path for this path variable. That allowed me to add the default toolbars to Clarisse. By adding to this same path in this use package, I am adding a second toolbar that contains the CLAM specific tools.

In this way I can add any set of additional tools to my copy of Clarisse, simply by 'using' those tools.

I can also change *which* specific version of the clam tools appear in clarisse simply by "using" a different version of clam.

### Other use cases.

One use I have for the use system is to change "shows" when working on visual effects. Each show has a unique setup that includes setting which versions of applications to use, which versions of plugins to use for these applications, and even paths to color lookup tables among others.

Setting all of these specific paths and variables and aliases *could* be done with a very long list of settings in a single .use file. But that would be extremely inefficient. Instead, it is possible to have one use package 'use' other use packages. In this manner, a complex set of behaviors may be created by 'ganging' up multiple, separate, smaller use packages.

For example, if a show: **MYSHOW** requires a specific version of Nuke, Maya, Blender as well as specific versions of Squirrel and Clam, I would construct individual use packages for each of these. Then my use package for the show would look something like this:

```bash
[branch]
show

[env]
OCIO_CONFIG_PATH=/show/myshow/color

[use_cmds]
use maya-2018.4
use nuke-v11
use blender-2.81
use squirrel-1.0
use clam-1.1

[unuse_cmds]
unuse maya-2018.4
unuse nuke-v11
unuse blender-2.81
unuse squirrel-1.0
unuse clam-1.1
```
The branch of this show is "show". I use the same branch name for *every* show. This is so that if I 'use' a different show, it will first unuse everything I had used for the previous show. I do not want both shows active in the same shell at the same time.

I set an env variable called OCIO_CONFIG_PATH which controls where to find the Open Color IO luts. This is custom for this specific show, and so any tool that runs in the current shell will find the color luts that are appropriate for this show. If a different show specific use package were used in this or another shell, then any tools would suddenly find that show's color luts.

I use the [use-cmds] section to load additional use packages. So by running the show's use package, I can quickly load many additional use packages. Later, when you unuse the show, all of these sub-packages will also be unused.

I can also manually unuse any of these used packages one by one if needed.

A list of all currently used packages, whether manually used in a shell, or auto-used from another use package can be displayed by typing: `use`.

### Auto-using use packages.

Manually typing in a bunch of use commands in each shell every time you create a new shell can be a bother.

Since I have a basic set of applications that I want to use all of the time (pycharm or chrome for example) I simply put the `use pycharm 2018.2.4` and `use chrome-79` commands directly in my .bashrc file. 

In this case don't even have to type the use commands by hand. They will be available in every shell automatically.

---
# A note about security:

Some very minor steps have been taken to provide a modest amount of security. The use.py application itself will refuse to run if it is not owned by root and not only writable by root (to prevent tampering with the source code). It will also only run executables (in the use-scripts and unuse-scripts sections) if they are owned by root and only writable by root. This prevents someone from surreptitiously changing the contents of a script being called by the use system and tricking the user into running malicious code. Similarly, use package files will only be processed if they have the same limitations (owned by root and only writable by root) to prevent someone from injecting another command into the use system without the end user being aware of it. 

That said, Any commands listed in the use-cmds and unuse-cmds section are not validated in the same way. Normally these sections should be used to run fairly innocent commands (like setting a python virtual environment). But note that even these seemingly innocuous commands could be hijacked and provide an avenue for malicious behavior. So calibrate your risk aversion accordingly.

These security precautions are generally used to prevent casual tampering with the use system, and are probably best to leave in place. They are NOT exhaustive security measures meant to prevent any and all exploits of the use system. But to be frank, if someone has gained access to your system and modified it such that the use system is now a vector for malware, you have much bigger issues to deal with. There is little that the use system can do that someone who already has access to your system could not do manually.

Along these lines, if these security settings are too restrictive, the source code contains several constants at the top of the code that enables and disables these security features. You may set them to True or False to control how permission validations are performed.


---
# FAQ:

- Didn't you just create a less good version of Python's virtual environments?

  - Kind of yes, and kind of no. But mostly no. Use packages can actually work with python virtual environments. You can switch virtual environments from directly within a use package.

  - Use packages are sort of like python's virtual environments (or a portion thereof), but extended outside of the Python programming environment.

- What about using docker?

  - Docker is a very powerful mechanism for virtualizing portions of your system. But it can be overkill and isn't really meant to be used for desktop applications. The Use system is fairly simple to set up and manage. It is intended to be easy and quick, without a lot of overhead. It merely manages different versions of applications and libraries on a simple desktop system.

- What are the system requirements?

  - Use was developed under python 3, and using the Bash shell. It runs on Linux and MacOS, though there is a chance it would also work on Windows using WSL. Beyond python 3 and Bash, there are no additional dependencies.
  
- What about tcsh? zsh? Any other shells?

  - The usage of the bash shell is the only one currently supported. But this connection to the calling shell is completely modular. If there were a need for additional shells, it would be relatively trivial to add that in the future.