"""The GUI consists of six panels.
-----------------------
|         A           |
|---------------------|
|         B           |
|---------------------|
|                     |
|         C           |
|                     |
|---------------------|
|                     |
|         D           |
|                     |
|---------|-----------|
|         |           |
|    E    |     F     |
|         |           |
-----------------------

A is the search panel where you form your query. Hitting enter executes the query
B is the RawQuery window where you can see the RawQuery that will be fed to Spotlight
C is the directory/file list browser
D is the comments pane where you can read and edit the photo comments. Hit <CTRL> + S to save, ESC or navigate away to cancel
E is the keywords pane where the keywords are listed (one to a line) and can be edited. Hit <CTRL> + S to save, ESC or navigate away to cancel
F is the EXIF pane where a bunch of read only EXIF data is shown

Starting the program with the -d option will print debugger messages to the console
"""
import logging
logger = logging.getLogger(__name__)
import Tkinter as tki, threading, Queue, argparse, time
import libchhobi as lch
import dirbrowser as dirb

class App(object):

  def __init__(self):
    self.root = tki.Tk()
    self.root.wm_title('Chhobi2')
    self.setup_window()
    self.root.wm_protocol("WM_DELETE_WINDOW", self.cleanup_on_exit)

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

    self.rawquery_win = tki.Text(self.root, undo=True, width=50, height=2, bg='black', fg='white')
    self.rawquery_win['font'] = ('consolas', '9')
    self.rawquery_win.pack(side='top', expand=True, fill='both')
    self.rawquery_win.insert(tki.INSERT,'Hi there')

    self.dir_win = dirb.DirBrowse(self.root, dir_root='/Users/kghose/Pictures')
    self.dir_win.pack(side='top', expand=True, fill='both')
    self.dir_win.treeview.bind("<<TreeviewSelect>>", self.selection_changed)

    self.comment_win = tki.Text(self.root, undo=True, width=40, height=3)
    self.comment_win['font'] = ('consolas', '12')
    self.comment_win.pack(expand=True, fill='both')

    fr = tki.Frame(self.root)
    fr.pack(side='top', expand=True, fill='both')
    self.keywords_win = tki.Text(fr, undo=True, width=30, height=10)
    self.keywords_win['font'] = ('consolas', '10')
    self.keywords_win.pack(side='left', expand=True, fill='both')
    self.exif_win = tki.Text(fr, undo=True, width=30, height=2, bg='black', fg='white')
    self.exif_win['font'] = ('consolas', '10')
    self.exif_win.pack(side='left', expand=True, fill='both')

  def selection_changed(self, event):
    print self.dir_win.treeview.selection()

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
  logging.basicConfig(level=logging.DEBUG)

  app = App()
  app.root.mainloop()