"""The GUI consists of XXX  write we've finalized this stuff
-----------------------
|                     |
|         A           |
|                     |
|---------------------|
|                     |
|         B           |
|                     |
|---------------------|
|                     |
|         C           |
|                     |
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

d <posix path>   - set the root of the file browser to this. Last set is remembered across sessions
n                - go to next entry in file browser
p                - go to previous entry in file browser
>                - if directory, enter. If image, show in preview
<                - go to parent directory
c <text>         - set this text as picture caption. Newline is indicated by \n
k <keyword>      - add this keyword to the current file/selection
k- <keyword>     - remove this keyword from the current file/selection
s <query string> - perform this mdfinder query and set the file browser to this virtual listing
a                - add this file to selection
x                - remove this file from selection
v                - toggle virtual listing (selected files)


"""
import logging
logger = logging.getLogger(__name__)
import Tkinter as tki, threading, Queue, argparse, time, Image, ImageTk
import libchhobi as lch, dirbrowser as dirb, exiftool
from cStringIO import StringIO

class App(object):

  def __init__(self):
    self.root = tki.Tk()
    self.root.wm_title('Chhobi2')
    self.setup_window()
    self.root.wm_protocol("WM_DELETE_WINDOW", self.cleanup_on_exit)
    self.etool = exiftool.PersistentExifTool()

  def cleanup_on_exit(self):
    """Needed to shutdown the exiftool."""
    self.etool.close()
    self.root.quit() #Allow the rest of the quit process to continue

  def setup_window(self):
    self.dir_win = dirb.DirBrowse(self.root, dir_root='./')#'/Users/kghose/Pictures')
    self.dir_win.pack(side='top', expand=True, fill='both')
    self.dir_win.treeview.bind("<<TreeviewSelect>>", self.selection_changed)

    fr = tki.Frame(self.root)
    fr.pack(side='top', expand=True, fill='both')

    self.thumbnail_label = tki.Label(fr)
    self.thumbnail_label.pack(side='left')

    self.info_text = tki.Text(fr, width=40, height=10)
    self.info_text['font'] = ('consolas', '10')
    self.info_text.pack(side='left', expand=True, fill='both')

    self.cmd_win = tki.Text(self.root, undo=True, width=50, height=3)
    self.cmd_win['font'] = ('consolas', '12')
    self.cmd_win.pack(side='top', expand=True, fill='both')
    self.cmd_win.bind('<Return>', self.command_execute)

  def selection_changed(self, event):
    files = self.dir_win.file_selection()
    logger.debug(files)

    if len(files):
      thumbnail = Image.open(StringIO(self.etool.get_preview_image(files[0])))
      photo = ImageTk.PhotoImage(thumbnail)
      self.thumbnail_label.config(image=photo)
      self.thumbnail_label.image = photo #Keep a reference

      exiv_data = self.etool.get_metadata_for_files(files)
      cap_set = set([exiv_data[0].get('Caption-Abstract', '')])
      key_set = set([ky for ky in exiv_data[0].get('Keywords', [])])

      logger.debug(cap_set)
      logger.debug(key_set)

      for n in range(1,len(exiv_data)):
        cap_set &= set([exiv_data[n].get('Caption-Abstract', '')])
        key_set &= set([ky for ky in exiv_data[n].get('Keywords', [])])

      info_text = ''

      if len(cap_set):
        info_text += 'Caption: {:s}\n'.format(cap_set.pop())
      else:
        info_text += 'Caption: -\n'
      info_text += 'Keywords: '
      for key in key_set:
        info_text += key + ','

      self.info_text.delete(1.0, tki.END)
      self.info_text.insert(tki.END, info_text)

    #lch.quick_look_file(files, mode='-p')
    #if len(files) == 1:
    #  lch.reveal_file_in_finder(file_name=files[0])

  def command_execute(self, event):
    """
    dw.selection_set(dw.next(dw.selection()))
    ."""
    self.dir_win.key_command(self.cmd_win.get(1.0, tki.END).strip())
    self.cmd_win.delete(1.0, tki.END)

    #from IPython import embed; embed()



  def search_execute(self, event):
    self.dir_win.virtual_flat([
      '/Users/kghose/Pictures/2011/2011-10-08/DSC_4934.JPG',
      '/Users/kghose/Pictures/2009/2009-09-25/DSC_1808.JPG',
      '/Users/kghose/Pictures/2007/2007-06-14/IMG_5018a.JPG',
    ])

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
  parser.add_argument('-d', default=False, action='store_true', help='Print debugging messages')
  args = parser.parse_args()
  if args.d:
    level=logging.DEBUG
  else:
    level=logging.INFO
  logging.basicConfig(level=level)

  app = App()
  app.root.mainloop()