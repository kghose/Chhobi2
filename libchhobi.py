"""Chhobi is a minimal commandline photo "organizer" written in Python for OS X. It allows
you to search for, select and manipulate the photo metadata of groups of photos.

Chhobi is a bit of a Frankenstein's monster. The main interface is in a minimal command 
line prompt style. Photos are selected and shown via Apple's native Finder which forms the 
GUI part of the program. exiv (metadata) manupulation is done using exiftool

To view or manipulate photo metadata first select the photos in Finder. Then go to the prompt and type a command to operate on the selected photos.

Add keywords 'keyword1' and 'keyword2'  

:k keyword1
:k keyword2

Remove keyword 'keyword3'

:k- keyword3

Replace all keywords with 'keyword1' and 'keyword2'

:k= keyword1
:k keyword2

Set comment (Any leading and trailing whitespace is removed)

:c My comment

For all commands hitting the Escape key will clear the command and return you to the
waiting mode without modifying any data

Basic search

Search for pictures containing 'against light' in keywords and 'sun' in the comment

:s 
:k against light
:c sun
:s  (indicates do search) 

The files display as a list and you can step through them using the cursor keys. 

Refine search to find pictures also containing 'beach' in the comment

:s
:c beach
:s

clear search

:x 

The simple search simply ANDS together multiple search terms. It is possible to do an advanced search as follows:

:a
(
:k keeper
:c beach
)
|
:f > 5.0
:

Again, type :x to clear the search.

By default the advanced search assumes AND and ==. For operators other than this


with | indicating OR




Advanced search. You can do a direct raw query like search as follows

Search for 'sea' and 'beach' in keywords or 'water' in comment

:r
:(k sea && k beach) || (c water)





If you change the image selection while in the middle of a command the command will still
apply to the image selected when you started the command.

The interface layout looks like this:

Current Image: <path to current image>
Current Image metadata:

Current command: (describes what mode you are in, adding keyword, adding comment etc etc)
Text:  ...... (what ever input you are giving to the command, if the command requires 
further input)

RawQuery:  ... online updated raw query text

"""

import logging
logger = logging.getLogger(__name__)
from subprocess import Popen, PIPE
import os, plistlib, argparse


def get_paths_of_selected():
  scpt = """
  set theFiles to ""
  repeat with itemAlias in (get selection of application "Finder")
     set theFiles to theFiles & POSIX path of (itemAlias as text) & return
  end repeat
  theFiles
  """
  p = Popen(['osascript', '-'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
  stdout, stderr = p.communicate(scpt)
  if p.returncode:#Something went wrong
    logger.error(stderr)
  return stdout.split('\r')[:-1] #The last item is simply a new line

def execute(prog_args, blocking=True):
  """If blocking is True, use wait to get result. Otherwise simply return with no error checking etc etc."""
  logger.debug(prog_args)
  p = Popen(prog_args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
  if blocking:
    if p.wait():
      logger.error(p.stderr.read())

    return p.stdout.read().splitlines()

  else: #Non-blocking, return immediately
    return []

def get_metadata(file):
  exiv_tags = ['model', 'lens', 'focal length', 'DOF', 'ISO', 'shutter', '1/f', 'caption', 'keywords']
  exif_args = ['exiftool',  '-forcePrint', '-model', '-lensid', '-focallength', '-Dof', '-ISO', '-ShutterSpeed', '-fnumber', '-Caption-Abstract', '-keywords', file]
  if not os.path.isdir(file):
    return {key: value for key,value in zip(exiv_tags, execute(exif_args))}
  else:
    return None

def set_caption(file, caption):
  #exif_args = ['exiftool', '-overwrite_original', '-P', '-Caption-Abstract={:s}'.format(caption), file]
  exif_args = ['exiftool', '-P', '-Caption-Abstract={:s}'.format(caption), file]
  return execute(exif_args)

def add_keyword(file, keyword):
  exif_args = ['exiftool', '-P', '-keywords+={:s}'.format(keyword), file]
  return execute(exif_args)

def quick_look_file(files, mode='-p'):
  #mode can be -t or -p
  cmd_args = ['qlmanage', mode] + files
  return execute(cmd_args, blocking=False)

def find(raw_query="kMDItemKeywords ==\"against light\"", root='TestData/'):
  """We don't use this. We create smart folders instead."""
  cmd_args = ['mdfind', '-onlyin', root, raw_query]
  return execute(cmd_args)

def load_smart_folder_template(smart_folder_name='chhobi2_saved_search_template.savedSearch'):
  return plistlib.readPlist(smart_folder_name)

def create_smart_folder(pl,raw_query, root='kMDQueryScopeComputer', smart_folder_name='chhobi2.savedSearch'):
  """pl is the template plist."""
  pl['RawQuery'] = raw_query
  pl['RawQueryDict']['RawQuery'] = raw_query #I believe this is cosmetic (does not affect the search)
  pl['RawQueryDict']['SearchScopes'] = [root]
  #If the smart folder exists, we need to delete it, otherwise it won't refresh
  if os.path.exists(smart_folder_name): os.remove(smart_folder_name)
  plistlib.writePlist(pl, smart_folder_name)

def point_to_folder(folder_name='chhobi2.savedSearch'):
  scpt = 'tell application "Finder" to reveal alias (POSIX file "{:s}")'.format(folder_name)
  p = Popen(['osascript', '-'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
  stdout, stderr = p.communicate(scpt)
  if p.returncode:#Something went wrong
    logger.error(stderr)
  return stdout.split('\r')[:-1] #The last item is simply a new line

def query_construction_dictionary():
  """."""


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('-d', default=False, action='store_true', help='Print debugging messages')
  args = parser.parse_args()
  if args.d:
    level=logging.DEBUG
  else:
    level=logging.INFO
  logging.basicConfig(level=logging.DEBUG)

  #paths = get_paths_of_selected()
  #print get_metadata(paths[0])
  #set_caption(paths[0], 'This is a caption')
  #quick_look_file(paths)
  #files = find(raw_query='kMDItemKind == "JPEG image"')
  #quick_look_file(files)

  pl = load_smart_folder_template()
  create_smart_folder(pl, raw_query='(kMDItemKeywords = "keeper") && (kMDItemFNumber > 5.0)')
  point_to_folder()