"""
This library contains methods that
a) Translate a more human readable query string into the verbose mdfind RawQuery format
b) Take care of calling Mac OS X components like mdfind to find images, preview to generate previews, thumbnails
c) Create smartfolders based on search criteria
"""

import logging
logger = logging.getLogger(__name__)
from subprocess import Popen, PIPE
import os, plistlib, argparse, re

#The regexp for substituting mdfind syntax into our simplified syntax
#http://docs.python.org/2/library/re.html
query_re = re.compile(r'(\w*?) *(?:==|!=|<|>|<=|>=)(?:\[c\] *|\[d\]| *)')

#Maps the human readable query item into a mdfinder item
query_map = {
  'k': 'kMDItemKeywords',    #keywords
  'c': 'kMDItemDescription' #caption
}

def query_to_rawquery(query):
  """Make substitutions to convert a human readable query into a mdfinder readable query."""
  def _match_sub(match):
    stri = match.group()[0]
    trailing = match.group()[1:]
    return query_map.get(stri, stri)+trailing

  return query_re.sub(_match_sub, query)

def execute_query(query, root = './'):
  raw_query = query_to_rawquery(query)
  cmd_args = ['mdfind', '-onlyin', root, raw_query]
  return execute(cmd_args)

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

def quick_look_file(files, mode='-p'):
  #mode can be -t or -p
  cmd_args = ['qlmanage', mode] + files
  return execute(cmd_args, blocking=False)

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

def reveal_file_in_finder(file_name=''):
  scpt = 'tell application "Finder" to reveal alias (POSIX file "{:s}")'.format(file_name)
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