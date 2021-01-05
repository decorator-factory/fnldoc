# Overview

`fnldoc` is a simple static site generator that uses the FNL markup language.

FNL is a Lisp-like markup language that provides uniform syntax and an extremely
simple extension system, where extensions are libraries instead of middleware.

`fnldoc` accepts a config file and a directory of files to which this config
is pointing. It produces another directory, where it puts the generated files.
That directory can then be used to serve a site, for example, using GitHub pages.


# Example documentation

An example project is included in the github repository. `input/` is the input
directory with the source files, and `fnldoc.json` is the configuration file.

## The input directory

Firstly, the input fnl directory includes the docs themselves:

```
input/
    thing.fnl
    aaa/
        stuff.fnl
        x.fnl
```

It also includes the CSS and JS files to be included:

```
input/
    dummy.css
    dummy.js
```

## The configuration

Let's look at the example documentation.

```javascript
{
    // Path to the input directory, will be used relatively to the current directory
    "input_directory": "input",

    // The page
    "start": "Thing",

    // 'toc' (table of contents) defines the tree structure of the documentation.
    // Each key is the name of the documentation page, and each value is either
    // a path to an FNL file (relative to the input directory) or another TOC
    "toc": {
        "Thing": "thing.fnl",
        "Aaa": {
            "stuff": "aaa/stuff.fnl",
            "In auctor tellus": "aaa/x.fnl"
        },
        "Bbb": {
            "stuff": "aaa/stuff.fnl",
            "In auctor tellus": "aaa/x.fnl"
        }
    },

    // 'output_directory' is where all the generated files will be put,
    // with both the 'serve' and the 'build' modes
    "output_directory": "output",

    // Optional extensions list. Contains pairs of values:
    // ["python.module.name", "name_to_look_up"].
    // python.module.name.name_to_look up must be a dictionary
    // mapping strings to fnl.Entity
    "extensions": [
        ["fnldoc.interpolate", "__extension__"],
        ["fnldoc.md", "__extension__"]
    ],

    // The title that will be
    "title": "Example Title",

    // CSS and JS files to put in the output directory:
    "extra_css": [
        "dummy.css"
    ],
    "extra_js": [
        "dummy.js"
    ]
}
```

# Installation

## Installing for trying out

```sh
pip install -e git+https://github.com/decorator-factory/fnldoc
```

## Including in requirements.txt

```
-e git+https://github.com/decorator-factory/fnldoc#egg=fnldoc
```

## Including in setup.py

```
    install_requires=[
        ...
        "fnldoc@git+https://github.com/decorator-factory/fnldoc#egg=fnldoc",
        ...
    ],
```

## Installing for development

```sh
git clone ssh://git@github.com/decorator-factory/fnldoc
cd fnldoc
python3.8 -m venv env
env/bin/python -m pip install .
```

# Running `fnldoc`

Build the documentation:
```sh
python -m fnldoc build path/to/config.json
```

Serve the documentation at `0.0.0.0:8080`:
```sh
python -m fnldoc serve path/to/config.json
```
