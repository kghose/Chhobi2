"""
I was inspired by https://github.com/smarnach/pyexiftool to look into exiftools -stay_open 1 mode (since my individual calls to exiftool were too slow). I wrote my own verison instead of taking smarnach's version simply because I wanted to understand how things worked, and wanted to make the code simple to fit my simple purposes.

Handling video metadata:
This is a little hacky: Exiftool can only handle reading for video metadata and there is no provision for keywords and
captions. What we do is generate a side car file in the form of a jpeg file that contains the keyword and caption.


Exiftool can handle reading of basic metadata from video files. In this case we simply load a few pieces of metadata from the file itself. However, Exiftool does not allow us to save metadata, like comments and keywords in the file itself. We use a sidecar file for this. We use ffmpeg to generate a thumbnail jpg image. If ffmpeg does not exist we generate a generic icon. We use this jpg as the sidecar file. This module allows us to transparently hook into the sidecar solution.

- Generate video thumbnail/sidecar
ffmpeg -loglevel panic -i /Users/kghose/Pictures/2013/2013-06-29/MVI_0843.AVI -ss 00:00:0 -f image2 -vframes 1 out.jpg
- Copy over video metadata
exiftool -TagsFromFile /Users/kghose/Pictures/2013/2013-06-29/MVI_0843.AVI out.jpg


biplist (https://github.com/wooster/biplist)

http://stackoverflow.com/questions/8530825/mac-os-x-add-a-custom-meta-data-field-to-any-file


"""
import logging
logger = logging.getLogger(__name__)
import os, subprocess, json, libchhobi as lch

class PersistentExifTool(object):
  """A class that simply opens exiftool with the -stay_open 1 flag and sets up communication via stdin."""
  def __init__(self):
    with open(os.devnull, 'w') as devnull:
      self.exiftool_process = subprocess.Popen(
        ['exiftool', '-stay_open', 'True', '-@', '-'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=devnull)
    self.running = True

  def close(self):
    if not self.running:
      return
    input = b'-stay_open\nFalse\n'
    self.exiftool_process.communicate(input)
    self.running = False

  def execute(self, query, expecting_response=True, expecting_binary=False):
    """Query is a list of exiftool commands. We add the -execute in the end."""
    query += '\n-execute\n'
    logger.debug(query)
    self.exiftool_process.stdin.write(query)
    self.exiftool_process.stdin.flush()
    output = b''
    fd = self.exiftool_process.stdout.fileno()
    response_end = b'{ready}'
    while not output[-32:].strip().endswith(response_end):
      output += os.read(fd, 4096)
    if expecting_response:
      if expecting_binary:
        return output.rstrip()[:-len(response_end)]
      else:
        logging.debug(output)
        stripped = output.strip()[:-len(response_end)]
        if len(stripped):
          return json.loads(stripped.decode("utf-8"))
        else:
          return []

  def get_metadata_for_files(self, file_list, side_car_ext = '.chhobi_movie_sidecar'):
    """Get standard metadata from the files. movie_exts are extensions that indicate file is a movie"""
    photo_files = [fi[0] for fi in file_list if fi[1]=='file:photo']
    video_files = [fi[0] for fi in file_list if fi[1]=='file:video']
    exiv_tags = ['-FileType', '-CreateDate', '-model', '-lensid', '-focallength', '-Dof', '-ISO', '-ShutterSpeed', '-fnumber','-Duration', '-Caption-Abstract', '-keywords']
    base_query = '\n'.join(exiv_tags)
    query = '-j\n' #To get JSON back
    for file in photo_files:
      query += file + '\n'
    query += base_query + '\n'
    meta_data = self.execute(query)
    meta_data += lch.read_xattr_metadata(video_files)
    #Singleton keywords need to be converted into a list
    for md in meta_data:
      if md.has_key('Keywords'):
        if not isinstance(md['Keywords'], list):
          md['Keywords'] = [md['Keywords']]
    return meta_data

  def set_metadata_for_files(self, file_list, meta_data):
    """Set selected metadata for the files. If keywords are present they are passed in as a list of tuples
     containing a plus or minus sign indicating if the keyword are to be added or removed and the keyword itself
    """
    photo_files = [fi[0] for fi in file_list if fi[1]=='file:photo']
    video_files = [fi[0] for fi in file_list if fi[1]=='file:video']
    query = '\n'
    for file in photo_files:
      query += file[0] + '\n'
    if meta_data.has_key('caption'):
      query += '-Caption-Abstract={:s}\n\n'.format(meta_data['caption'])
    if meta_data.has_key('keywords'):
      for keyword in meta_data['keywords']:
        query += '-keywords{:s}={:s}\n'.format(keyword[0],keyword[1])
    self.execute(query, expecting_response=False)
    lch.write_xattr_metadata(video_files, meta_data)

  def get_preview_image(self, file):
    """Return a binary string corresponding to the preview image."""
    query = '-PreviewImage\n -b\n'
    query += file + '\n'
    return self.execute(query, expecting_binary=True)

  def get_thumbnail_image(self, file):
    """Return a binary string corresponding to the preview image."""
    query = '-ThumbnailImage\n -b\n'
    query += file + '\n'
    return self.execute(query, expecting_binary=True)