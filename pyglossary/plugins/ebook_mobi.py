# -*- coding: utf-8 -*-
# The MIT License (MIT)

# Copyright © 2012-2016 Alberto Pettarin (alberto@albertopettarin.it)
# Copyright © 2016-2020 Saeed Rasooli <saeed.gnu@gmail.com>

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from formats_common import *
from pyglossary.ebook_base import *

enable = True
lname = "mobi"
format = "Mobi"
description = "Mobipocket (.mobi) E-Book"
extensions = (".mobi",)
extensionCreate = ".mobi"
sortOnWrite = ALWAYS
kind = "package"
wiki = "https://en.wikipedia.org/wiki/Mobipocket"
website = None

tools = [
	{
		"name": "Amazon Kindle",
		"web": "https://www.amazon.com/kindle",
		"platforms": ["Amazon Kindle"],
		"license": "Proprietary",
	},
	{
		"name": "calibre",
		"web": "https://calibre-ebook.com/",
		"wiki": "https://en.wikipedia.org/wiki/Calibre_(software)",
		"repo": "https://github.com/kovidgoyal/calibre",
		"platforms": ["Linux", "Windows", "Mac"],
		"license": "GPL",
	},
	{
		"name": "Okular",
		"web": "https://okular.kde.org/",
		"wiki": "https://en.wikipedia.org/wiki/Okular",
		"repo": "https://invent.kde.org/graphics/okular",
		"platforms": ["Linux", "Windows", "Mac"],
		"license": "GPL",
	},
	{
		"name": "Book Reader",
		"web": "https://f-droid.org/en/packages/com.github.axet.bookreader/",
		"repo": "https://gitlab.com/axet/android-book-reader",
		"platforms": ["Android"],
		"license": "GPL",
	},
]

optionsProp = {
	"group_by_prefix_length": IntOption(
		comment="Prefix length for grouping",
	),
	# "group_by_prefix_merge_min_size": IntOption(),
	# "group_by_prefix_merge_across_first": BoolOption(),

	# specific to mobi
	"kindlegen_path": StrOption(
		comment="Path to kindlegen executable",
	),

	"compress": BoolOption(
		disabled=True,
		comment="Enable compression",
	),
	"keep": BoolOption(
		disabled=True,
		comment="Keep temp files",
	),
	"include_index_page": BoolOption(
		disabled=True,
		comment="Include index page",
	),
	"apply_css": StrOption(
		disabled=True,
		comment="Path to css file",
	),
	"cover_path": StrOption(
		disabled=True,
		comment="Path to cover file",
	),
}

extraDocs = [
	(
		"Other Requirements",
		"Install [KindleGen](https://wiki.mobileread.com/wiki/KindleGen)"
		" for creating Mobipocket e-books."
	),
]


class Writer(EbookWriter):
	_compress: bool = False
	_keep: bool = False
	_kindlegen_path: str = ""

	CSS_CONTENTS = """"@charset "UTF-8";"""
	GROUP_XHTML_TEMPLATE = """<?xml version="1.0" encoding="utf-8" standalone="no"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
	<head>
		<title>{title}</title>
		<link rel="stylesheet" type="text/css" href="style.css" />
	</head>
	<body id="groupPage" class="groupPage">
		<h1 class="groupTitle">{group_title}</h1>
		<div class="groupNavigation">
			<a href="{previous_link}">[ Previous ]</a>
{index_link}
			<a href="{next_link}">[ Next ]</a>
		</div>
{group_contents}
	</body>
</html>"""

	GROUP_XHTML_INDEX_LINK = """\t\t<a href="index.xhtml">[ Index ]</a>"""

	GROUP_XHTML_WORD_DEFINITION_TEMPLATE = """\t<div class="groupEntry">
		<idx:entry>
			<h2 class="groupHeadword"><idx:orth>{headword}</idx:orth></h2>
			<p class="groupDefinition">{definition}</p>
		</idx:entry>
	</div>"""

	OPF_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<package unique-identifier="uid">
	<metadata>
		<dc-metadata xmlns:dc="http://purl.org/metadata/dublin_core"
			xmlns:oebpackage="http://openebook.org/namespaces/oeb-package/1.0/">
			<dc:Title>{title}</dc:Title>
			<dc:Language>{sourceLang}</dc:Language>
			<dc:Identifier id="uid">{identifier}</dc:Identifier>
			<dc:Creator>{creator}</dc:Creator>
			<dc:Rights>{copyright}</dc:Rights>
			<dc:Subject BASICCode="REF008000">Dictionaries</dc:Subject>
		</dc-metadata>
		<x-metadata>
			<output encoding="utf-8"></output>
			<DictionaryInLanguage>{sourceLang}</DictionaryInLanguage>
			<DictionaryOutLanguage>{targetLang}</DictionaryOutLanguage>
			<EmbeddedCover>{cover}</EmbeddedCover>
		</x-metadata>
	</metadata>
	<manifest>
{manifest}
	</manifest>
	<spine>
{spine}
	</spine>
	<tours></tours>
	<guide></guide>
</package>"""

	def __init__(self, glos, **kwargs):
		import uuid
		EbookWriter.__init__(
			self,
			glos,
		)
		glos.setInfo("uuid", str(uuid.uuid4()).replace("-", ""))

	def write(self):
		import subprocess

		filename = self._filename
		kindlegen_path = self._kindlegen_path

		yield from EbookWriter.write(self)

		# download kindlegen from this page:
		# https://www.amazon.com/gp/feature.html?ie=UTF8&docId=1000765211

		# run kindlegen
		if not kindlegen_path:
			log.warn(f"Not running kindlegen, the raw files are located in {filename}")
			log.warn(
				"Provide KindleGen path with: "
				"--write-options 'kindlegen_path=...'"
			)
			return

		name = self._glos.getInfo("name")

		log.info("Creating .mobi file with kindlegen, using '{kindlegen_path}'")
		opf_path_abs = join(filename, "OEBPS", "content.opf")
		proc = subprocess.Popen(
			[kindlegen_path, opf_path_abs, "-o", "content.mobi"],
			stdout=subprocess.PIPE,
			stdin=subprocess.PIPE,
			stderr=subprocess.PIPE
		)
		output = proc.communicate()
		log.info(output[0].decode("utf-8"))
		mobi_path_abs = os.path.join(filename, "OEBPS", "content.mobi")
		log.info(f"Created .mobi file with kindlegen: {mobi_path_abs}")
