"""Styled Tooltip"""
import sublime
import sublime_plugin
import os

from plistlib import readPlistFromBytes

RUNNING = False
USER_SETTINGS = {}

class SchemeParser():
	"""Parses color scheme and builds css file"""

	def load_color_scheme(self):
		"""Read the color_scheme user settings and load the file contents."""

		scheme_path = sublime.load_settings("Preferences.sublime-settings").get("color_scheme", "Packages/Color Scheme - Default/Monokai.tmTheme")
		scheme = sublime.load_binary_resource(scheme_path)
		return scheme

	def read_scheme(self, scheme):
		"""Converts supplied scheme(bytes) to python dict."""

		return  readPlistFromBytes(scheme)

	def parse_plist(self, root):
		"""Parse the supplied plist dictionary node into a dictionary of css classes and properties."""

		# Create a dictionary to hold the css classes and properties. 
		css_stack = {}
		for node in root:

			# If the node does not have a settings node, skip it
			if not len(node["settings"]):
				continue

			tmp_dict = {}

			# Parse the settings for the node and map 
			for key in node["settings"]:
				for value in node["settings"][key].split():
					css = CSSHelper.get_css_name(key, value)

					# If no mapping exists for the key, skip it
					if (css == None):
						continue

					# Create a dictionary entry for each valid key and value.
					tmp_dict[css] = CSSHelper.get_property_value(css, value)

			if not len(tmp_dict):
				continue

			# If no scope node, assume it is the default settings
			if not "scope" in node :
				# tmp_dict["margin"] = "2px"
				# tmp_dict["padding"] = "1em"
				tmp_dict[CSSHelper.CSS_NAME_MAP["background"]] = ColorHelper().getTintedColor(tmp_dict[CSSHelper.CSS_NAME_MAP["background"]], 10)
				css_stack["html"] = tmp_dict
			else:
				# Create the css class node
				scope = "." + node["scope"].lower()

				# If multiple scopes, split and apply to each
				scopes = scope.split(",")


				for i, s in enumerate(scopes):
					if not scopes[i].startswith("."):
						scopes[i] = "."+scopes[i].strip()

					# TODO - may need to rethink this piece to be more consistent with how css in HTML works...
					scopes[i] = scopes[i].replace(" ", "_")

					css_stack[ scopes[i] ] = tmp_dict

		return css_stack

	def generate_style_sheet(self, dict):
		"""Create a css file from the css generated from the scheme"""

		file_path = sublime.packages_path() + os.sep + "User" + os.sep + "theme_styles.css"
		f = open(file_path, "w")
		f.write(self.generate_style_sheet_content(dict))
		f.close()

	def generate_style_sheet_content(self, dict):
		file_content = ""
		for css_class in dict:
			properties = CSSHelper.get_properties_string(css_class, dict)
			file_content += "%s { %s } " % (css_class, properties)

		return file_content


class CSSHelper():

	CSS_NAME_MAP = {
		"background": "background-color", 
		"foreground": "color"
	}

	CSS_DEFAULT_VALUES = {
		"font-style": "normal",
		"font-weight": "normal",
		"text-decoration": "none"
	}

	@staticmethod
	def get_css_name(name, value):
		"""Get the css name of a scheme value."""

		# fontStyle can be mapped to font-style and font-weight. Need to handle both
		if "fontStyle" == name:
			if value == "bold":
				return "font-weight"

			if value == "underline":
				return "text-decoration"

			return "font-style"

		if name in CSSHelper.CSS_NAME_MAP:
			return CSSHelper.CSS_NAME_MAP[name]

		return None

	@staticmethod
	def get_properties_string(css_class, dict):
		"""Build a list of css properties and return as string."""

		properties = ""
		for prop in dict[css_class]:
			properties +=  "%s: %s; " % (prop, dict[css_class][prop])

		return properties

	@staticmethod
	def get_property_value(prop, value):
		if len(value.strip()):
			return value

		if prop in CSSHelper.CSS_DEFAULT_VALUES:
			print (CSSHelper.CSS_DEFAULT_VALUES[prop])
			return CSSHelper.CSS_DEFAULT_VALUES[prop]


class ColorHelper():
	"""Helper class responsible for all color based calculations and conversions."""

	def getTintedColor(self, color, percent):
		"""Adjust the average color by the supplied percent."""

		rgb = self.hex_to_rgb(color)
		average = self.get_rgb_average(rgb)
		mode = 1 if average < 128 else -1

		delta = ((256 * (percent / 100)) * mode)
		rgb = (rgb[0] + delta, rgb[1] + delta, rgb[2] + delta)
		color = self.rgb_to_hex(rgb)

		return color

	def get_rgb_average(self, rgb):
		"""Find the average value for the curren rgb color."""

		return int( sum(rgb) / len(rgb) )

	def hex_to_rgb(self, color):
		"""Convert a hex color to rgb value"""

		hex_code = color.lstrip("#")
		hex_length = len(hex_code)

		#Break the hex_code into the r, g, b hex values and convert to decimal values.
		rgb = tuple(int(hex_code[i:i + hex_length // 3], 16) for i in range(0,hex_length,hex_length //3))

		return rgb

	def rgb_to_hex(self, rgb):
		""" Convert the supplied rgb tuple into hex color value"""

		return "#%02x%02x%02x" % rgb


class StyledTooltipCommand(sublime_plugin.WindowCommand):
	def run(self, content, flags = 0, location = -1, max_width = 320, max_height = 240,
		on_navigate = None, on_hide = None, view=None):
		"""Read the contents of the generated stylesheet and prepend the stylesheet
		     content within a style tag.
		"""

		if (view == None):
			view = self.window.active_view()

		style_sheet = sublime.load_resource("Packages/User/theme_styles.css")

		html = "<style>%s</style>" % (style_sheet)
		html += content

		view.show_popup(html, flags, location, max_width, max_height, on_navigate, on_hide)


class ParseSchemeCommand(sublime_plugin.ApplicationCommand):

	def run(self):
		global RUNNING

		if (RUNNING):
			return

		RUNNING = True
		parser = SchemeParser()
		scheme = parser.load_color_scheme()
		plist_dict = parser.read_scheme(scheme)
		css_stack = parser.parse_plist(plist_dict["settings"])

		parser.generate_style_sheet(css_stack)
		RUNNING = False


def plugin_loaded():
	load_settings()

	if USER_SETTINGS["run_on_plugin_loaded"]:
		add_listener()
		sublime.run_command("parse_scheme")

def load_settings():
	settings = sublime.load_settings("Preferences.sublime-settings")

	USER_SETTINGS["run_on_plugin_loaded"] = settings.get("run_on_plugin_loaded", True)
	USER_SETTINGS["run_on_scheme_change"] = settings.get("run_on_scheme_change", True)

def add_listener():
	if USER_SETTINGS["run_on_scheme_change"]:
		settings = sublime.load_settings("Preferences.sublime-settings")
		settings.add_on_change("color_scheme", scheme_changed)


def scheme_changed():
	global RUNNING

	if USER_SETTINGS["run_on_scheme_change"]:
		if (not RUNNING):
			sublime.run_command("parse_scheme")



### Command for testing ###

class StyledTooltipTestCommand(sublime_plugin.WindowCommand):
	def run(self):
		content = "<p class=\"constant language\">Keyword</p>"
		content += "<p class=\"comment line\">This is a comment</p>"
		content += "<p class=\"support function\">Storage Type</p>"
		content += "<p class=\"entity other inherited-class\">What</p>"

		self.window.run_command("styled_tooltip", {"content": content, "max_width": 600} )

