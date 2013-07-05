"""The GUI consists of four panels
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
[arrow keys]     - navigate in file browser (even when in command window). Once you start a command
                   your arrow keys work as normal cursor keys in the command window. When in command mode
                   up and down arrow keys step through the history
[right cursor]   - If an image file is selected in file browser, will open the file in a quick view window
r                - Reveal the current files/folders in finder
a                - add selected files to pile
x                - remove selected files from pile (if they exist in pile)
p                - show pile

After typing the following commands you need to hit enter to execute
d <posix path>   - set the root of the file browser to this. Last set is remembered across sessions
c <text>         - set this text as picture caption.
k <keyword>      - add this keyword to the current file/selection
k- <keyword>     - remove this keyword from the current file/selection
s <query string> - perform this mdfinder query and set the file browser to this virtual listing
cp               - clear all images from pile
z WxH            - resize all images in pile to fit within H pixels high and W pixels wide,
                   put them in a temporary directory and reveal the directory
"""
import logging
logger = logging.getLogger(__name__)
import Tkinter as tki, tempfile, argparse, Image, ImageTk, ConfigParser
import libchhobi as lch, dirbrowser as dirb, exiftool
from cStringIO import StringIO
from os.path import join

class App(object):

  def __init__(self):
    self.root = tki.Tk()
    self.root.wm_title('Chhobi2')
    self.load_prefs()
    self.setup_window()
    self.root.wm_protocol("WM_DELETE_WINDOW", self.cleanup_on_exit)
    self.etool = exiftool.PersistentExifTool()
    self.cmd_state = 'Idle'
    self.one_key_cmds = ['r', 'a', 'x', 'p']
    self.command_prefix = ['d', 'c', 'k', 's', 'z']
    #If we are in Idle mode and hit any of these keys we move into a command mode and no longer propagate keystrokes to the browser window
    self.pile = set([]) #We temporarily 'hold' files here
    self.cmd_history = lch.CmdHist(memory=20)

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
    self.dir_win.treeview.bind('<<TreeviewOpen>>', self.open_external, add='+')

    fr = tki.Frame(self.root)
    fr.pack(side='top')#, expand=True, fill='x')

    #A trick to force the thumbnail_label to a particular size
    f = tki.Frame(fr, height=155, width=155, bg='black')
    f.pack_propagate(0) # don't shrink
    f.pack(side='left')
    self.thumbnail_label = tki.Label(f)
    self.thumbnail_label.pack()

    self.info_text = tki.Text(fr, width=40, height=12, fg='white', bg='black', padx=5, pady=5)
    self.info_text['font'] = ('courier', '11')
    self.info_text.pack(side='left', fill='x')

    self.cmd_win = tki.Text(self.root, undo=True, width=50, height=3, fg='black', bg='white')
    self.cmd_win['font'] = ('consolas', '12')
    self.cmd_win.pack(side='top', fill='x')
    self.cmd_win.bind("<Key>", self.cmd_key_trap)

  def cmd_key_trap(self, event):
    chr = event.char
    if self.cmd_state == 'Idle':
      if chr in self.one_key_cmds:
        self.single_key_command_execute(chr)
        return 'break'
      elif chr in self.command_prefix:
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
      elif event.keysym == 'Up' or event.keysym == 'Down':
        self.browse_history(event.keysym)

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
      info_text += 'Caption       :\n{:s}\n'.format(cap_set.pop())
    else:
      info_text += 'Caption       : -\n'
    info_text +=   'Keywords      : '
    if len(key_set):
      info_text += key_set.pop()
      for key in key_set:
        info_text += ',' + key
      info_text += '\n'
    else:
      info_text += '-\n'

    if len(exiv_data) == 1:
      for k,v in exiv_data[0].iteritems(): #in ['Model', 'LensID', 'FocalLength', 'ISO', 'ShutterSpeed', 'FNumber']:
        if k not in ['Caption-Abstract','Keywords', 'SourceFile']:
          info_text += k.ljust(14) + ': ' + str(v) + '\n'
    else:
      info_text += '(Showing common info)'
    return info_text

  def get_thumbnail(self, file):
    im_data = self.etool.get_thumbnail_image(file)
    if len(im_data):
      thumbnail = Image.open(StringIO(im_data))
    else:
      logger.debug('No embedded thumnail for {:s}. Generating on the fly.'.format(file))
      #Slow process of generating thumbnail on the fly
      thumbnail = Image.open(file)
      thumbnail.thumbnail((150,150), Image.ANTIALIAS) #Probably slows us down?
    return ImageTk.PhotoImage(thumbnail)

  def selection_changed(self, event):
    files = self.dir_win.file_selection()
    logger.debug(files)

    if len(files):
      photo = self.get_thumbnail(files[0])
      self.thumbnail_label.config(image=photo)
      self.thumbnail_label.image = photo #Keep a reference

      exiv_data = self.etool.get_metadata_for_files(files)
      info_text = self.formatted_metadata_string(exiv_data)
      self.info_text.delete(1.0, tki.END)
      self.info_text.insert(tki.END, info_text)

  def single_key_command_execute(self, chr):
    if chr == 'r':
      self.reveal_in_finder()
    elif chr == 'a':
      self.add_selected_to_pile()
    elif chr == 'x':
      self.remove_selected_from_pile()
    elif chr == 'p':
      self.show_pile()

  def command_execute(self, event):
    command = self.cmd_win.get(1.0, tki.END)
    files = self.dir_win.file_selection()
    if command[0] == 'd':
      dir_root = command[2:].strip()
      self.config.set('DEFAULT', 'root', dir_root)
      self.set_new_photo_root(dir_root)
    elif command[:2] == 'c ':
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
    elif command[:2] == 'cp':
      self.clear_pile()
    elif command[:2] == 'z ':
      self.resize_and_show(command[2:].strip().lower().split('x'))
    self.cmd_win.delete(1.0, tki.END)
    self.cmd_state = 'Idle'
    self.cmd_history.add(command) #Does not distinguish between valid and invalid commands. Ok?

  def command_cancel(self):
    self.cmd_win.delete(1.0, tki.END)
    self.cmd_state = 'Idle'

  def browse_history(self, keysym):
    partial = self.cmd_win.get(1.0, tki.INSERT)
    insert = self.cmd_win.index(tki.INSERT)
    if keysym == 'Up':
      step = -1
    else:
      step = 1
    suggestion = self.cmd_history.completion(partial, step)
    if suggestion is not '':
      self.cmd_win.delete(1.0, tki.END)
      self.cmd_win.insert(tki.END, suggestion)
      self.cmd_win.mark_set(tki.INSERT, insert)

  def set_new_photo_root(self, new_root):
    self.photo_root = new_root
    self.dir_win.set_dir_root(self.photo_root)

  def search_execute(self, query_str):
    files = lch.execute_query(query_str, root = self.config.get('DEFAULT', 'root'))
    self.dir_win.virtual_flat(files)

  def open_external(self, event):
    files = self.dir_win.file_selection()#Only returns files
    if len(files): lch.quick_look_file(files)

  def reveal_in_finder(self):
    files_folders = self.dir_win.all_selection()#Returns both files and folders
    if len(files_folders): lch.reveal_file_in_finder(files_folders)

  def add_selected_to_pile(self):
    files = self.dir_win.file_selection()#Only returns files
    for f in files:
      self.pile.add(f)

  def remove_selected_from_pile(self):
    files = self.dir_win.file_selection()#Only returns files
    for f in files:
      self.pile.discard(f)

  def clear_pile(self):
    self.pile.clear()

  def show_pile(self):
    self.dir_win.virtual_flat(self.pile, title='Showing Pile. Select this to go back')

  def resize_and_show(self, size):
    size = (int(size[0]), int(size[1]))
    out_dir = tempfile.mkdtemp()
    for n,file in enumerate(self.pile):
      outfile = join(out_dir, '{:06d}.jpg'.format(n))
      im = Image.open(file)
      im.thumbnail(size, Image.ANTIALIAS)
      im.save(outfile, 'JPEG')
    lch.reveal_file_in_finder([out_dir])

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