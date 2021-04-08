# Formatter

## What?

Formatter can be used as a 'translator' whenever a service needs to make a call to another service or the outside world.
Imagine a Lamp controlled over MQTT, the MQTT service might not understand how to format the color object given to it on a state change request.
To solve this you can add either a provided formatter, like 'core.color_to_str', or write your own and add it to the device config.

## Writing Formatter:

Formatter are written as python functions, which take an input, transform it, and return the new payload.
In the formatter for our color example might be implemented like this:
````python
def color_to_string(color):
    return f'{color.r};{color.g};{color.b}'
````

You can add the option to configure your formatter by adding arguments which will then be matched with the user config.

````python
def color_to_string(color, delimiter):
    return f'{color.r}{delimiter}{color.g}{delimiter}{color.b}'
````

## Using Formatter
