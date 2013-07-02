"""The GUI consists of four panel
-----------------------
|                     |
|         A           |
|                     |
|---------------------|
|         |           |
|    B    |     C     |
|         |           |
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

Esc              - cancel current command
Enter            - execute current command
[arrow keys]     - navigate in file browser (even when in command window). Once you start a command your arrow keys
                   now work as normal cursor keys in the command window, as usual.
d <posix path>   - set the root of the file browser to this. Last set is remembered across sessions
c <text>         - set this text as picture caption.
k <keyword>      - add this keyword to the current file/selection
k- <keyword>     - remove this keyword from the current file/selection
s <query string> - perform this mdfinder query and set the file browser to this virtual listing
a                - add this file to selection
x                - remove this file from selection
v                - toggle virtual listing (selected files)


"""
import logging
logger = logging.getLogger(__name__)
import Tkinter as tki, threading, Queue, argparse, time, Image, ImageTk, ConfigParser
import libchhobi as lch, dirbrowser as dirb, exiftool
from cStringIO import StringIO

class App(object):

  def __init__(self):
    self.root = tki.Tk()
    self.root.wm_title('Chhobi2')
    self.load_prefs()
    self.setup_window()
    self.root.wm_protocol("WM_DELETE_WINDOW", self.cleanup_on_exit)
    self.etool = exiftool.PersistentExifTool()
    self.cmd_state = 'Idle'
    self.command_prefix = ['d', 'c', 'k', 's', 'a', 'x', 'v']
    #If we are in Idle mode and hit any of these keys we move into a command mode and no longer propagate keystrokes
    #to the browser window

  def cleanup_on_exit(self):
    """Needed to shutdown the exiftool and save configuration."""
    self.etool.close()
    with open('chhobi2.cfg', 'wb') as configfile:
      self.config.write(configfile)
    self.root.quit() #Allow the rest of the quit process to continue

  def load_prefs(self):
    self.config_default = {
        'root': './'
    }
    self.config = ConfigParser.ConfigParser(self.config_default)
    self.config.read('chhobi2.cfg')

  def setup_window(self):
    self.dir_win = dirb.DirBrowse(self.root, dir_root=self.config.get('DEFAULT','root'), relief='raised',bd=2)
    self.dir_win.pack(side='top', expand=True, fill='both')
    self.dir_win.treeview.bind("<<TreeviewSelect>>", self.selection_changed, add='+')

    fr = tki.Frame(self.root)
    fr.pack(side='top')#, expand=True, fill='x')

    #A trick to force the thumbnail_label to a particular size
    f = tki.Frame(fr, height=150, width=150, relief='raised',bd=2)
    f.pack_propagate(0) # don't shrink
    f.pack(side='left')
    self.thumbnail_label = tki.Label(f)
    self.thumbnail_label.pack()

    self.info_text = tki.Text(fr, width=40, height=12)
    self.info_text['font'] = ('consolas', '10')
    self.info_text.pack(side='left', fill='x')

    self.cmd_win = tki.Text(self.root, undo=True, width=50, height=3, foreground='black', background='gray')
    self.cmd_win['font'] = ('consolas', '12')
    self.cmd_win.pack(side='top', fill='x')
    self.cmd_win.bind("<Key>", self.cmd_key_trap)

  def cmd_key_trap(self, event):
    chr = event.char
    if self.cmd_state == 'Idle':
      if chr in self.command_prefix:
        self.cmd_state = 'Command'
      else:
        self.propagate_key_to_browser(event)
        return 'break'
    else:
      if event.keysym == 'Return':
        self.command_execute(event)
        return 'break'
      elif event.keysym == 'Escape':
        self.command_cancel()

  def propagate_key_to_browser(self, event):
    """When we are in idle mode we like to mirror some key presses in the command window to the file browser."""
    self.dir_win.treeview.focus_set()
    self.dir_win.treeview.event_generate('<Key>', keycode=event.keycode)
    self.cmd_win.focus_set()

  def formatted_metadata_string(self, exiv_data):
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
    if len(key_set):
      info_text += key_set.pop()
      for key in key_set:
        info_text += ',' + key
      info_text += '\n'
    else:
      info_text += '-\n'

    if len(exiv_data) == 1:
      for k in ['Model', 'LensID', 'FocalLength', 'ISO', 'ShutterSpeed', 'FNumber']:
        info_text += k + ': ' + str(exiv_data[0][k]) + '\n'
    return info_text

  def selection_changed(self, event):
    files = self.dir_win.file_selection()
    logger.debug(files)

    if len(files):
      thumbnail = Image.open(StringIO(self.etool.get_thumbnail_image(files[0])))
      photo = ImageTk.PhotoImage(thumbnail)
      self.thumbnail_label.config(image=photo)
      self.thumbnail_label.image = photo #Keep a reference

      exiv_data = self.etool.get_metadata_for_files(files)
      info_text = self.formatted_metadata_string(exiv_data)
      self.info_text.delete(1.0, tki.END)
      self.info_text.insert(tki.END, info_text)

  def command_execute(self, event):
    command = self.cmd_win.get(1.0, tki.END)
    files = self.dir_win.file_selection()
    if command[0] == 'd':
      dir_root = command[2:].strip()
      self.config.set('DEFAULT', 'root', dir_root)
      self.set_new_photo_root(dir_root)
    elif command[0] == 'c':
      caption = command[2:].strip()
      self.etool.set_metadata_for_files(files, {'caption': caption})
      self.selection_changed(None) #Need to refresh stuff
    elif command[:2] == 'k ':
      keyword = command[2:].strip()
      self.etool.set_metadata_for_files(files, {'keywords': [('+',keyword)]})
      self.selection_changed(None) #Need to refresh stuff
    elif command[:2] == 'k-':
      keyword = command[3:].strip()
      self.etool.set_metadata_for_files(files, {'keywords': [('-',keyword)]})
      self.selection_changed(None) #Need to refresh stuff
    elif command[0] == 's':
      self.search_execute(command[2:].strip())
    self.cmd_win.delete(1.0, tki.END)
    self.cmd_state = 'Idle'

    #from IPython import embed; embed()

  def command_cancel(self):
    self.cmd_win.delete(1.0, tki.END)
    self.cmd_state = 'Idle'

  def set_new_photo_root(self, new_root):
    self.photo_root = new_root
    self.dir_win.set_dir_root(self.photo_root)

  def search_execute(self, query_str):
    files = lch.execute_query(query_str, root = self.config.get('DEFAULT', 'root'))
    self.dir_win.virtual_flat(files)

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