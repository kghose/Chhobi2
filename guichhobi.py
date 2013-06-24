"""The GUI consists of six panels.
-----------------------
|         A           |
|---------------------|
|                     |
|         B           |
|                     |
|---------------------|
|                     |
|         C           |
|                     |
|---------|-----------|
|         |           |
|    D    |     E     |
|         |           |
-----------------------

A is the search panel where you form your query. Hitting enter executes the query
B is the directory/file list browser
C is the comments pane where you can read and edit the photo comments. Hit <CTRL> + S to save, ESC or navigate away to cancel
D is the keywords pane where the keywords are listed (one to a line) and can be edited. Hit <CTRL> + S to save, ESC or navigate away to cancel
E is the EXIF pane where a bunch of read only EXIF data is shown

Starting the program with the -d option will print debugger messages to the console
"""
import logging
logger = logging.getLogger(__name__)
import Tkinter as tki, threading, Queue, argparse, time
import libchhobi as lch, dirbrowser as dirb, exiftool

class App(object):

  def __init__(self):
    self.root = tki.Tk()
    self.root.wm_title('Chhobi2')
    self.setup_window()
    self.root.wm_protocol("WM_DELETE_WINDOW", self.cleanup_on_exit)
    self.etool = exiftool.PersistentExifTool()

  def cleanup_on_exit(self):
    """Needed to shutdown the polling thread."""
    print 'Window closed. Cleaning up and quitting'
    #self.poll_thread_stop_event.set()
    self.root.quit() #Allow the rest of the quit process to continue

  def setup_window(self):
    self.query_win = tki.Text(self.root, undo=True, width=50, height=3)
    self.query_win['font'] = ('consolas', '12')
    self.query_win.pack(side='top', expand=True, fill='both')
    self.query_win.bind('<Return>', self.search_execute)
    #self.query_win.insert(tki.INSERT,'Hi there')

    self.dir_win = dirb.DirBrowse(self.root, dir_root='./')#'/Users/kghose/Pictures')
    self.dir_win.pack(side='top', expand=True, fill='both')
    self.dir_win.treeview.bind("<<TreeviewSelect>>", self.selection_changed)

    self.caption_text = tki.Text(self.root, undo=True, width=40, height=3)
    self.caption_text['font'] = ('consolas', '12')
    self.caption_text.pack(expand=True, fill='both')

    fr = tki.Frame(self.root)
    fr.pack(side='top', expand=True, fill='both')
    self.keywords_win = tki.Text(fr, undo=True, width=30, height=10)
    self.keywords_win['font'] = ('consolas', '10')
    self.keywords_win.pack(side='left', expand=True, fill='both')
    self.exif_win = tki.Text(fr, undo=True, width=30, height=2, bg='black', fg='white')
    self.exif_win['font'] = ('consolas', '10')
    self.exif_win.pack(side='left', expand=True, fill='both')

  def selection_changed(self, event):
    files = self.dir_win.file_selection()
    logger.debug(files)

    self.caption_text.delete(1.0, tki.END)
    self.keywords_win.delete(1.0, tki.END)
    self.exif_win.delete(1.0,tki.END)

    if len(files):
      exiv_data = self.etool.get_metadata_for_files(files)
      cap_set = set([exiv_data[0].get('Caption-Abstract', '')])
      key_set = set([ky for ky in exiv_data[0].get('Keywords', [])])

      logger.debug(cap_set)
      logger.debug(key_set)

      for n in range(1,len(exiv_data)):
        cap_set &= set([exiv_data[n].get('Caption-Abstract', '')])
        key_set &= set([ky for ky in exiv_data[n].get('Keywords', [])])

      if len(cap_set):
        self.caption_text.insert(tki.END, cap_set.pop())
      for key in key_set:
        self.keywords_win.insert(tki.END, key + '\n')


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