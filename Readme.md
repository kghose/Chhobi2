A minimalist photo organizer for Mac
------------------------------------

![Chhobi screen shot](https://raw.github.com/kghose/Chhobi2/gh-pages/images/screenshot001.png)

## `Because photographers can be geeks too`

Features
========
* Simple file browser to flip through images
* Powerful searching via Mac OS X spotlight
* Displays basic EXIF information
* Displays embedded thumbnail (or generates one on the fly)
* Allows you to modify captions and keywords only
* Add photos to a pile and then batch resize and copy, ready for emailing
* Pseudo commandline interface: access all functions with short keystrokes

### Chhobi = [Python] + [Tkinter] + [exiftool] + [mdfind] + [PIL]

[Python]: http://python.org
[Tkinter]: http://docs.python.org/2/library/tkinter.html
[exiftool]: http://www.sno.phy.queensu.ca/~phil/exiftool/exiftool_pod.html
[mdfind]: https://developer.apple.com/library/mac/documentation/Darwin/Reference/ManPages/man1/mdfind.1.html
[PIL]: http://effbot.org/zone/pil-index.htm

[Short screen cast](http://www.youtube.com/watch?v=l20VpopThz0)

Manual
------

```
The GUI consists of four panels
-----------------------
|                     |
|         A           |
|                     |
|---------------------|
|         |           |
|    B    |     C     |
|         |           |
|---------------------|
|         D           |
-----------------------

A is the directory/file list browser
B is the thumbnail pane
C is the info pane where you can see the photo comments, keywords
  and a bunch of EXIF data
D is the command line. Hitting enter executes the query

Starting the program with the -h option will print this usage manual
Starting the program with the -d option will print debugger messages to the console

Commands:

Esc              - cancel current command
Enter            - execute current command
[arrow keys]     - navigate in file browser (even when in command window). Once you start a command
                   your arrow keys work as normal cursor keys in the command window. When in command mode
                   up and down arrow keys step through the history
[right cursor]   - If an image file is selected in file browser, will open the file in a quick view window
r                - Reveal the current files/folders in finder
a                - add selected files to pile
x                - remove selected files from pile (if they exist in pile)
p                - show pile
h                - show help/manual

After typing the following commands you need to hit enter to execute
d <posix path>   - set the root of the file browser to this. Last set is remembered across sessions
c <text>         - set this text as picture caption.
k <keyword>      - add this keyword to the current file/selection
k- <keyword>     - remove this keyword from the current file/selection
s <query string> - perform this mdfinder query and set the file browser to this virtual listing
cp               - clear all images from pile
z WxH            - resize all images in pile to fit within H pixels high and W pixels wide,
                   put them in a temporary directory and reveal the directory

```

The user manual is accessed by running the program with the -h option

    python guichhobi.py -h

or pressing the 'h' key in the command window

Rationale
=========
I think iPhoto is bloated, and any photo organizer concept I could come up with, seemed to unnecessarily duplicate many standard OS functions, such as file organization and metadata searching. Several powerful commandline tools like exiftool, mdfind and convert already exist to manipulate images and image metadata. So I harked back to my Unix days and thought, why not go retro? Why not go back to the GUI as a wrapper around powerful and fast commandline tools? The use of an actual command line to perform all the actions was, of course, not strictly necessary, but if you are going retro, why not go all the way?


License
=======
Chhobi is made available for download in the hope that the programs may be of some use. No claim is made that the code works and is free of bugs, but I would appreciate bug reports (kaushik.ghose@gmail.com)

http://www.gnu.org/licenses/gpl.html

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.



TODO
====
- ( ) Expand search parsing
- (x) Selections/collections
- (x) Resize and zip collection to send via mail
- (x) (Won't do) Export queries as smart folders
- (x) (silently generate thumbnail) Indicate when preview thumbnail is not available - autogenerate one
- (x) Command history
- ( ) Commands to change appearance


Programming notes and Resources
===============================

Tkinter
-------
* A Tkinter app, when launched from the Terminal will not grab focus ([focus stays in Terminal][1])
* Get rid of 'frame' around text box : set `highlightthickness=0`


[1]: http://sourceforge.net/mailarchive/forum.php?thread_name=299cc2dd0909141604t5013feddkd6e82c0120d38c6a%40mail.gmail.com&forum_name=tcl-mac


Mac OS X
--------

RawQuery format:
http://developer.apple.com/library/mac/#documentation/Carbon/Conceptual/SpotlightQuery/Concepts/QueryFormat.html#//apple_ref/doc/uid/TP40001849-CJBEJBHH

Metadata codes:
http://developer.apple.com/library/mac/#documentation/Carbon/Reference/MetadataAttributesRef/Reference/CommonAttrs.html#//apple_ref/doc/uid/TP40001694-SW1


Integrating with finder
-----------------------
My initial idea was to have no GUI elements at all, instead using the finder to select and view the images. In a preliminary version I had a thread that polled the finder for its current selection periodically and used that to drive the interface. This however had a major drawbacks - the applescript (run as a subprocess through oascript) that I used loaded the Finder and the load increased with the size of the selection. The GUI remained responsive since I used a spearate thread for the polling, but my fans started going off and Finder would start consuming CPU when the application was just sitting there. I decided instead to build in a tree view into the application and use Finder for previews only instead.


A note on generating smart folders
----------------------------------

(http://developer.apple.com/library/mac/#documentation/Carbon/Conceptual/SpotlightQuery/Concepts/QueryingMetadata.html#//apple_ref/doc/uid/TP40001848-CJBEJBHH)

Smart Folders are typically created by opening up a finder window and entering a search criterion. The search is very powerful, allowing you to search on very detailed file properties, including (relevant to us) things like f-numbers, shutter speeds, ISOs etc etc. You can also save the search for later access.

When a smart folder is saved as a plist file which has an extension called .savedSearch. Finder is programmed to interpret a .plist file with a .savedSearch extension as a set of commands to list the results of the search.

Saved Searches were probably not meant to be generated programatically - their format is a little obscure. If you load up a saved search you will note that the main business seems to occur in the tags 'RawQuery' and 'RawQueryDict'. 'RawQuery' carries the search string that is passed to mdfind to execute the search and return results. 'RawQueryDict' carries the sub tag ''SearchScopes' which is a list of tags that tell Finder which folders to search within, with 'kMDQueryScopeComputer' refering to the local computer and folders referred to in the usual POSIX notation.

The 'RawQuery' tag under 'RawQueryDict' appears to be cosmetic.

mdimport -X will give a list of tags that the RawQuery (and mdfind) will operate on
mdimport -X 2> attributes.txt (Yes, the output is through stderr, go figure)

[Searchable attributes][http://developer.apple.com/library/mac/#documentation/Carbon/Reference/MetadataAttributesRef/Reference/CommonAttrs.html#//apple_ref/doc/uid/TP40001694-SW1]


Python's [plistlib][plistlib] module offers a very elegant interface to reading and writing plists as Python dictionaries. Chhobi uses a template saved search (created by doing a blank search and saving it) to create a default savedSearch file scaffold. Then the ['RawQuery'] tag and the ['RawQueryDict']['SearchScopes'] are updated with the current search parameters.

[plistlib]: http://docs.python.org/3.4/library/plistlib.html

Icon
----
```python
import Image, base64
im = Image.open('chhobi-icon.png')
imsm = im.resize((150,150))
str = imsm.tostring(encoder_name='raw')
str64 = base64.b64encode(str)
```
