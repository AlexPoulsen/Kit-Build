# Kit-Build
Easily build Kit (kitlang.org) from source and install it in the right place on Mac, Linux, and (with difficulty on) Windows†.
Can use the dev branch (currently no release version, so this is the default).
Can also run tests to verify everything is working fine. This is currently not available when installing on Windows with Scoop.
Also compiles a vscode extension and installs it (optional) and patches the Code Runner extension to allow running .kit files with a right click (optional).

Requires:
- npm and Visual Studio Code for installing the extension.
- Visual Studio Code and the Code Runner extension in order to modify it.

If Scoop is not installed, it will attempt to install it and try to install Kit with it again.
If .NET Runtime is not installed (necessary for Scoop), it will download it and attempt to install it and try to install Scoop again.
If Stack isn't installed, it will install Stack and try again.

Adds the toolchain path to startup files for Bash, Csh, Fish, Rc, Sh (requires running with sudo), Tcsh, Zsh. Shuoldn't have issues if any aren't installed. When the code for this in another script, Bash called from Python did not echo the variable, or messed up in some other way, and reports a failure. It was however in the startup scripts and could be `echo`'d successfully. If this occurs, try testing it manually to see if it has a path for `KIT_TOOLCHAIN_PATH`, if it does, `kitc` should work fine. If someone knows what is going on with this, please make a PR or issue so I can fix it.

If someone on Windows (or on any Linux Distro) wants to test it out, that would be awesome. I have a Mac with too little SSD space to boot up a VM to test any other platforms, so I may miss bugs on Windows or some Linux Distros.

Download and run in one line on fish on unixlikes:

`cd ~; and curl https://raw.githubusercontent.com/AlexPoulsen/Kit-Build/master/kit_build.py --create-dirs -sLo ~/kit_build_from_github.py; and python3 kit_build_from_github.py; and rm kit_build_from_github.py`

Same for bash and most other shells:

`cd ~ && curl https://raw.githubusercontent.com/AlexPoulsen/Kit-Build/master/kit_build.py --create-dirs -sLo ~/kit_build_from_github.py && python3 kit_build_from_github.py && rm kit_build_from_github.py`

† Windows support is buggy and while most `subprocess.run()` calls work in CMD or Powershell (I'm unsure if one works better than the other), the commands don't work called from Python. This could be fixed by doing `shell=True, executable="path/to/CMD/or/Powershell`. Additionally this does not set environment variables on Windows at this point. I don't have a Windows computer or space for a VM so it's quite hard to test things. Oddly, Colorama does not seem to be working for the Windows users I've walked through this. Still, it does serve as a guide to installing everything, since many of the commands here were only found after long amounts of searching. Help from Python programmers on Windows would be amazing.
