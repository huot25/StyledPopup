"""StyledPopup"""
import sublime
import sublime_plugin
import os
import hashlib

from plistlib import readPlistFromBytes

def show_popup(view, content, *args, **kwargs):
	"""Parse the color scheme if needed and show the styled pop-up."""

	if view == None:
		return

	manager = StyleSheetManager()
	color_scheme = view.settings().get("color_scheme")

	style_sheet = manager.get_stylesheet(color_scheme)["content"]

	html = "<style>%s</style>" % (style_sheet)
	html += content

	view.show_popup(html,  *args, **kwargs)


class StyleSheetManager():
	"""Handles loading and saving data to the file on disk as well as provides a simple interface for"""
	"""accessing the loaded style sheets. """
	style_sheets = {}

	def __init__(self):
		self.theme_file_path = os.path.join([sublime.packages_path(), "User", "theme_styles.json"])
		self.resource_path = "/".join(["Packages", "User", "theme_styles.json"])
		self.style_sheets = {}

	def is_stylesheet_parsed_and_current(self, color_scheme):
		"""Parse the color scheme if needed or if the color scheme file has changed."""

		if not self.has_stylesheet(color_scheme) or not self.is_file_hash_stale(color_scheme):
			return False

		return True

	def load_stylesheets_content(self):
		"""Load the content of the theme_styles.json file."""

		content = None

		if  os.path.isfile(self.theme_file_path):
			content = sublime.load_resource(self.resource_path)

		return content

	def get_stylesheets(self):
		"""Get the stylesheet dict from the file or return an empty dictionary no file contents."""
		
		if not len(self.style_sheets):
			content = self.load_stylesheets_content()
			if  len(content):
				self.style_sheets = sublime.decode_value(str(content))
			
		return self.style_sheets

	def save_stylesheets(self, style_sheets):
		"""Save the stylesheet dictionary to file"""
	
		content = sublime.encode_value(style_sheets, True)

		with open(self.theme_file_path, "w") as f:
			f.write(content)

		self.style_sheets = style_sheets

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
		self.save_stylesheets(style_sheets)

	def get_stylesheet(self, color_scheme):
		"""Get the supplied color scheme stylesheet if it exists."""
		active_sheet = None

		if self.is_stylesheet_parsed_and_current(color_scheme):
			active_sheet = self.get_stylesheets()[color_scheme]
		else:
			active_sheet = SchemeParser().run(color_scheme)
			self.add_stylesheet(color_scheme, active_sheet)

		return active_sheet

	def get_file_hash(self, color_scheme):
		"""Generate an MD5 hash of the color scheme file to be compared for changes."""

		content = sublime.load_binary_resource(color_scheme)
		file_hash = hashlib.md5(content).hexdigest()
		return file_hash

	def is_file_hash_stale(self, color_scheme):
		"""Check if the color scheme file has changed on disk."""

		current_hash = self.get_file_hash(color_scheme)
		stored_hash = self.get_stylesheet(color_scheme)["hash"]
		return (current_hash == stored_hash)


class SchemeParser():
	"""Parses color scheme and builds css file"""

	def run(self, color_scheme):
		"""Parse the color scheme for the active view."""

		print ("Styled Popup: Parsing color scheme")

		content = self.load_color_scheme(color_scheme)
		scheme = self.read_scheme(content)
		css_stack = StackBuilder().create_css_stack(scheme["settings"])
		style_sheet = self.generate_style_sheet_content(css_stack)
		return style_sheet

	def load_color_scheme(self, color_scheme):
		"""Read the color_scheme user settings and load the file contents."""

		content  = sublime.load_binary_resource(color_scheme)
		return content

	def read_scheme(self, scheme):
		"""Converts supplied scheme(bytes) to python dict."""

		return  readPlistFromBytes(scheme)

	def generate_style_sheet_content(self, properties):
		file_content = ""
		for css_class in properties:
			properties_string = CSSFactory.generate_properties_string(css_class, properties)
			file_content += "%s { %s } " % (css_class, properties_string)

		return file_content

class StackBuilder():
	stack = {}

	def __init__(self):
		self.clear_stack()

	def clear_stack(self):
		self.stack = {}

	def is_valid_node(self, node):
		if "settings" not in node:
			return False

		if not len(node["settings"]):
			return False

		return True

	def is_base_style(self, node):
		if "scope" in node:
			return False

		return True

	def build_stack(self, root):
		"""Parse scheme dictionary into css classes and properties."""

		self.clear_stack()
		for node in root:
			css_properties = {}

			if not self.is_valid_node(node):
				continue

			styles = node["settings"]
			css_properties = self.generate_css_properties(styles)

			if not len(css_properties):
				continue

			if self.is_base_style(node):
				self.set_base_style(css_properties)
			else:
				classes = self.get_node_classes_from_scope(node["scope"])
				self.apply_properties_to_classes(classes, css_properties)

	def generate_css_properties(self, styles):
		properties = {}
		for key in styles:
			for value in styles[key].split():
				new_property = CSSFactory.generate_new_property(key, value)
				properties.update(new_property)

		return properties

	def set_base_style(self, css_style):
		self.stack["html"] = css_style

	def apply_properties_to_classes(self, classes, properties):
		for css_class in classes:
			self.set_scope_style(css_class, properties)

	def set_class_properties(self, css_class, properties):
		self.stack[css_class] = properties
				
	def get_node_classes_from_scope(self, scope):
		scope = "." + scope.lower()
		scopes = scope.split(",")
		return scopes


class CSSFactory():

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
	def generate_new_property(key, value):
		new_property = {}
		value = value.strip()
		
		property_name = CSSFactory.get_property_name(key, value)

		if (property_name == None):
			return new_property

		if len(value):
			new_property[property_name] = value
		else:
			new_property[property_name] = CSSFactory.get_property_default(property_name, value)

		return new_property

	@staticmethod
	def generate_properties_string(css_class, dict):
		"""Build a list of css properties and return as string."""

		properties = ""
		for prop in dict[css_class]:
			properties +=  "%s: %s; " % (prop, dict[css_class][prop])

		return properties

	@staticmethod
	def get_property_name(name, value):
		"""Get the css name of a scheme value if supported."""

		# fontStyle can be mapped to font-style and font-weight. Need to handle both
		if name == "fontStyle":
			if value == "bold":
				return "font-weight"

			if value == "underline":
				return "text-decoration"

			return "font-style"

		if name in CSSFactory.CSS_NAME_MAP:
			return CSSFactory.CSS_NAME_MAP[name]

		return None

	@staticmethod
	def get_property_default(prop):
		if prop in CSSFactory.CSS_DEFAULT_VALUES:
			return CSSFactory.CSS_DEFAULT_VALUES[prop]

		return None

class ColorFactory():
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
