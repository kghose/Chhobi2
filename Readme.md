Minimal Photo Organizer for Mac. Because photographers can be geeks too.

Chhobi is a pseudo commandline photo organizer for Mac. It allows you to browse your photos and view/change the metadata using just the keyboard. It allows you to search for photos using any metadata that Mac OS indexes.

Chhobi is fashioned after the Unix/Linux GUIs of old that were simply wrappers around powerful commandline tools. The GUI is created using Tkinter, [exiftool][exiftool] is the backend that reads/writes metadata and [mdfind][mdfind] performs the searches.

[exiftool]: http://www.sno.phy.queensu.ca/~phil/exiftool/exiftool_pod.html
[mdfind]: https://developer.apple.com/library/mac/documentation/Darwin/Reference/ManPages/man1/mdfind.1.html

The user manual is accessed by running the program with the -h option

i.e. python guichhobi.py -h

Rationale
=========
I think iPhoto is bloated and any photo organizer concept I could come up with seemed to unnecessarily duplicate many standard OS functions, such as file organization and metadata searching. Several powerful commandline tools like exiftool, mdfind and convert already exist to manipulate images and image metadata. So I harked back to my Unix days and thought, why not go retro? Why not go back to the GUI as a wrapper around powerful and fast commandline tools? The use of an actual command line to perform all the actions was, of course, not strictly necessary, but if you are going retro, why not go all the way?

Features
========
* Simple file browser to flip through images
* Displays basic EXIF information
* Displays embedded thumbnail (or generates one on the fly)
* Allows you to modify captions and keywords only
* Powerful searching via Mac OS X spotlight


TODO
====
* Selections/collections
* Resize and zip collection to send via mail
* Export queries as smart folders
* [DONE, silently generate thumbnail] Indicate when preview thumbnail is not available - autogenerate one
* Command history
* Commands to change appearance


Resources
=========

RawQuery format:
http://developer.apple.com/library/mac/#documentation/Carbon/Conceptual/SpotlightQuery/Concepts/QueryFormat.html#//apple_ref/doc/uid/TP40001849-CJBEJBHH

Metadata codes:

http://developer.apple.com/library/mac/#documentation/Carbon/Reference/MetadataAttributesRef/Reference/CommonAttrs.html#//apple_ref/doc/uid/TP40001694-SW1


Programming notes
=================
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
import Image, base64
im = Image.open('chhobi-icon.png')
imsm = im.resize((150,150))
str = imsm.tostring(encoder_name='raw')
str64 = base64.b64encode(str)
