# use
A command line tool (and support structure) that switches between different installed versions of an app. This allows multiple versions of the same app to be installed (and used) at the same time. It is designed to work under UNIX-like systems like Linux and MacOS. It *may* work with WSL (Windows Subsystem for Linux) but is untested.

This toolset is based on a system that we use where I work.  This is my own interpretation and implementation.

This document is woefully under developed at the moment. I hope to update it in time.

---
# Installation
Just download the .zip file and unzip it in some location that makes sense to you.

Then add this line to your .bashrc file:

`source /directory/where/you/unzipped/the/downloaded/file/use.sh setup`

(Basically you want to source the use.sh script with the single argument 'setup')

This will result in the current shell being ready to start using the 'use' command. This needs to be run for each shell you create, which is why I suggest you put this in your .bashrc file. Running this command will create several other alias' for you. These are: use, unuse, and used (all of which are described below).

Note that a sample .use file is included with the download. It should give some insight on how the system works.

---
# Environment
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
# How the system works from an end-user perspective:
Assume you have two (or more) versions of an app (say, Blender-2.78 and Blender-2.79) on your system.

Say you want to run version 2.78. In a terminal window, you would type: "use blender-2.78". This sets up the current shell so that if you type "blender", you will launch Blender version 2.78.

If you want to run version 2.79, then you would type "user blender-2.79". From this point forward (and in this shell only) typing "blender" would launch Blender version 2.79.

In addition to the afore mentioned "use" command, here are also the following 3 additional commands:

"used" - Displays a list of the currently "used" packages in the current shell.

"unuse" - Removes a currently used package from the current shell (so that it cannot be run by typing its command
in that shell anymore).

"setup" - Initializes the whole use system. This needs to be run once per shell (usually as part of the .bashrc file).

---
# Under the hood
All of these commands are handled by a single shell script: use.sh.  This shell script accepts the individual commands (use, unuse, used, setup) as command line arguments.  The shell script also handles tab-completion (the user merely has to type the first few letters of a use package name and a list of matching packages will be displayed).

Individual application packages are managed by small text files that end in ".use".  One of these files must exist for every version of every application manged by the system.

Note: The actual location of the applications being managed by this system is completely arbitrary. Also, this system only works under the bash shell.

The actual use.sh command cannot be run. It must be sourced in order for the system to work.  This is made easier by the "setup" command which creates three alias' in the current shell. These alias' are: "use", "unuse", and "used".

The short description of how the system works is that it simply sets some environmental variables and alias' in the current shell (which is why it needs to be sourced). The script reads the settings from the .use file passed to it as an argument.

---
# Specific Use Cases
###Setting up multiple applications on a single system:
Let's assume you want to have more than one version of Blender running on your system, and you want to be able to quickly switch from one to the other.

Start by installing Blender to a location of your choosing. For my purposes I will always install all of my applications to /opt/. I use the following structure:

/opt/apps/[vendor]/[appname]/[version]/

Then within this directory I have two directories:

- app
- wrapper

I store the actual application in the 'app' directory. I store any custom wrappers and the .use file in the 'wrapper' directory.

So in the case of Blender I would have the following structure:

`/opt/apps/blender/blender/2.79/app` <- this holds the actual application files and directories

`/opt/apps/blender/blender/2.79/wrapper` <- this is where the blender.use file is stored.

The blender.use file is extremely simple and looks like this:

```
[branch]
blender

[alias]
blender=/opt/apps/blender/blender/$VERSION/app/blender
```

Since `/opt/apps/` is in the use package search path (and recursive is True) that means this blender.use file will be found by the system. And since auto-versioning is enabled (and the offset is set to `2`) that means it will look up two levels in the directory to find its version number.

So when you type `use bl` and hit `tab`, the system will auto-complete `blender-2.79` for you. Note that it has automatically added the version number (and dropped the .use).

But who wants to only use Blender 2.79 now that 2.80 are out?

So create some new directories:

`/opt/apps/blender/blender/2.80/app`

`/opt/apps/blender/blender/2.80/wrapper`

In the app directory, install the 2.8 version of Blender. In the wrapper directory just copy the .use file from 2.79. Note that since it uses the variable `$VERSION` you don't need to make any changes. It will simply work exactly as it did before.

Now when you type `use bl` and hit tab, you will be presented with two options: `blender-2.79` and `blender-2.80`. Note, again, that the version numbers have been automatically added to the use pacakges. You did not have to customize the .use file to include them manually. Once you finish typing `blender-2.80` you may now simply type: `blender` in this shell and blender 2.8 will start up.

Now you can continue this same pattern for every beta version of Blender. In a shell you can easily choose which one you want to 'use' simply by typing `use blender-<version>`. Feel free to have 100 different versions on your system without any concern that they will interfere with each other.

Note: the directory structure I indicated above is just how I set up my own system. The use system is quite freeform with regard to where .use files are stored and where the applications they relate to are stored. They do not have to be in the same hierarchy at all. That is just how I like to mange my system.
###Using different libraries on the same system:
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

###Other examples:
These are not the only two use cases. use packages can modify environmental variables, change path variables, set aliases, define .desktop files (not yet implemented), and even run arbitrary scripts when called.

Basically any changes you need to make to your shell environment prior to running an application or doing any work can be included in a .use package.

One use I have for it is to change "shows" when working on visual effects. Each show may be using a different version of an application (say Maya 2018 for one show and Maya 2017 for another). Use packages can call other use packages (not yet fully implemented) so that I can set up a default setting for a specific show simply by calling: `use showname-1.0` and suddenly I have all the specifics for this show set in my shell, including paths to OpenColorIO config files, specific versions of tools I have coded, and any other specific changes I want to make to my system that are unique to that particular shell.

I also have a basic set of applications that I want to use all of the time. Pycharm is one for example. So I simply put the `use pycharm 2018.2.4` command directly in my .bashrc file. Then I don't even have to type the use command out. I can simply type `pycharm` and it will launch the app. But if I suddenly want to try out a newer version, I can manually do that in a shell by 'using' the newer version.

It really is the cat's meow. :)