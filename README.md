# StyledPopup
This plugin provides a standardized way to style view popups based on the view's color scheme.

The plugin will parse the active color scheme and generate a style sheet which can be used to style the html displayed in the popup.

The classes generated are based on the scopes available within the color scheme. Since all color schemes are based on common scopes, this provides an ideal method to style html elements.

## Usage

### How to use StyledPopup as a dependencey

The StyledPopup module needs to be installed as a dependency through package control in order to be able to import the new python module. Simply create a `dependencies.json` file within your plugin and add the following content.

```json
{
	"*": {
		"*": [
			"StyledPopup"
		]
	}
}
```

Once the file has been added to your plugin, simply run the ** Package Control: Satisfy Dependencies ** command to tell Package Control to install your dependencies. You could also restart Sublime Text and Package Control should notify you that a new dependency has been install.

Once installed you can simply call the styled popup 

### Calling the Styled Popup.

Import the module using:

```python
import styled_popup
```

Then call the styled_popup.show_popup function passing the view associated with the popup and any arguments to be passed to the view's show_popup function. The html will have the style sheet appended automatically and any css styles that match a given scope will be styled.

```python
styled_popup.show_popup(view, html)
```

### HTML Markup

To style specific elements in the html, simply assign the element a class that matches the scope you would like to use.

```html
<span class="keyword">This should be styled like a keyword</span>
```

Each nested scope selector should be applied as a seperate css class:

```html
<span class="entity name function"> This should be styled similar to a function within the color scheme</span>
```

![alt text](http://huotmedia.com/github/StyledPopup/images/screen_1.png)

The css classes will all be based on the basic supported scopes. 

* string.quoted.double
* entity.name.function
* invalid.illegal
* keyword.control
* storage.type

For a complete list of supported scopes please visit the [Textmate language grammer documentation](https://manual.macromates.com/en/language_grammars)

### Example Command

Create a new python file within the "User" directory of packages. Paste the following code into the new file and save.

```python
import sublime
import sublime_plugin
import styled_popup

class PopupTestCommand(sublime_plugin.WindowCommand):
    def run(self):

        html = """Each <span class="keyword">element</span> within
                  the <span class="entity name class">html</span> can be styled
                  individually using common <span class="string quoted">scope</span> names.
                  Simply wrap each element to be styled in a span and apply the
                  <span class="comment line">css classes</span> for each scope."""

        styled_popup.show_popup(self.window.active_view(), html)
```

Open the Sublime Text Console("ctrl+`") and enter "window.run_command('popup_test')" into the input field at the bottom of the console and press "Enter". You should see a popup window appear which follows the styling for the active view.

## Package Settings

**popup_style_cache_limit**
> An integer setting that controls the number of parsed color scheme to cache.
> *Default:* **5**

## Future Tasks

1. Implement styled code blocks with language based syntax coloring.
