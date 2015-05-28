import sublime, sublime_plugin, os
from plistlib import readPlistFromBytes

running = False

class StyledTooltipCommand(sublime_plugin.WindowCommand):
	def run(self, content, flags = 0, location = -1, max_width = 320, max_height = 240,
		on_navigate = None, on_hide = None):
		view = self.window.active_view()
		style_sheet = sublime.load_resource("Packages/User/theme_styles.css")

		html = "<style>%s</style>" % (style_sheet)
		html += content

		view.show_popup(html, flags, location, max_width, max_height, on_navigate, on_hide)

# Command for testing
class StyledTooltipTestCommand(sublime_plugin.WindowCommand):
	def run(self):
		content = "<p class=\"keyword\">Keyword</p>"
		content += "<p class=\"comment line\">This is a comment</p>"
		content += "<p class=\"support function\">Storage Type</p>"
		content += "<p class=\"invalid\">What</p>"

		self.window.run_command("styled_tooltip", {"content": content, "max_width": 600} )

###### Start Color Parser


class ParseSchemeCommand(sublime_plugin.ApplicationCommand):
	css_mapper = {"background": "background-color", "foreground": "color" }
	def run(self):
		global running

		if (running):
			return

		running = True
		scheme_path = sublime.load_settings("Preferences.sublime-settings").get("color_scheme", None)
		scheme = sublime.load_binary_resource(scheme_path)
		plist_dict = readPlistFromBytes(scheme)
		css_dict = self.parse_plist(plist_dict["settings"])

		self.generate_style_sheet(css_dict)
		running = False

	def parse_plist(self, root):
		css_dict = {}
		for node in root:

			if not len(node["settings"]):
				continue

			tmp_dict = {}
			for key in node["settings"]:
				css = self.get_css_name(key)
				if (css == None):
					continue

				tmp_dict[css] = node["settings"][key]


			if not "scope" in node :
				tmp_dict["margin"] = "2px"
				tmp_dict["padding"] = "1em"
				tmp_dict[self.css_mapper["background"]] = ColorHelper().getTintedColor(tmp_dict[self.css_mapper["background"]], 10)
				css_dict["html"] = tmp_dict
			else:
				scope = "." + node["scope"].lower()
				scopes = scope.split(",")
				for i, s in enumerate(scopes):
					if not scopes[i].startswith("."):
						scopes[i] = "."+scopes[i].strip()

					scopes[i] = scopes[i].replace(" ", "_")
					css_dict[ scopes[i] ] = tmp_dict

		return css_dict

	def get_css_name(self, name):
		if name in self.css_mapper:
			return self.css_mapper[name]

		return None

	def generate_style_sheet(self, dict):
		file_content = ""

		for style in dict:
			file_content += style + " {"

			for attrib in dict[style]:
				file_content += attrib + ": " + dict[style][attrib] + ";"

			file_content += "} "

		file_path = sublime.packages_path() + os.sep + "User" + os.sep + "theme_styles.css"
		f = open(file_path, "w")
		f.write(file_content)
		f.close()

class ColorHelper:
	def getTintedColor(self, color, v):
		rgb = self.hex_to_rgb(color)
		mean = self.get_mean(rgb)
		mod = 1 if mean < 128 else -1

		adj = ((256 * (v / 100)) * mod)
		rgb = (rgb[0] + adj, rgb[1] + adj, rgb[2] + adj)
		color = self.rgb_to_hex(rgb)

		return color

	def get_mean(self, rgb):
		tot = 0
		for el in rgb:
			tot += el
		mean = tot/3

		return mean

	def hex_to_rgb(self, color):
		value = color.lstrip("#")
		lv = len(value)
		rgb = tuple(int(value[i:i + lv // 3], 16) for i in range(0,lv,lv //3))

		return rgb

	def rgb_to_hex(self, rgb):
		return "#%02x%02x%02x" % rgb

def plugin_loaded():
	add_listener()
	sublime.run_command("parse_scheme")

def add_listener():
	settings = sublime.load_settings("Preferences.sublime-settings")
	settings.add_on_change("color_scheme", scheme_changed)
	print ("listener added")

def scheme_changed():
	global running

	if (not running):
		sublime.run_command("parse_scheme")

