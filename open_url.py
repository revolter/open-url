# Open URL opens selected URLs, files, folders, or googles text
# Hosted at http://github.com/noahcoad/open-url

import sublime, sublime_plugin
import webbrowser, urllib, thread, re, os, subprocess

class OpenUrlCommand(sublime_plugin.TextCommand):
	open_me = ""
	open_with = None
	debug = False
	config = sublime.load_settings("open_url.sublime-settings")

	def run(self, edit=None, url=None):
		# sublime text has its own open_url command used for things like Help menu > Documentation
		# if a url is specified, then open it instead of getting text from the edit window
		if url is None:
			# retrieve multiple selections
			for selection in self.view.sel():
				# retrieve the text from the selection
				if selection.empty():
					text = self.selection(selection)
				else:
					text = self.view.substr(selection)

				# split the selected text by whitespace
				for url in text.split():
					self.parse(url)
		else:
			self.parse(url)

	# parse and open url
	def parse(self, url):
		# strip quotes if quoted
		if (url.startswith("\"") & url.endswith("\"")) | (url.startswith("\'") & url.endswith("\'")):
			url = url[1:-1]

		# find the relative path to the current file 'google.com'
		try:
			relative_path = os.path.normpath(os.path.join(os.path.dirname(self.view.file_name()), url))
		except TypeError:
			relative_path = None

		# debug info
		if self.debug:
			print("open_url debug : ", [url, relative_path])

		# check if one or more aliases are present
		if self.config.has('aliases'):
			# get all aliases
			for alias in self.config.get('aliases'):
				if url == alias:
					# retrieve alias value
					url = self.config.get('aliases')[alias]

		# if this is a directory, show it (absolute or relative)
		# if it is a path to a file, open the file in sublime (absolute or relative)
		# if it is a URL, open in browser
		# otherwise google it
		if os.path.isdir(url):
			os.startfile(url)

		elif relative_path and os.path.isdir(relative_path):
			os.startfile(relative_path)

		elif os.path.exists(url):
			self.choose_action(url)

		elif os.path.exists(os.path.expandvars(url)):
			self.choose_action(os.path.expandvars(url))

		elif relative_path and os.path.exists(relative_path):
			self.choose_action(relative_path)

		else:
			if "://" in url:
				webbrowser.open_new_tab(url)
			elif re.search(r"\w[^\s]*\.(?:com|co|uk|gov|edu|tv|net|org|tel|me|us|mobi|es|io)[^\s]*\Z", url):
				if not "://" in url:
					url = "http://" + url
				webbrowser.open_new_tab(url)
			else:
				url = "http://google.com/#q=" + urllib.quote(url, '')
				webbrowser.open_new_tab(url)

	# pulls the selection or url at the specified position
	def selection(self, s):
		# expand selection to possible URL
		start = s.a
		end = s.b

		# if nothing is selected, expand selection to nearest terminators
		if (start == end):
			view_size = self.view.size()
			terminator = list('\t\"\'><, []()')

			# move the selection back to the start of the url
			while (start > 0
					and not self.view.substr(start - 1) in terminator
					and self.view.classify(start) & sublime.CLASS_LINE_START == 0):
				start -= 1

			# move end of selection forward to the end of the url
			while (end < view_size
					and not self.view.substr(end) in terminator
					and self.view.classify(end) & sublime.CLASS_LINE_END == 0):
				end += 1

		# grab the URL
		return self.view.substr(sublime.Region(start, end)).strip()

	# for files, as the user if they's like to edit or run the file
	def choose_action(self, file):
		self.open_me = file
		action = 'menu'
		for auto in self.config.get('autoactions'):
			for ending in auto['endswith']:
				if (file.endswith(ending)):
					action = auto['action']
					if ('openwith' in auto):
						self.open_with = auto['openwith']
					break
		if action == 'menu':
			sublime.active_window().show_quick_panel(["Edit", "Run"], self.select_done)
		elif action == 'edit':
			self.select_done(0)
		elif action == 'run':
			self.select_done(1)

	# shell execution must be on another thread to keep Sublime from locking if it's a sublime file
	def run_me(self, file, open_with):
		if open_with:
			subprocess.call([open_with, file], shell = True)
		else:
			os.system("\"" + file + "\"")

	# for files, either open the file for editing in sublime, or shell execute the file
	def select_done(self, index):
		if index == 0:
			self.view.window().open_file(self.open_me)
		elif index == 1:
			thread.start_new_thread(self.run_me, (self.open_me, self.open_with))

# p.s. Yes, I'm using hard tabs for indentation.  bite me
# set tabs to whatever level of indentation you like in your editor
# for crying out loud, at least they're consistent here, and use
# the ST2 command "Indentation: Convert to Spaces", which will convert
# to spaces if you really need to be part of the 'soft tabs only' crowd =)