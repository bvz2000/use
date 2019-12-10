# use

Use is a command line tool that, on a basic level, simply makes modifications to your currently open shell. These changes can be the creation/modification of environmental variables, command aliases, path variables, and the running of arbitrary shell commands or even whole scripts.

On a slightly higher level, this ability to make arbitrary and extensive changes to your current shell means you can do a number of useful things:

- Install multiple versions of an application, and choose which version to run at any particular time simply by typing `use app-name-version-#`. 
  - For example, typing `use blender-2.79` would 'activate' that version of Blender in that shell. In other words, executing the command `blender` in that shell would run version 2.79. 
  - Typing `use blender-2.80` in a different shell would 'activate' the 2.80 version in that shell. Executing `blender` in that shell would run version 2.8.

- Allow multiple versions of an application to run at the same time.
  - As described above, each shell can run its own version of an application. This would allow more than one version to be running at the same time.
  
- Have different versions of plugins available for an application depending on the end user's needs.
  - For example, an application like Maya could use version 1 of a plugin in one shell, and version 2 in another shell. Simply by typing `use plugin-v1` or `use plugin-v2`, you can control what plugins are active for any particular session.
  
- Have a released version of a tool active in one shell, and the development version of the same tool in another.
  - For example, if you are developing a command-line tool that is being used in your organization, you can have the majority of users using the released version by typing `use tool-v1.0`. But a few users could use the beta version simply by typing `use tool-v1.1b`. And you, as the developer, could be using your local development version by typing `use tool-dev`.
  
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

`source /opt/scripts/use.sh setup`

(changing the path to match where you unzipped the files).

Your shells are now ready to start using the 'use' command. 


---
# Examples of how the system works from an end-user perspective:

#### Manage multiple versions of an application.
Assume you have two (or more) versions of an app (say, maya-2018.3 and maya-2018.4) on your system.

Say you want to run version 2018.4. In a terminal window, you would type: "use maya-2018.4". This sets up the current shell (and current shell only) so that if you type "maya", you will launch Maya version 2018.4.

Now say something seems broken in the latest release (2018.4). If you want to downgrade to running version 2018.3, you would type "use maya-2018.3". From this point forward (and in this shell only) typing "maya" would launch Maya version 2018.3.

This is extendable to any number of versions. If you had 100 different versions of Maya on your system, merely by typing `use maya-<version>` would allow you to choose to run that specific version.

This also allows you to run several instances of different versions of the same application simultaneously. One shell can be used to launch version 2018.3. Another shell can be used to launch version 2018.4. Both can be active at the same time (allowing you to, for example, compare the behavior between versions, or duplicate data from one to another).

#### Manage multiple versions of plugins for an application

Let's say you had a set of plugins that Maya relied on, but which had different versions for different tasks. Perhaps one version works well with jpg images, but has bugs with png files. Maybe the other version does will with png files, but cannot manage jpg files. In this case, you could create a use package for each of these plugins, and invoke the one you are likely to need in the shell prior to running Maya.

For example, you could type `use plugin-v1.0` and then `use maya-2018.4` in a shell. Now when you run `maya` you will get a copy of maya version 2018.4 running and it will load plugin version 1.0.

But later you might type `use plugin-v2.0` and then `use maya-2018.4` in a shell. Now when you run `maya` you will *still* get version 2018.4, but the plugin it will load will be version 2.0 instead.

In this way, by ganging up multiple different use packages, you can exert fine control over the exact configuration of the toolsets you want to run at any particular time. 

*Note, there are convenience methods that are available that remove the need to manually type a whole long list of use commands in each shell. In effect, they can gang up multiple use commands under a single "master" command. This mechanism is described in more detail below.*

#### Manage libraries under development at the same time as released versions.

Let's now assume you are developing a set of tools or plugins for Maya yourself. But let's assume you have already released previous versions to your team of artists.

By creating a use package for the released version as well as the various development versions, your artists can choose which particular set of tools or plugins to activate in any particular shell.

For example, most of your art team would type `use my-tools-v1.0.0` in their shell. Then whenever they invoke this tool, they are running the released code. But a small number of these artists might type `use my-tools-v1.0.1beta` in their shells. In these few cases, they would be using (and presumably testing) the beta version of the tool. As before, they can control *per-shell* which version they want to run, meaning they could even have most of their shells (and production work) running using the released version of the toolset, but still have one or two shells testing the beta version.

Similarly, you could type `use my-tools-dev` in your shell and you would be using the raw development code, bugs and all. Again, this is configurable *per shell* so that you can run the production version, the beta version, and the development version all at the same time. And switch from one to the other simply by invoking a single use command.

#### Additional commands:
In addition to the previously mentioned "use" command, there are also the following 3 additional commands:

`used` - Displays a list of the currently "used" packages in the current shell.

`unuse` - Removes a currently used package from the current shell (it essentially removes all of the modifications made to the shell by the original use command).

`set-desktop` - If run as root, this will add a .desktop file to a Linux based system that will run the app managed by the use package. ***This is still under active development and may change in the future. The command is currently not functional.***

`setup` - Initializes the whole use system. This needs to be run once per shell (This is usually done as part of the .bashrc file and as such becomes more or less invisible to the end user).

---
# Under the hood
####use.sh and use.py
All of the use commands are handled by a single shell script: use.sh.  This shell script accepts the individual commands (use, unuse, used, setup) as command line arguments.  The shell script also handles tab-completion (the user merely has to type the first few letters of a use package name and a list of matching packages will be displayed). The shell script is only responsible for handing the use request off to a python script (use.py) which does the actual processing. This python script then returns a bash command in the form of a string which the shell script then executes.

The actual use.sh command cannot be run. It must be sourced in order for the system to work.  This is made easier by the "setup" command which creates three alias' in the current shell. These alias' are: "use", "unuse", and "used".

The setup command MUST be run once for each shell where you intend to use the use or unuse commands. Since this would be annoying to have to remember to type each time you create a new shell, it is recommended that you add the following command to your .bashrc file (the following example assumes you unzipped the downloaded files to `/opt/scripts`, but you may actually install the use system anywhere on your system you deem fit. Adjust the following line to the path where you unzipped the downloaded files):

`source /opt/scripts/use.sh setup`
 
--
####Use Packages
Individual application packages are managed by small text files that end in ".use" (also known as 'use packages').

One of these files must exist for every version of every application or library manged by the use system. These files must live somewhere in one of the search paths used to define use package locations.

#####Search Paths
There are two default search paths: `/opt/apps` and `opt/use`.

You may modify or add to these paths through the use of specific environmental variables (described below).

The applications that are managed by these use packages may live anywhere on the system or network. I have a preferred setup which I describe below, but the actual structure of where use packages and the files they represent is completely free-form. This means you may place the .use files anywhere on your network that you find suitable (as long as you include these locations in the search paths). Your applications, tools, libraries, and other items that are managed by these use packages may be anywhere on your network as well (and do not need to be added to any search paths).

#####Use Package Format
A .use file (use package) is formatted as a standard, windows-style .ini file. 

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
  
  - This is a single line that names the particular use package, without a version number. Think of this as being the overall "name" of a particular use package family regardless of what specific version is being used. For example, Blender-2.70, Blender-2.80, and Blender-2.81 would all share the same branch named "blender".
  - Typically, this name is all lower case.
  - Whenever a new member of this branch is used, any previous members of this branch (in this shell) are automatically unused first (all their settings undone before the new settings are applied). For this reason, it is important that different families of tools have unique branch names. You would not, for example, want Maya and Blender to share a single branch named "3d". If you did, using `maya-2018.4` followed by using `blender-2.81` would mean that `maya-2018.4` would be unused (all of its settings removed from the current shell).
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
  - If you include an executable in this section, no security checks are done, so it is best to limit the use of this section to simple commands (such as setting Python virtual environments for example), and leaving the calling of custom executables to the use-scripts section.
- **unuse-cmds**: (Option). 
  - Identical to the use-cmds section, except these commands are executed during the unuse process.

#####Versioning

Each use package generally needs to have a version attached to it (this is not strictly necessary and there may be cases in which you do not wish to include versions, but these cases are less common).

A version can be (nearly) any text (not limited to numbers or any particular format). For example, all of the following are valid versions:
- v1
- 1.0
- dev
- v4sp3
- dev
- BOO!

The only version not allowed is the text: "latest" which is reserved for a possible future feature.

Versions are typically added to the end of the use package name after a hyphen. For example:
- blender-2.79
- maya-2018.4
- clam-dev

The use system handles the versioning of use packages in two separate ways:
 
- auto versioning
- baked versions

**Auto Versioning**

- The easiest (and most flexible way) to handle versioning is to let the system auto-manage versions. In this case the version numbers are derived from the location of a use package (the version is extracted from the path to the use package).
 
- To use this system, you would name your use package something like: `blender.use`. Note that there is no version in the use package name. This use package would then be placed in a directory that has the version number somewhere in the path. For example:

  `opt/apps/blender/blender/2.80/wrapper`

- The use system will look at the path and automatically identify the version as being 2.80 based on a setting described below. When the end user interacts with the use system, this use package will be presented to the end user as: `blender-2.80`. The version number will have been automatically added on the fly.
 
- The system uses an environmental variable called `USE_PKG_AUTO_VERSION_OFFSET` to determine where to look for the version number in a path. This contains a number which indicates how many directories up the path to look for the version number. By default, this is set to `2`, and represents an offset from where the use package is stored. So if the path to the use package is:

  `/opt/apps/isotropix/clarisse/4.0sp4/wrapper/clarisse.use`

  then two steps up would be `4.0sp4`.

**Baked Versions**

- Baked versions are simply version numbers that are baked into the use package names.


#How I manage my apps

The following section gives a few different scenarios on how one could format the use packages and the directories where these use packages are stored. 

#A note about security:

Some minor steps have been taken to provide a modest amount of security. The use.py application itself will refuse to run if it is not owned by root and not only writable by root (to prevent tampering with the source code). It will also only run executables (in the use-scripts and unuse-scripts sections) if they are owned by root and only writable by root. This prevents someone from surreptitiously changing the contents of a script being called by the use system and tricking the user into running malicious code. Similarly, use package files will only be processed if they have the same limitations (owned by root and only writable by root) to prevent someone from injecting another command into the use system without the end user being aware of it. 

That said, Any commands listed in the use-cmds and unuse-cmds section are not validated in the same way. Normally these sections should be used to run fairly innocent commands (like setting a python virtual environment). But note that even these seemingly innocuous commands could be hijacked and provide an avenue for malicious behavior. So calibrate your risk aversion accordingly. On the other hand, this feature can also be used by the sys-admin in the case that these permissions are too restrictive and you choose to run tools with looser permissions. 

If these settings are too restrictive, the source code contains several constants at the top of the code that enables and disables these security features. You may set them to True or False to control how permission validations are performed.

---
# Specific Use Cases

What follows are two specific use cases for the use system. There are a myriad of other ways it can be used, but these two represent a cross section of what I think are the most likely common scenarios.

###Case #1: Easily Running Multiple Versions of the Same Application:
Let's assume you want to have more than one version of Blender running on your system, and you want to be able to quickly switch from one to the other.

Start by installing Blender to a location of your choosing. For my purposes I will always install all of my applications to /opt/. I use the following structure:

/opt/apps/[vendor]/[appname]/[version]/

Then within this directory I have two directories:

- app
- wrapper

I store the actual application in the 'app' directory. I store any custom wrappers, custom libraries that may be referenced by LD_LIBRARY_PATH, and the .use file in the 'wrapper' directory.

So in the case of Blender I would have the following structure:

`/opt/apps/blender/blender/2.79/app` <- this holds the actual application files and directories

`/opt/apps/blender/blender/2.79/wrapper` <- this is where the blender.use file is stored.

The `blender.use` file is extremely simple and looks like this:

```
[branch]
blender

[alias]
blender=/opt/apps/blender/blender/$VERSION/app/blender
```

Since `/opt/apps/` is in the use package search path (and recursive is True) that means this blender.use file will be found by the system. And since auto-versioning is enabled (and the offset is set to `2`) that means it will look up two levels in the directory to find its version number.

So when you type `use bl` and hit `tab`, the system will auto-complete `blender-2.79` for you. Note that it has automatically added the version number (and dropped the .use).

But who wants to only use Blender 2.79 now that 2.80 is out?

So create some new directories:

`/opt/apps/blender/blender/2.80/app`

`/opt/apps/blender/blender/2.80/wrapper`

In the app directory, install the 2.8 version of Blender. 

In the wrapper directory just copy the .use file from 2.79. Note that since it uses the variable `$VERSION` you don't need to make any changes. It will simply work exactly as it did before. Note: There are additional built in variables (described below) which can actually simplify the structure of the use file even further.

Now when you type `use bl` and hit tab, you will be presented with two options: `blender-2.79` and `blender-2.80`. Note, again, that the version numbers have been automatically added to the use packages. You did not have to customize the .use file to include them manually. Once you finish typing `blender-2.80` you may now simply type: `blender` in this shell and blender 2.8 will start up.

Now you could continue this same pattern for every beta version of Blender too. In a shell you can easily choose which one you want to 'use' simply by typing `use blender-<version>`. Feel free to have 100 different versions on your system without any concern that they will interfere with each other.

Note: the directory structure I indicated above is just how I set up my own system. The use system is quite freeform with regard to where .use files are stored and where the applications they relate to are stored. They do not have to be in the same hierarchy at all. That is just how I like to mange my system.
###Case #2: Using different libraries on the same system:
Say you want to have different versions of a python package for different purposes. For example, perhaps you are developing a tool and you want users on your network to be able to use the latest released library, but you yourself want to use the development version. This is also easy to accomplish using the use packages.

Create two .use packages (if you are using the auto-versioning system they will have to be in separate directories).

Say you created a tool called "mytool", and you have already released version 1.0. Create (for example) the following directory structure:

`/opt/studio/packages/mytool/1.0/wrapper/` <- this is where your use package will live.

`/opt/studio/packages/mytool/1.0/modules/` <- this is where your python modules will live.

and

`/opt/studio/packages/mytool/dev/wrapper/` <- this is where your use package for the dev version will live. Note that there is no 'modules' directory. Your source code under development can live wherever you usually store your projects.

Now the use package for your released (1.0) version (in `/opt/studio/packages/mytool/1.0/wrapper/` and named `mytool.use`) of the module would (possibly) look like this:

```
[branch]
mytool

[path-prepend-PYTHONPATH]
/opt/studio/packages/mytool/$VERSION/modules/
```

Now when you type `use mytool-1.0` your python path will have been updated to point to the 1.0 release of your python packages.

But your use package for your development version (in `/opt/studio/packages/mytool/dev/wrapper/` and also named `mytool.use`) would (possibly) look like this:

```
[branch]
mytool

[path-prepend-PYTHONPATH]
/home/me/Documents/dev/mytool/modules/
```

And when you type `use mytool-dev` your python path will have been set to point to your development version of your python packages.

In this way it is easy to have multiple versions of python packages ready, and you simply 'use' the version you are interested in whenever you need to use one or the other.

This may seem to duplicate the functionality of Python's virtual environments. In reality, you would probably just use virtual environments, but call them from this use package. That leverages the power of the virtual environments, but wraps it up in a package that can also set enviro

###Other examples:
These are not the only two use cases. use packages can modify environmental variables, change path variables, set aliases, run shell commands, define .desktop files (not yet implemented), and even run arbitrary scripts when called.

Basically any changes you need to make to your shell environment prior to running an application or doing any work can be included in a .use package.

One use I have for it is to change "shows" when working on visual effects. Each show may be using a different version of an application (say Maya 2018 for one show and Maya 2017 for another). Use packages can call other use packages (not yet fully implemented) so that I can set up a default setting for a specific show simply by calling: `use showname-1.0` and suddenly I have all the specifics for this show set in my shell, including paths to OpenColorIO config files, specific versions of tools I have coded, and any other specific changes I want to make to my system that are unique to that particular shell.

I also have a basic set of applications that I want to use all of the time. Pycharm is one for example. So I simply put the `use pycharm 2018.2.4` command directly in my .bashrc file. Then I don't even have to type the use command out. I can simply type `pycharm` and it will launch the app. But if I suddenly want to try out a newer version, I can manually do that in a shell by 'using' the newer version.

It really is the cat's meow. :)

---
# Environmental Variables
Use understands the following environmental variables:

#####USE_PKG_SEARCH_PATHS

This is a list of paths where the system will look for use packages (files ending in .use that describe a single use package).
Defaults to `/opt/apps/:/opt/use/`

#####USE_PKG_SEARCH_RECURSIVE

A boolean determining whether to search sub-directories of the paths listed above. If this environment variable is not set, defaults to `True`.

#####USE_PKG_AUTO_VERSION

A boolean determining whether to automatically derive the version number for a use package based on some information in the path of this use package. Note, if you decide to use auto-versioning then ALL of your use packages must use auto-versioning. Likewise, if you choose not to use it, none of your use packages will use auto-versioning. If this environment variable is not set, defaults to `True`. 

#####USE_PKG_AUTO_VERSION_OFFSET

Where in the path to look for the version number given as an offset from the location of the use package. For example, if the path to the use package is:

`/this/is/the/path/to/the/use/package/v001/wrapper/package.use`

then you would want to set the offset to 2, meaning it would look up the hierarchy by two levels and find `v001`. If this environment variable is not set, defaults to `2`.

---
#FAQ:

- Didn't you just create a less good version of Python's virtual environments?

Kind of yes, and kind of no. But mostly no. Use packages can actually work with python virtual environments. You can switch virtual environments from directly within a use package.

Use packages are sort of like python's virtual environments (or a portion thereof), but extended outside of the Python programming environment.

- What about using docker?

Docker is a very powerful mechanism for virtualizing portions of your system. But it can be overkill and isn't really meant to be used for desktop applications. The Use system is fairly simple to set up and manage. It is intended to be easy and quick, without a lot of overhead. It merely manages different versions of applications and libraries on a simple desktop system.

- What are the system requirements?

Use was developed under python 3, and using the Bash shell. It runs on Linux and MacOS, though there is a chance it would also work on Windows using WSL. Beyond python 3 and Bash, there are no additional dependencies.