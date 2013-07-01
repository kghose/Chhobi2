Minimal Photo Organizer for Mac. Because photographers can be geeks too.

Chhobi is a Frankenstein's monster of Python and native Mac OS X components.




I decided, as an experiment, to come up with a program that organizes photo exif data but does not reinvent the wheel. I decided that the OS already had finder which lets you preview and sort through images. The things missing from the regular OS are

* Changing EXIF data like keywords and captions
* Organizing photos into groups
* Resizing photos


TODO
====
* Export queries as smart folders
* Indicate when preview thumbnail is not available - autogenerate one
* Command history
* Commands to change appearance


Resources
=========

RaqQuery format:
http://developer.apple.com/library/mac/#documentation/Carbon/Conceptual/SpotlightQuery/Concepts/QueryFormat.html#//apple_ref/doc/uid/TP40001849-CJBEJBHH





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
