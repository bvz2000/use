#!/usr/bin/env python

import os
import shutil
import sys

"""
A series of functions designed to manage applications on Linux.
"""
STUDIO_APP_N = "studio"
COMM_APP_N = "commercial"


def create_studio_app(comm_app_p=None, comm_ver_d=None):
    """
    Create the studio app version of a commercial app.

    :param comm_app_p: The full path to the commercial app binary or script.
    :param comm_ver_d: The full path to the version dir.

    :return:
    """

    if not comm_app_p:
        print("Please enter the path to the app script or binary:")
        comm_app_p = input("Path to script or binary:")

    if not comm_ver_d:
        print("Please enter the path to the version directory:")
        comm_ver_d = input("Path to the version directory:")

    comm_app_p = comm_app_p.strip()
    comm_ver_d = comm_ver_d.strip()

    comm_app_p = comm_app_p.strip('"')
    comm_app_p = comm_app_p.strip("'")

    comm_ver_d = comm_ver_d.strip('"')
    comm_ver_d = comm_ver_d.strip("'")

    # Validate that these items exist.
    if not os.path.exists(comm_app_p):
        print("\n\nApp does not exist (" + comm_app_p + ")")
        sys.exit(1)
    if not os.path.exists(comm_ver_d) or not os.path.isdir(comm_ver_d):
        print("\n\nVersion directory does not exist (" + comm_ver_d + ")")
        sys.exit(1)

    # Clean up the comm_ver_d
    comm_ver_d = comm_ver_d.rstrip(os.path.sep)

    # Derive the script name (this is also the app name)
    app_n = os.path.split(comm_app_p)[1].lower()
    script_n = app_n.lower()
    if app_n.endswith(".sh"):
        app_n = os.path.splitext(app_n)[0]
    if not script_n.endswith(".sh"):
        script_n += ".sh"

    # Build the root dir, the studio and commercial dirs, as well as the
    # version string
    root_d = os.path.split(comm_ver_d)[0]
    current_d = os.path.join(root_d, "CURRENT")
    studio_d = os.path.join(comm_ver_d, STUDIO_APP_N)
    commercial_d = os.path.join(comm_ver_d, COMM_APP_N)
    version_n = os.path.split(comm_ver_d)[1]

    # Create this directory if it does not exist
    if not os.path.exists(studio_d):
        os.makedirs(studio_d)

    # Build the script path
    script_p = os.path.join(studio_d, script_n)
    script_current_p = os.path.join(current_d, STUDIO_APP_N, script_n)

    # Create the script if it does not already exist.
    if not os.path.exists(script_p):
        with open(script_p, "w") as f:
            f.write(comm_app_p + "\n")
    os.chmod(script_p, 0o755)

    # Bring over any .desktop files
    for dir_n, dirs_n, files_n in os.walk(commercial_d):
        for file_n in files_n:
            if file_n.endswith(".desktop"):
                desktop_source_p = os.path.join(dir_n, file_n)
                desktop_dest_p = os.path.join(studio_d, file_n)
                if not os.path.exists(desktop_dest_p):
                    shutil.copy(desktop_source_p, desktop_dest_p)
                else:
                    print("Warning: Not copying", desktop_source_p,
                          "because a file of that name already exists in",
                          studio_d)
                os.chmod(desktop_dest_p, 0o644)

    # Also copy the first of the desktop files we find over to a file named
    # <appname>.desktop and <appname>-current.desktop
    found = False
    app_desktop_p = os.path.join(studio_d, app_n + ".desktop")
    app_curr_desktop_p = os.path.join(studio_d, app_n + "-common.desktop")
    items = os.listdir(studio_d)
    for item in items:
        if item.endswith(".desktop"):
            if not os.path.exists(app_desktop_p):
                shutil.copy(os.path.join(studio_d, item), app_desktop_p)
                found = True
            # if not os.path.exists(app_curr_desktop_p):
            #     shutil.copy(os.path.join(studio_d, item), app_curr_desktop_p)
            #     found = True
            if found:
                break

    # Create a use package with the bare minimum amount of data
    ver_use_pkg = os.path.join(studio_d, app_n + "-" + version_n + ".use")
    curr_use_pkg = os.path.join(studio_d, app_n + "-current.use")

    # Version use package
    if not os.path.exists(ver_use_pkg):
        with open(ver_use_pkg, "w") as f:
            f.write("[branch]\n")
            f.write(app_n + "\n")
            f.write("\n")
            f.write("[env]\n")
            f.write(app_n.upper() + "_HOME=" + root_d + "\n")
            f.write("\n")
            f.write("[alias]\n")
            f.write(app_n + "=" + script_p + "\n")
            f.write("\n")
            f.write("[desktop]\n")
            f.write("desktop=" + app_desktop_p + "\n")
            f.write("\n")
            f.write("[path-prepend]\n\n")
            f.write("[path-postpend]\n\n")
            f.write("[cmds]\n\n")
            f.write("[unuse]\n\n")
    #
    # # Current use package
    # if not os.path.exists(curr_use_pkg):
    #     with open(curr_use_pkg, "w") as f:
    #         f.write("[branch]\n")
    #         f.write(app_n + "\n")
    #         f.write("\n")
    #         f.write("[env]\n")
    #         f.write(app_n.upper() + "_HOME=" + current_d + "\n")
    #         f.write("\n")
    #         f.write("[alias]\n")
    #         f.write(app_n + "=" + script_current_p + "\n")
    #         f.write("\n")
    #         f.write("[desktop]\n")
    #         f.write("desktop=" + app_desktop_p + "\n")
    #         f.write("\n")
    #         f.write("[path-prepend]\n\n")
    #         f.write("[path-postpend]\n\n")
    #         f.write("[cmds]\n\n")
    #         f.write("[unuse]\n\n")


if __name__ == "__main__":

    help_flags = ["-h", "-help", "--help", "-u", "-usage", "--usage"]
    for help_flag in help_flags:
        if help_flag in sys.argv or help_flag.upper() in sys.argv:
            usage = "Options are:\n"
            usage += " create-studio-app <path-to-app-binary> <path-to-version>"
            usage += "\n (both options are optional, and if you do not include"
            usage += " them you will be prompted for their values at run time.)"
            print(usage)
            sys.exit(0)

    if sys.argv[1] == "create-studio-app":
        try:
            app_path = sys.argv[2]
        except IndexError:
            app_path = None
        try:
            version_dir = sys.argv[3]
        except IndexError:
            version_dir = None

        create_studio_app(app_path, version_dir)

