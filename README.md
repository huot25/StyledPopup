# StyledTooltip
This plugin provides a standardized way to style tooltips based on the users theme. 

The plugin will parse the users active theme and generate a style sheet which can be used to style the html displayed in the tooltip.

The classes generated are based on the scopes available within the theme. Since all themes are based on specific scopes, this provides a common method to style html elements

## Usage

### HTML Markup

To style specific elements in the html, simply assign the element a class that matches the scope you would like to use. 

    <span class="keyword">This should be styled like a keyword</span>
    <span class="support type"> This should be styled similar to a support type within the theme</span>
    
![alt text](http://huotmedia.com/github/StyledTooltip/images/screen_1.png)
    
### Calling the Styled Tooltip.

I have created a new command that will automatically insert the stylesheet when called. Instead of calling view.show_popup directory, call view.run_command("styled_tooltip", {"content": "Your HTML Content Here"}). 

The new command supports all of the parameters of .show_popup so you can still modify the popup as you see fit.

## Future Tasks

1. Finalize code, clean-up, and commet
2. Implement a way to add styled code blocks with language based syntax coloring.
