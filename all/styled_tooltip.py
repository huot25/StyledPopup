"""StyledPopup"""
import sublime
import sublime_plugin
import os
import hashlib

from plistlib import readPlistFromBytes

def show_popup(view, content, **kwargs):
	if (view == None):
		view = self.window.active_view()

	manager = StyleSheetManager()
	style_sheet = manager.get_stylesheet(view.settings().get("color_scheme"))["content"]

	html = "<style>%s</style>" % (style_sheet)
	html += content

	view.show_popup(html, **kwargs)

class SchemeParser():
	"""Parses color scheme and builds css file"""

	def run(self):
		"""Parse the color scheme for the active view."""

		print ("Styled Popup: Parsing color scheme")
		content = self.load_color_scheme()
		plist_dict = self.read_scheme(content)
		css_stack = self.parse_plist(plist_dict["settings"])
		style_sheet = self.generate_style_sheet_content(css_stack)
		return style_sheet

	def load_color_scheme(self, view=None):
		"""Read the color_scheme user settings and load the file contents."""

		if view == None:
			view = sublime.active_window().active_view()

		scheme = view.settings().get("color_scheme")
		content  = sublime.load_binary_resource(scheme)
		return content

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


class StyleSheetManager():

	def __init__(self):
		self.theme_file_path = sublime.packages_path() + os.sep + "User" + os.sep + "theme_styles.json"

	def get_stylesheets_content(self):
		"""Load the content of the theme_styles.json file."""

		content = None

		if (os.path.isfile(self.theme_file_path)):
			content = sublime.load_resource("Packages/User/theme_styles.json")

		return content

	def get_stylesheets(self):
		"""Get the stylesheet dict from the file or return an empty dictionary no file contents."""

		content = self.get_stylesheets_content()
		if (content):
			style_sheets = sublime.decode_value(str(content))
		else:
			style_sheets = {}
			
		return style_sheets

	def set_stylesheets(self, style_sheets):
		"""Save the stylesheet dictionary to file"""

		content = sublime.encode_value(style_sheets, True)

		with open(self.theme_file_path, "w") as f:
			f.write(content)

	def has_stylesheet(self, color_scheme):
		"""Check if the stylesheet dictionary has the current color scheme."""

		if color_scheme in self.get_stylesheets():
			return True

		return False

	def add_stylesheet(self, color_scheme, content):
		"""Add the parsed color scheme to the stylesheets dictionary."""

		style_sheets = self.get_stylesheets()
		file_hash = self.get_file_hash(color_scheme)
		style_sheets[color_scheme] = {"content": content, "hash": file_hash}
		self.set_stylesheets(style_sheets)

	def get_stylesheet(self, color_scheme):
		"""Get the supplied color scheme stylesheet if it exists."""

		style_sheets = self.get_stylesheets()
		return style_sheets[color_scheme]

	def get_file_hash(self, color_scheme):
		"""Generate an MD5 hash of the color scheme file to be compared for changes."""

		content = sublime.load_binary_resource(color_scheme)
		file_hash = hashlib.md5(content).hexdigest()
		return file_hash

	def check_file_hash(self, color_scheme):
		"""Check if the color scheme file has changed on disk."""

		current_hash = self.get_file_hash(color_scheme)
		stored_hash = self.get_stylesheet(color_scheme)["hash"]
		return (current_hash == stored_hash)


class ColorSchemeListener(sublime_plugin.EventListener):
	def on_activated_async(self, view):
		"""Parse the color scheme if needed or if the color scheme file has changed."""

		if view == None:
			return

		manager = StyleSheetManager()
		color_scheme = view.settings().get("color_scheme")

		if (not manager.has_stylesheet(color_scheme) or 
		    not manager.check_file_hash(color_scheme)):
			style_sheet = SchemeParser().run()
			manager.add_stylesheet(color_scheme, style_sheet)

# add the custom event listener to the plugin callbacks manually so the on_activated handler is called
sublime_plugin.all_callbacks["on_activated_async"].append(ColorSchemeListener())






