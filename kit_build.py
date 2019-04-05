import subprocess
import platform
import os
import urllib.request
import zipfile
import shutil
import json
import sys
import codecs
import typing

try:
	import colorama
except ImportError:
	subprocess.run(["pip", "install", "colorama"])
	import colorama

colorama.init()
system = platform.system()


def path_add(new_path: str):
	if new_path not in os.getenv('PATH'):
		os.environ["PATH"] += os.pathsep + new_path


class cd:
	"""Context manager for changing the current working directory"""

	def __init__(self, newPath):
		self.newPath = os.path.expanduser(newPath)

	def __enter__(self):
		self.savedPath = os.getcwd()
		os.chdir(self.newPath)

	def __exit__(self, etype, value, traceback):
		os.chdir(self.savedPath)


RED = "\033[1;31m"
BLUE = "\033[1;34m"
CYAN = "\033[1;36m"
GREEN = "\033[0;32m"
RESET = "\033[0;0m"
BOLD = "\033[;1m"
REVERSE = "\033[;7m"
if not (system.lower() in ["windows", "win", "win32", "win64"]):
	colors_supported = codecs.decode(subprocess.run(["tput", "colors"], capture_output=True).stdout, "ascii").replace("\n", "")
else:
	colors_supported = "256"
if colors_supported == "256":
	KIT1 = "\033[38;5;79m"
	KIT2 = "\033[38;5;80m"
	KIT3 = "\033[38;5;45m"
	KITSUCCESS = "\033[38;5;77m"
	KITFAIL = "\033[38;5;124m"
	KITYELLOW = "\033[38;5;220m"
else:
	KIT1 = "\033[1;36m"
	KIT2 = "\033[1;36m"
	KIT3 = "\033[1;36m"
	KITSUCCESS = "\033[1;36m"
	KITFAIL = "\033[1;31m"
	KITYELLOW = "\033[0;93m"


def reset_format():
	sys.stdout.write(RESET)
	print(flush=True, end="")


def text_gradient(text, colors=(KIT1, KIT2, KIT3)):
	out = ""
	lastwhere = 0
	for n in range(len(colors) + 1):
		where = len(text) * n // len(colors)
		clen = [0]
		counter = 0
		incr = 0
		for x in text.split(" "):
			incr = len(x) + incr + 1
			clen.append(incr)
			counter += 1
		clen = clen[0:len(clen) - 1]
		clendiff = []
		for c in clen:
			clendiff.append(abs(c - where))
		where = clen[clendiff.index(min(clendiff))]
		try:
			out += text[lastwhere:where] + colors[n]
		except IndexError:
			out += text[lastwhere:where]
		lastwhere = where
	return out


def prompt(text, default="y", kitcolor=False):
	"""returns true if yes and false if no"""
	default_indicator = " [Y/n] " if "y" == default.lower()[0] else " [y/N] "
	out = text + default_indicator
	if kitcolor:
		sys.stdout.write(BOLD)
		out = text_gradient(out)
	try:
		out = True if "y" == input(out).lower()[0] else False
	except IndexError:
		out = True if "y" == default.lower()[0] else False
	if kitcolor:
		reset_format()
	return out


def notify(text, color):
	sys.stdout.write(color)
	print(text, flush=True)
	reset_format()


def set_global_env_var(name, what, message=""):
	startup_files = {"csh":   os.environ["HOME"] + "/.cshrc",  # --------------- # csh
					"tcsh":  os.environ["HOME"] + "/.tcshrc",  # -------------- # tcsh
					"sh":    "/etc/profile",  # ------------------------------- # sh
					"bash":  os.environ["HOME"] + "/.bash_profile",  # -------- # bash
					"bash2": os.environ["HOME"] + "/.bashrc",  # -------------- # bash
					"zsh":   os.environ["HOME"] + "/.zshenv",  # -------------- # zsh
					"rc":    os.environ["HOME"] + "/.rcrc",  # ---------------- # rc
					"fish":  os.environ["HOME"] + "/.config/fish/config.fish"}  # fish
	commands = {"csh":  (lambda n, w: "setenv " + n + " " + w),  # ------------ # csh
				"tcsh": (lambda n, w: "setenv " + n + " " + w),  # ------------ # tcsh
				"sh":   (lambda n, w: "export " + n + "=" + w),  # ------------ # sh
				"bash": (lambda n, w: "export " + n + "=" + w),  # ------------ # bash
				"zsh":  (lambda n, w: "export " + n + "=" + w),  # ------------ # zsh
				"rc":   (lambda n, w: n + "=" + w),  # ------------------------ # rc
				"fish": (lambda n, w: "set -x " + n + " " + w)}  # ------------ # fish
	for n in startup_files.keys():
		try:
			if not get_global_env_var(name, what, n.replace("2", "")):
				try:
					with open(startup_files[n], "r+") as file:
						append = True
						for line in file.readlines():
							if line.replace("\n", "") == commands[n.replace("2", "")](name, what):
								append = False
						if append:
							file.seek(0, 2)
							file.write("\n" + commands[n.replace("2", "")](name, what) + "\n")
				except FileNotFoundError:
					with open(startup_files[n], "a+") as file:
						file.write("\n" + message + "\n" + commands[n.replace("2", "")](name, what) + "\n")
		except PermissionError:
			notify("Insufficient permissions to edit " + startup_files[n] + " for " + n.replace("2", "") + ", try running with sudo. File might also not exist.", BOLD + KITFAIL)
			notify("Continuing to next startup file...", BOLD + KITFAIL)


def get_global_env_var(name, what, which: typing.Union[str, bool] = True):
	commands = {"csh":  (lambda n: "echo $" + n),
				"tcsh": (lambda n: "echo $" + n),
				"sh":   (lambda n: "echo $" + n),
				"bash": (lambda n: "echo $" + n),
				"zsh":  (lambda n: "echo $" + n),
				"rc":   (lambda n: "echo $" + n),
				"fish": (lambda n: "echo $" + n)}
	if which and (which.__class__ == bool):
		output = {}
		all = True
		for n in commands.keys():
			shell_path = subprocess.run(["which", n], stdout=subprocess.PIPE).stdout.decode('utf-8').replace("\n", "")
			if shell_path == "":
				output[n] = "Shell not found"
			else:
				this_success = subprocess.run(commands[n](name), stdout=subprocess.PIPE, shell=True, executable=shell_path).stdout.decode('utf-8').replace("\n", "")
				# print(shell_path)
				# print(this_success, flush=True)
				output[n] = this_success
				all &= (this_success == what)
		return all, output
	else:
		shell_path = subprocess.run("which " + which, stdout=subprocess.PIPE, shell=True).stdout.decode('utf-8').replace("\n", "")
		return what == subprocess.run(commands[which](name).split(" "), stdout=subprocess.PIPE, shell=True, executable=shell_path).stdout.decode('utf-8')


if not (os.path.exists("kit") and os.path.isdir("kit")):
	subprocess.run(["git", "clone", "https://github.com/kitlang/kit.git"])

with cd("kit"):
	if prompt("Use dev branch?", "y", True):
		subprocess.run(["git", "fetch", "origin"])
		subprocess.run(["git", "checkout", "dev"])
	subprocess.run(["git", "pull"])
	print("Running on " + system)
	if system.lower() in ["windows", "win32", "win", "win64"]:
		localbin = os.path.abspath(os.getenv('APPDATA') + "\local\\bin")
		if prompt("Use new scoop install?", "y", True):
			# new build process with scoop
			try:
				subprocess.run(["scoop", "install", "'https://raw.githubusercontent.com/kitlang/kit/dev/.packages/scoop/kitlang-prerelease.json'"])
			except:
				this_path = os.path.dirname("\\".join(os.path.realpath(__file__).split("\\")[:-1]))
				try:
					subprocess.call(["Set-ExecutionPolicy", "RemoteSigned", "-scope", "CurrentUser"])
					subprocess.call(["C:\WINDOWS\system32\WindowsPowerShell\\v1.0\powershell.exe", "iex (new-object net.webclient).downloadstring('https://get.scoop.sh')"])
					subprocess.run(["scoop", "install", "'https://raw.githubusercontent.com/kitlang/kit/dev/.packages/scoop/kitlang-prerelease.json'"])
				except:
					urllib.request.urlretrieve("https://download.microsoft.com/download/0/5/C/05C1EC0E-D5EE-463B-BFE3-9311376A6809/NDP472-KB4054531-Web.exe", this_path + "\dotnet_4_7_2.exe")
					dotnet_installer = this_path + "\dotnet_4_7_2.exe"
					subprocess.call(dotnet_installer)
					subprocess.call(["Set-ExecutionPolicy", "RemoteSigned", "-scope", "CurrentUser"])
					subprocess.call(["C:\WINDOWS\system32\WindowsPowerShell\\v1.0\powershell.exe", "iex (new-object net.webclient).downloadstring('https://get.scoop.sh')"])
					subprocess.run(["scoop", "install", "'https://raw.githubusercontent.com/kitlang/kit/dev/.packages/scoop/kitlang-prerelease.json'"])
			if prompt("Run tests?", "n", True):
				notify("I don't know how to do this for scoop installs yet.", BOLD + KITFAIL)
		else:
			try:
				subprocess.run(["stack", "upgrade"])
			except:
				if "32" in system:
					urllib.request.urlretrieve("https://get.haskellstack.org/stable/windows-i386.zip", localbin + "\stack32.zip")
					location = localbin + "\stack32.zip"
				else:
					urllib.request.urlretrieve("https://get.haskellstack.org/stable/windows-x86_64.zip", localbin + "\stack64.zip")
					location = localbin + "\stack64.zip"
				path_add(localbin)
				zipfile.ZipFile(location, "r").extractall()
				os.remove(location)
			subprocess.run(["stack", "build"])
			if prompt("Run tests?", "n", True):
				subprocess.run(["stack", "test"])
			subprocess.run(["stack", "install"])
		shutil.rmtree(localbin + "\std")
		shutil.copytree(os.path.abspath("std"), os.path.abspath(localbin + "\std"))
		if prompt("Add Visual Studio Code extension?", "y", True):
			with cd("utils"):
				with cd("vscode-kitlang"):
					subprocess.run(["npm", "install", "-g", "vsce"])
					this_path = os.path.dirname("\\".join(os.path.realpath(__file__).split("\\")[:-1]) + "\kit\\utils\\vscode-kitlang")
					files_in_here = [f for f in os.listdir(this_path) if os.path.isfile(os.path.join(this_path, f))]
					for f in files_in_here:
						if f.split(".")[-1] == "vsix":
							os.remove(f)
					subprocess.run(["vsce", "package"])
					files_in_here = [f for f in os.listdir(this_path) if os.path.isfile(os.path.join(this_path, f))]
					for f in files_in_here:
						if f.split(".")[-1] == "vsix":
							subprocess.run(["code", "--uninstall-extension", "kitlang.kitlang"])
							subprocess.run(["code", "--install-extension", os.path.abspath(f)])
							os.remove(f)
			if prompt("Modify Code Runner extension?", "y", True):
				with cd(os.path.abspath(os.environ["USERPROFILE"] + "\.vscode\extensions")):
					this_path = os.path.abspath(os.environ["USERPROFILE"] + "\.vscode\extensions")
					files_in_here = [f for f in os.listdir(this_path) if os.path.isfile(os.path.join(this_path, f))]
					for f in files_in_here:
						if "code-runner" in f:
							with cd(f):
								with open("package.json", "r") as read_file:
									data = json.load(read_file)
								data["contributes"]["configuration"]["properties"]["code-runner.executorMap"]["default"]["kit"] = "kitc --run"
								with open("package.json", "w") as write_file:
									json.dump(data, write_file)
			notify("Please restart Visual Studio Code", KITYELLOW)

	else:
		try:
			subprocess.run(["stack", "upgrade"])
		except:
			subprocess.run(["curl", "-sSL", "https://get.haskellstack.org/ | sh"])
		subprocess.run(["stack", "build"])
		if prompt("Run tests?", "n", True):
			subprocess.run(["stack", "test"])
		subprocess.run(["stack", "install"])
		this_path = os.path.dirname("/".join(os.path.realpath(__file__).split("/")))
		notify("Attempting to add the Kit toolchain path to shell startup files...", BOLD + KITYELLOW)
		set_global_env_var("KIT_TOOLCHAIN_PATH", this_path + "/toolchains", "# kitc toolchain path - added by kit_build.py")
		success_condition = get_global_env_var("KIT_TOOLCHAIN_PATH", this_path + "/toolchains", True)
		if success_condition.__class__ == tuple:
			if success_condition[0]:
				notify("Toolchain path added to environment variable successfully", BOLD + KITSUCCESS)
			else:
				notify("Toolchain path not added to environment variable", BOLD + KITFAIL)
				notify(success_condition[1], BOLD + KITFAIL)
		else:
			if success_condition:
				notify("Toolchain path added to environment variable successfully", BOLD + KITSUCCESS)
			else:
				notify("Toolchain path not added to environment variable", BOLD + KITFAIL)
		try:
			if system.lower() == "darwin":
				# path_add(os.path.abspath("/usr/local/lib/"))
				shutil.copyfile(os.path.abspath(os.environ["HOME"] + "/.local/bin/kitc"), os.path.abspath("/usr/local/bin/kitc"))
				os.remove(os.path.abspath(os.environ["HOME"] + "/.local/bin/kitc"))
				if not os.path.exists(os.path.abspath("/usr/local/lib/kit/")):
					os.makedirs(os.path.abspath("/usr/local/lib/kit/"))
				shutil.rmtree(os.path.abspath("/usr/local/lib/kit/"))
				shutil.copytree(os.path.abspath("std"), os.path.abspath("/usr/local/lib/kit/"))
			else:
				# path_add(os.path.abspath("/usr/lib/"))
				shutil.copyfile(os.path.abspath(os.environ["HOME"] + "/.local/bin/kitc"), os.path.abspath("/usr/bin/kitc"))
				os.remove(os.path.abspath(os.environ["HOME"] + "/.local/bin/kitc"))
				if not os.path.exists(os.path.abspath("/usr/lib/kit/")):
					os.makedirs(os.path.abspath("/usr/lib/kit/"))
				shutil.rmtree(os.path.abspath("/usr/lib/kit/"))
				shutil.copytree(os.path.abspath("std"), os.path.abspath("/usr/lib/kit/"))
		except FileExistsError:
			pass
		if prompt("Add Visual Studio Code extension?", "y", True):
			with cd("utils"):
				with cd("vscode-kitlang"):
					subprocess.run(["npm", "install", "-g", "vsce"])
					this_path = os.path.dirname("/".join(os.path.realpath(__file__).split("/")[:-1]))
					files_in_here = [f for f in os.listdir(this_path) if os.path.isfile(os.path.join(this_path, f))]
					for f in files_in_here:
						if f.split(".")[-1] == "vsix":
							os.remove(f)
					subprocess.run(["vsce", "package"])
					files_in_here = [f for f in os.listdir(this_path) if os.path.isfile(os.path.join(this_path, f))]
					for f in files_in_here:
						if f.split(".")[-1] == "vsix":
							subprocess.run(["code", "--uninstall-extension", "kitlang.kitlang"])
							subprocess.run(["code", "--install-extension", os.path.abspath(f)])
							os.remove(f)
			if prompt("Modify Code Runner extension?", "y", True):
				with cd(os.path.abspath(os.environ["HOME"] + "/.vscode/extensions")):
					this_path = os.path.abspath(os.environ["HOME"] + "/.vscode/extensions")
					files_in_here = [f for f in os.listdir(this_path) if os.path.isfile(os.path.join(this_path, f))]
					for f in files_in_here:
						if "code-runner" in f:
							with cd(f):
								with open("package.json", "r") as read_file:
									data = json.load(read_file)
								data["contributes"]["configuration"]["properties"]["code-runner.executorMap"]["default"]["kit"] = "kitc --run"
								with open("package.json", "w") as write_file:
									json.dump(data, write_file)
			notify("Please restart Visual Studio Code", KITYELLOW)
