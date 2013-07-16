A minimalist photo organizer for Mac
------------------------------------

![Chhobi screen shot](https://raw.github.com/kghose/Chhobi2/gh-pages/images/screenshot001.png)

## *Because photographers can be geeks too*

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
(With a cameo appearance from [ffmpeg])

[Python]: http://python.org
[Tkinter]: http://docs.python.org/2/library/tkinter.html
[exiftool]: http://www.sno.phy.queensu.ca/~phil/exiftool/exiftool_pod.html
[mdfind]: https://developer.apple.com/library/mac/documentation/Darwin/Reference/ManPages/man1/mdfind.1.html
[PIL]: http://effbot.org/zone/pil-index.htm
[ffmpeg]: http://www.ffmpeg.org/

[Short screen cast](http://youtu.be/99QfEyQB5WQ)

Installation
============
> The nature of this program makes it useful/appealing only to people with some knowledge of programming and using the commandline on macs.  Therefore I have not spent effort in making a nice package with all the dependencies etc. I'm listing the non-standard Python packages that Chhobi uses along with download links. Anybody with a moderate interest in computers should be able to get Chhobi up and running with these instructions. It should also be possible, with a little tweaking, to get this program running on Linux and Windows machines, but I have not tried it.

Non-standard Python dependencies
--------------------------------
1. [PIL](http://stackoverflow.com/questions/9070074/how-to-install-pil-on-mac-os-x-10-7-2-lion) - needed for thumbnail display
2. [xattr](https://pypi.python.org/pypi/xattr) - needed to write video metadata as Mac OS X extended attributes
3. [biplist](https://bitbucket.org/wooster/biplist) - needed to write video metadata as Mac OS X extended attributes

Non-standard command-line tools
-------------------------------
1. [exiftool](http://www.sno.phy.queensu.ca/~phil/exiftool/) - Needed to read and write exiv photo meatadata
2. [ffmpeg](http://www.ffmpeg.org/download.html) - needed to generate display thumbnail for videos.

Installation recipe
-------------------
> You should check for the latest versions of all software

1. Install `exiftool` from the mac os [dmg](http://www.sno.phy.queensu.ca/~phil/exiftool/ExifTool-9.33.dmg)
2. Install `ffmpeg` from the [zip file](http://ffmpegmac.net/resources/SnowLeopard_Lion_Mountain_Lion_13.05.2013.zip)
3. Install PIL
```
curl -O -L http://effbot.org/media/downloads/Imaging-1.1.7.tar.gz
tar -xzf Imaging-1.1.7.tar.gz
cd Imaging-1.1.7
python setup.py install --user
```

4. `pip install xattr --user` - Install xattr
5. `pip install biplist --user` - Install biplist
6. `git clone https://github.com/kghose/Chhobi2.git` - Get Chhobi2

You can now start Chhobi by going into the download directory and typing

`python guichhobi.py`

Click on the command window (the input box with white background) and press 'h' to get the manual.

Manual
======

```
The GUI consists of five panels
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
|---------------------|
|         E           |
-----------------------

A is the directory/file list pane. There are three panes, visible one at a time and switched using the
  keys 1,2,3
   1 - the disk browser,
   2 - search results and
   3 - the pile
B is the thumbnail pane
C is the info pane where you can see the photo comments, keywords
  and a bunch of EXIF data
D is the command line. Hitting enter executes the query
E is the status window, showing messages etc.

Starting the program with the -h option will print this usage manual
Starting the program with the -d option will print debugger messages to the console

Commands:

Esc              - cancel current command
Enter            - execute current command
[arrow keys]     - navigate in file browser (even when in command window). Once you start a command
                   your arrow keys work as normal cursor keys in the command window. When in command mode
                   up and down arrow keys step through the history
[right cursor]   - If an image file is selected in file browser, will open the file in a quick view window
1                - show disk browser window
2                - show search window
3                - update and show pile
r                - Reveal the current files/folders in finder
a                - add selected files to pile
x                - remove selected files from pile (if they exist in pile)
h                - show help

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
Chhobi is made available for download in the hope that it may be of some use. No claim is made that the code works and is free of bugs, but I would appreciate bug reports (iamkaushik.ghose@gmail.com: When you email me **remove the first three letters**)

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

Program details
===============
The captions (exiftool: `Caption-Abstract`) and keywords (exiftool `keywords`) you enter are stored in the standard photo metadata itself. This means that they will show up in Finder, show up in Inspector, show up in spotlight and can be read by any exif compliant tool. They will survive transfers across file systems and operating systems. This is the beauty of standardized metadata. This is all possible because of Phil Harvy's wonderful exiftool command line program and its super awesome interactive mode, which allows you to perform multiple queries without having to call the program repeatedly.

Exiftool, however, does not handle captions and keywords for videos. I do not know if there is a standard for such user defined metadata for videos. I first toyed with the idea of using sidecar files, but this left a very bad taste in my mouth. I finally settled on using extended attributes to save the captions (`com.apple.metadata:kMDItemDescription`), keywords (`com.apple.metadata:kMDItemKeywords`) and even the thumbnail (`chhobi2:thumbnail`). This has the bonus that `mdfind` (and therefore Spotlight) indexes the caption and keywords.

Chhobi stores two pieces of information - your photo root and its geometry - in a simple text configuration file called chhobi2.cfg in your home directory.

Chhobi runs exiftool in safe mode, which means your original images are always kept and captions and keywords are added in a copy of the original.

TODO
====
- ( ) Increase the video types handled
- ( ) Command to force regenerate thumbnail
- (x) Handle video metadata
- ( ) Expand search parsing
- (x) Selections/collections
- (x) Resize and zip collection to send via mail
- ( ) Export queries as smart folders
- (x) (silently generate thumbnail) Indicate when preview thumbnail is not available - autogenerate one
- (x) Command history
- ( ) Commands to change appearance
- (x) Increase status bar time
- (x) Show status when changing browser panes
- ( ) Write how to do searches
- ( ) Fix '=' vs '==' issue

Programming notes and Resources
===============================

Mac OS X writing file metadata
------------------------------
[`xattr -wx com.apple.metadata:kMDItemKeywords <hexdumped plist> File`][macosmetadata]

* you need to use -wx because the data needs to be in binary format
* You need to preface the tag with `com.apple.metadata:` for Spotlight to index it (and for it to showup on Finder info)
* The plist needs to be in [binary format][biplist]
* The [hexdump][binascii] is in the format that `xxd -p` gives which is straight hex and is what is obtained by binascii.b2a_hex(
* Setting a plain text string by doing `xattr -x blah blah` will not work - the xattr will not be recognized by spotlight

[macosmetadata]: http://stackoverflow.com/questions/8530825/mac-os-x-add-a-custom-meta-data-field-to-any-file
[biplist]: https://github.com/wooster/biplist
[binascii]: docs.python.org/2/library/binascii.html

### Batteries included
Interestingly, all this can be done from within Python, without going to the xattr, mdls and other tools for binary plists
You just need the `xattr` and `biplist` modules.

To read keywords you need to do

`biplist.readPlistFromString(xattr.getxattr('TestData/2013-06-29/MVI_0843.AVI', 'com.apple.metadata:kMDItemKeywords'))`

which returns the keywords as a list.

You can set them by doing
```
pl = ['Cat','hat','mat']
xattr.setxattr('TestData/2013-06-29/MVI_0843.AVI', 'com.apple.metadata:kMDItemKeywords', biplist.writePlistToString(pl))
```

Video metadata
--------------
Exif tool can read video metadata but not write it. Chhobi simply writes comments and keywords in extended metadata,
which is also indexed by spotlight, so this nicely solves our problem with video metadata.


Creating Mac OS X bundle
------------------------
py2applet --make-setup ../Chhobi2/guichhobi.py ../Chhobi2/icon_sm.pgm ../Chhobi2/chhobi.icns
python setup.py py2app -e sip,sympy

```
"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

from setuptools import setup

APP = ['../Chhobi2/guichhobi.py']
DATA_FILES = ['../Chhobi2/icon_sm.pgm']
OPTIONS = {'argv_emulation': False,
 'iconfile': '/Users/kghose/Source/Chhobi2/chhobi.icns'}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
```

python setup.py py2app -e sip,pandas,matplotlib,sympy,scipy --matplotlib-backends -

Embedding
---------
gcc -I/Library/Frameworks/Python.framework/Versions/2.7/include/python2.7 -I/Library/Frameworks/Python.framework/Versions/2.7/include/python2.7 -fno-strict-aliasing -fno-common -dynamic -isysroot /Developer/SDKs/MacOSX10.6.sdk -arch i386 -arch x86_64 -g -O2 -DNDEBUG -g -O3 -L/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/config -ldl -framework CoreFoundation -lpython2.7 -u _PyMac_Error Python.framework/Versions/2.7/Python test.c -o testme



Python
------
* When using Popen, do not us PIPE for production sized data. It freezes. Use files instead to read data from process output [pipe1].

[pipe]: http://thraxil.org/users/anders/posts/2008/03/13/Subprocess-Hanging-PIPE-is-your-enemy/

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
