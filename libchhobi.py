"""
This library contains methods that
a) Translate a more human readable query string into the verbose mdfind RawQuery format
b) Take care of calling Mac OS X components like mdfind to find images, preview to generate previews, thumbnails
c) Create smartfolders based on search criteria
"""

import logging
logger = logging.getLogger(__name__)
from subprocess import Popen, PIPE, list2cmdline
import re, collections, xattr, biplist, os

#The regexp for substituting mdfind syntax into our simplified syntax
#http://docs.python.org/2/library/re.html
query_re = re.compile('(\w*?) *(==|!=|<|>|<=|>=)')

#Maps the human readable query item into a mdfinder item
query_map = {
  'k': 'kMDItemKeywords',    #keywords
  'c': 'kMDItemDescription', #caption
  'd': 'kMDItemContentCreationDate',
  'f': 'kMDItemFNumber',
  't': 'kMDItemExposureTimeSeconds',
  'l': 'kMDItemFocalLength'
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
  return execute_long(cmd_args)

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

def execute_long(prog_args):
  """Don't use PIPE for stdout, use a file. Block
  Needed for queries because PIPE barfs even for small amounts of data
  """
  logger.debug(list2cmdline(prog_args))
  with open('query.txt','w') as stdout:
    p = Popen(prog_args, stdin=PIPE, stdout=stdout, stderr=PIPE)
    if p.wait():
      logger.error(p.stderr.read())
  with open('query.txt','r') as stdout:
    return stdout.read().splitlines()

def quick_look_file(files, mode='-p'):
  #mode can be -t or -p
  Popen(['open'] + files)
  #cmd_args = ['qlmanage', mode] + files
  #return execute(cmd_args, blocking=False)

def reveal_file_in_finder(files=[]):
  Popen(['open', '-R'] + files)

def read_xattr_metadata(file_list):
  """For the given list of files read us the kMDItemDescription and kMDItemKeywords."""
  meta_data = []
  for file in file_list:
    md = {}
    attrs = xattr.listxattr(file)
    if 'com.apple.metadata:kMDItemDescription' in attrs:
      md['Caption-Abstract'] = biplist.readPlistFromString(xattr.getxattr(file, 'com.apple.metadata:kMDItemDescription'))
    if 'com.apple.metadata:kMDItemKeywords' in attrs:
      md['Keywords'] = biplist.readPlistFromString(xattr.getxattr(file, 'com.apple.metadata:kMDItemKeywords'))
    meta_data.append(md)
  return meta_data

def write_xattr_metadata(file_list, meta_data):
  if meta_data.has_key('caption'): #Simple, just replace all the captions
    bipl = biplist.writePlistToString(meta_data['caption'])
    for file in file_list:
      xattr.setxattr(file, 'com.apple.metadata:kMDItemDescription', bipl)

  if meta_data.has_key('keywords'): #A little more involved. For each file, load original keywords,
                                   #then remove or add the relevant keywords
    for file in file_list:
      if 'com.apple.metadata:kMDItemKeywords' in xattr.listxattr(file):
        orig_keywd_list = set(biplist.readPlistFromString(xattr.getxattr(file, 'com.apple.metadata:kMDItemKeywords')))
      else:
        orig_keywd_list = set([])
      for keyword in meta_data['keywords']:
        if keyword[0] == '+': orig_keywd_list.add(keyword[1])
        if keyword[0] == '-': orig_keywd_list.remove(keyword[1])
      xattr.setxattr(file, 'com.apple.metadata:kMDItemKeywords', biplist.writePlistToString(list(orig_keywd_list)))

def get_thumbnail_from_xattr(file, tsize=150):
  """Look for thumbnail in xattr or use ffmpeg to generate one (and store it in xattr).
  ffmpeg command from http://stackoverflow.com/questions/14551102/with-ffmpeg-create-thumbnails-proportional-to-the-videos-ratio
  e.g. ffmpeg -itsoffset -1 -i TestData/2013-06-29/MVI_0843.AVI -vframes 1 -filter:v scale="min(150\, iw):-1"  out.jpg
  Note that list form of Popen takes care of the quoting - nothing special needs to be done.
  """
  if 'chhobi2:thumbnail' in xattr.listxattr(file):
    return xattr.getxattr(file, 'chhobi2:thumbnail')
  ftemp = 'chhobi2_thumb_temp.jpg'
  Popen(['ffmpeg', '-loglevel', 'panic', '-itsoffset', '-1', '-i', file, '-vframes', '1', '-filter:v', 'scale=min({:d}\, iw):-1'.format(tsize), ftemp]).wait() #This takes a finite amount of time
  thumb_data = open(ftemp, 'rb').read()
  os.remove(ftemp) #Clean up after ourselves
  xattr.setxattr(file, 'chhobi2:thumbnail', thumb_data)
  return thumb_data

class CmdHist:
  """A tiny class to implement a crude command history. We keep adding new commands to the deque. Older
   commands are forgotten (the deque has a finite length). When we want to ask for completion we send
   in a 'hint' which is a few characters. We give suggestions matching the hint."""
  def __init__(self, memory=20):
    self.history = collections.deque(maxlen=memory)
    self.partial = None
    self.completions = None
    self.completions_idx = None

  def add(self, cmd):
    cmd = cmd.strip()#Get rid of newlines
    if cmd not in self.history:
      self.history.append(cmd)
    self.partial = None #Need to clear this so we can make the suggestions list afresh
    logger.debug(self.history)

  def completion(self, partial, step):
    """Hint is the partial command we send in for matching, step is +1 or -1 indicating which we way we go
    in the deque."""
    partial = partial.strip()
    logger.debug(partial)
    if self.partial == partial:
      self.completions_idx += step
      if self.completions_idx >= len(self.completions): self.completions_idx = 0
      if self.completions_idx < 0: self.completions_idx = len(self.completions) - 1
    else:
      self.partial = partial
      self.completions = [c for c in self.history if c.startswith(partial)]
      self.completions_idx = len(self.completions) - 1
    if self.completions == []: return ''
    return self.completions[self.completions_idx]

if __name__ == "__main__":
  import sys
  logging.basicConfig(level=logging.DEBUG)
  print sys.argv[1]
  print query_to_rawquery(sys.argv[1])
