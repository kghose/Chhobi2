"""
This library contains methods that
a) Translate a more human readable query string into the verbose mdfind RawQuery format
b) Take care of calling Mac OS X components like mdfind to find images, preview to generate previews, thumbnails
c) Create smartfolders based on search criteria
"""

import logging
logger = logging.getLogger(__name__)
from subprocess import Popen, PIPE, list2cmdline
import os, plistlib, argparse, re

#The regexp for substituting mdfind syntax into our simplified syntax
#http://docs.python.org/2/library/re.html
query_re = re.compile('(\w*?) *(==|!=|<|>|<=|>=)')

#Maps the human readable query item into a mdfinder item
query_map = {
  'k': 'kMDItemKeywords',    #keywords
  'c': 'kMDItemDescription', #caption
  'd': 'kMDItemContentCreationDate',
}

def query_to_rawquery(query):
  """Make substitutions to convert a human readable query into a mdfinder readable query."""
  def _match_sub(match):
    tag = match.group(1)
    return query_map.get(tag, tag) + match.group(2)

  return query_re.sub(_match_sub, query)

def execute_query(query, root = './'):
  raw_query = query_to_rawquery(query)
  cmd_args = ['mdfind', '-onlyin', root, raw_query]
  return execute(cmd_args)

def execute(prog_args, blocking=True):
  """If blocking is True, use wait to get result. Otherwise simply return with no error checking etc etc."""
  logger.debug(list2cmdline(prog_args))
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

def reveal_file_in_finder(files=[]):
  Popen(['open', '-R'] + files)

if __name__ == "__main__":
  import sys
  logging.basicConfig(level=logging.DEBUG)
  print sys.argv[1]
  print query_to_rawquery(sys.argv[1])
