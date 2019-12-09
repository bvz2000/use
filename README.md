# use
A command line tool (and support structure) that switches between different installed versions of an app (or library or anything that can be set in a shell). This allows multiple versions of the same app to be installed (and used) at the same time. It can also be used to load specific libraries under specific cases (i.e. a development version of a python library in one shell, but the production version in another shell). Think of it as being something like a virtual environment but for desktop applications (among other uses).

It is designed to work under UNIX-like systems like Linux and MacOS. It *may* work with WSL (Windows Subsystem for Linux) but is untested. It is currently only set up to work under the BASH shell, but it would be relatively trivial to add other shells if there was some demand for this.

This toolset is based on a system that we use where I work.  This is my own interpretation and implementation.

This document is woefully under developed at the moment. I hope to update it in time.

---
# Installation
Just download the .zip file and unzip it in some location that makes sense to you.

Then add this line to your .bashrc file:

`source /directory/where/you/unzipped/the/downloaded/file/use.sh setup`

(Basically you want to source the use.sh script with the single argument 'setup')

This will result in the current shell being ready to start using the 'use' command. 

This needs to be run for each shell you create, which is why I suggest you put this in your .bashrc file. Running this command will create several other alias' for you. These are: use, unuse, and used (all of which are described below).

Note that a sample .use file is included with the download. It should give some insight on how the system works.

Use has no dependencies other than bash and the standard python 3 installation.

---
# How the system works from an end-user perspective:
Assume you have two (or more) versions of an app (say, Blender-2.79 and Blender-2.80) on your system.

Say you want to run version 2.79. In a terminal window, you would type: "use blender-2.79". This sets up the current shell so that if you type "blender", you will launch Blender version 2.79.

If you want to run version 2.80, then you would type "use blender-2.80". From this point forward (and in this shell only) typing "blender" would launch Blender version 2.80.

If you had 100 different versions of Blender on your system, merely by typing `use blender-<version>` would allow you to choose to run that specific version.

This also works for dependencies. If you had a set of tools that Blender relied
on, but which had different versions for different tasks, you could `use blender-tools-<version>` in a specific shell and know that
when Blender called those tools, it would be calling the version you just "used". A different shell could be using a different set.

In addition to the afore-mentioned "use" command, there are also the following 3 additional commands:

"used" - Displays a list of the currently "used" packages in the current shell.

"unuse" - Removes a currently used package from the current shell (it essentially removes all of the modifications made to the shell by the original use command).

"setup" - Initializes the whole use system. This needs to be run once per shell (This is usually done as part of the .bashrc file and as such becomes more or less invisible to the end user).

---
# Under the hood
All of these commands are handled by a single shell script: use.sh.  This shell script accepts the individual commands (use, unuse, used, setup) as command line arguments.  The shell script also handles tab-completion (the user merely has to type the first few letters of a use package name and a list of matching packages will be displayed). The shell script is only responsible for handing the use request off to a python script (use.py) which does the actual processing. This python script then returns a bash command in the form of a string which the shell script then executes.

The actual use.sh command cannot be run. It must be sourced in order for the system to work.  This is made easier by the "setup" command which creates three alias' in the current shell. These alias' are: "use", "unuse", and "used".

The setup command MUST be run once for each shell where you intend to use the use or unuse commands. Since this would be annoying to have to remember to type each time you create a new shell, it is recommended that you add this command to your .bashrc file:

`source /directory/where/you/installed/the/use/system/use.sh setup`

#####Use Packages
Individual application packages are managed by small text files that end in ".use".  One of these files must exist for every version of every application manged by the use system. These files live somewhere in one of the search paths where the use system knows to look for these .use files (also known as use packages). 

The default search paths are:

`/opt/apps`

and

`opt/use`

but note that these search paths may be set to any arbitrary set of paths by modifying an environmental variable (described below).

The applications that are managed by these use packages may live anywhere on the system or network. I have a preferred setup which I describe below, but the actual structure of where use packages and the files they represent is completely free-form.

A .use file (use package) is formatted as a standard, windows-style .ini file. The following is an example use package file. Note that normally you would not set one up with all of the contents being shown here. This example is over-provisioned simply to show what kinds of options are available. Lower down in this document I show some more common examples of use packages.

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
ls -l

[unuse-cmds]
cd ~
```

- branch - (Required). This is a single line that names the particular use package, without a version number. This allows the various versions of a particular application to interact with each other. So, for example, if this particular use package is for a version of Blender, the branch would simply be "blender".
- env - (Optional). This is a list of environmental variables to set in the form of: env = value. You may set as many env variables as desired in this section, with one assignment per line.
- alias - (Optional). This is a list of aliases to set in the form of: alias = value. You may set as many aliases as desired in this section, with one assignment per line.
- desktop - (Optional). This is a path to a .desktop file for the current application. This is used to automatically add .desktop files in Linux based systems. (UNDER DEVELOPMENT)
- path-prepend-PATH_VARIABLE - (Optional). Path environment variables are a special case of environmental variables. You may add one section named: "path-prepend-PATH_VARIABLE" for each path variable you wish to prepend a value to. For example, if you wanted to prepend the paths `/opt/apps/scripts` and `/opt/apps/tools` to your PYTHONPATH variable, you would create a section called: [path-prepend-PYTHONPATH]. The contents of this section would have each of the previous two paths, one on each line. If you wanted to prepend to another path (PATH for example) you would add another section called:[path-prepend-PATH] and populate it with as many paths as you wanted to prepend to that variable. There is no limit to the number of paths you may modify with these sections, nor any limit to the number of paths you may prepend in any single section.
- path-postpend-PATH_VARIABLE: (Optional). This works identically to the path-prepend sections, but any paths you include will be appended to the end of the path variables instead of being prepended to the beginning.
- use-scripts: (Optional). This is a simple list of scripts to call during the use process. These scripts may be any executable file (not simply limited to shell scripts). There is no limitation to what these scripts may do, but for security purposes they must be owned by root and only writable by root (this may be modified by changing some constants in the code - see below). Scripts will be sourced, not run, so they may affect the status of the current shell.
- unuse-scripts: (Optional). Like the use-scripts, this is a list of executables to call when running the unuse command. The same permissions requirements apply. 
- use-cmds: (Optional). This is a simple list of single line shell commands to execute during the use command. If you include an executable in this section, no security checks are done, so it is best to limit the use of this section to simple commands (such as setting Python virtual environments for example), and leaving the calling of custom executables to the use-scripts section.
- unuse-cmds: (Option). Identical to the use-cmds section, except these commands are executed during the unuse process.

#####Versioning

The use system handles versioning of use packages in two separate ways. The most useful is to let the system auto-manage versions. In this case you would name your use package something like: `blender.use`, and place it in a directory that has the version number somewhere in the path. For example:

`opt/apps/blender/blender/2.80/wrapper`

The use system will look at the path and automatically identify the version as being 2.80. The use package will then be presented to the end user as: `blender-2.80`. The system uses an environmental variable called `USE_PKG_AUTO_VERSION_OFFSET` to determine where to look for the version number in a path. By default, this is set to `2`, and represents an offset from where the use package is stored. So to use the 

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