#!/usr/bin/env python3

import glob
import sys
import os
from os.path import join, dirname, exists, isdir
import re
import logging

import setuptools
from cx_Freeze import setup, Executable
from setuptools.command.install import install

from pyglossary.glossary import VERSION

log = logging.getLogger("root")
relRootDir = "share/pyglossary"


class my_install(install):
	def run(self):
		install.run(self)
		if os.sep == "/":
			binPath = join(self.install_scripts, "pyglossary")
			log.info("creating script file \"%s\"", binPath)
			if not exists(self.install_scripts):
				os.makedirs(self.install_scripts)
				# let it fail on wrong permissions.
			else:
				if not isdir(self.install_scripts):
					raise OSError(
						"installation path already exists " +
						"but is not a directory: %s" % self.install_scripts
					)
			open(binPath, "w").write(
				join(self.install_data, relRootDir, "main.py") +
				" \"$@\""  # pass options from command line
			)
			os.chmod(binPath, 0o755)


package_data = {
	"res": glob.glob("res/*"),
	"pyglossary": [
		"plugins/*.py",
		"langs/*",
		"plugin_lib/*.py",
		"plugin_lib/py*/*.py",
		"ui/*.py",
		"ui/progressbar/*.py",
		"ui/gtk3_utils/*.py",
		"ui/wcwidth/*.py",
	] + [
		# safest way found so far to include every resource of plugins
		# producing plugins/pkg/*, plugins/pkg/sub1/*, ... except .pyc/.pyo
		re.sub(
			r"^.*?pyglossary%s(?=plugins)" % ("\\\\" if os.sep == "\\" else os.sep),
			"",
			join(dirpath, f),
		)
		for top in glob.glob(
			join(dirname(__file__), "pyglossary", "plugins")
		)
		for dirpath, _, files in os.walk(top)
		for f in files
		if not (f.endswith(".pyc") or f.endswith(".pyo"))
	],
}


def files(folder):
	for path in glob.glob(folder + "/*"):
		if os.path.isfile(path):
			yield path


with open("README.md", "r", encoding="utf-8") as fh:
	long_description = fh.read()

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
	"packages": ["os"],
	"excludes": [],
}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
	name="pyglossary",
	version=VERSION,
	cmdclass={
		"install": my_install,
	},
	description="A tool for converting dictionary files aka glossaries.",
	long_description_content_type="text/markdown",
	long_description=long_description,
	author="Saeed Rasooli",
	author_email="saeed.gnu@gmail.com",
	license="GPLv3+",
	url="https://github.com/ilius/pyglossary",
	packages=[
		"pyglossary",
	],
	entry_points={
		'console_scripts': [
			'pyglossary = pyglossary.ui.main:main',
		],
	},
	package_data=package_data,
	options={
		"build_exe": build_exe_options,
	},
	executables=[Executable("pyglossary.pyw", base=base)]
)
