# TEX-NAV Text Editor

- TEX-NAV is a text editor and file navigator built with Python and Tkinter.
- Made for Windows.

## Requirements

- Python 3.x
- Tkinter (usually comes pre-installed with Python)

## Usage

Run the script to set up TEX-NAV:

```
git clone https://github.com/siddhanth78/tex-nav
cd tex-nav
python setup.py
```

TEX-NAV will be installed in your home directory.

To remove TEX-NAV from your system, navigate to your home directory, and delete the TEX-NAV folder and the TEX-NAV desktop shortcut manually.

## Commands

TEX-NAV supports various commands that can be entered in the query bar:

- `:q` - Close the current tab
- `:s` - Save the current file
- `:sq` - Save and close the current file
- `:new filename` - Create a new file
- `:newd dirname` - Create a new directory
- `:del filename` - Delete a file or directory
- `:re oldname -> newname` - Rename a file or directory
- `:copy source -> destination` - Copy a file or directory
- `:move source -> destination` - Move a file or directory
- `:info filename` - Show information about a file or directory
- `:f searchterm` - Find occurrences of a term in the current file
- `:fr` - Open the Find and Replace dialog
- `:fs size` - Change the font size
- `:cmd` - Open a command prompt in the current directory

## Key Shortcuts

- `Ctrl+N` - Text autocompletion
- `Tab` - Indent selected text, insert tab or autofill query
- `Shift+Tab` - Unindent selected text
