"""The GUI consists of five panels
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
|---------------------|
|         E           |
-----------------------

A is the directory/file list pane. There are three panes, visible one at a time and switched using the
  keys 1,2,3
   1 - the disk browser,
   2 - search results and
   3 - the pile
B is the thumbnail pane
C is the info pane where you can see the photo comments, keywords
  and a bunch of EXIF data
D is the command line. Hitting enter executes the query
E is the status window, showing messages etc.

Starting the program with the -h option will print this usage manual
Starting the program with the -d option will print debugger messages to the console

Commands:

Esc              - cancel current command
Enter            - execute current command
[arrow keys]     - navigate in file browser (even when in command window). Once you start a command
                   your arrow keys work as normal cursor keys in the command window. When in command mode
                   up and down arrow keys step through the history
[right cursor]   - If an image file is selected in file browser, will open the file in a quick view window
1                - show disk browser window
2                - show search window
3                - update and show pile
r                - Reveal the current files/folders in finder
a                - add selected files to pile
x                - remove selected files from pile (if they exist in pile)
p                - open preview window
[                - rotate image CCW (left)
]                - rotate image CW (right)
h                - show help

After typing the following commands you need to hit enter to execute
d <posix path>   - set the root of the file browser to this. Last set is remembered across sessions
c <text>         - set this text as picture caption.
k <keyword>      - add this keyword to the current file/selection
k- <keyword>     - remove this keyword from the current file/selection
s <query string> - perform this mdfinder query and set the file browser to this virtual listing
cp               - clear all images from pile
z WxH            - resize all images in pile to fit within H pixels high and W pixels wide,
                   put them in a temporary directory and reveal the directory
u key <string>   - Set the api_key
                   If you change the api_key or api_secret, you need to authorize again
u secret <string>- Set the api_secret
u auth           - authorize Flickr to give Chhobi permissions to upload photos
                   This will only work if the api_key and secret is set
                   This will open a browser window to the page where Flickr will as for your authorization
                   After you authorize Flickr you will receive a code.
u code <code>    - enter the code you get after enabling authorization.
                   This allows Chhobi to get tokens and a secret that will let Chhobi upload photos to your account.
u                - upload currently selected file(s) in the disk browser window
u p              - upload all files in the pile

Search query syntax:
Chhobi's search is a very thin layer on top of mdfind. The syntax for mdfind is found at

http://developer.apple.com/library/mac/#documentation/Carbon/Conceptual/SpotlightQuery/Concepts/QueryFormat.html#//apple_ref/doc/uid/TP40001849-CJBEJBHH

Chhobi gives you several shortcuts to the rather long mdfind names relevant to searching through your photos/movies

  k -> keywords (kMDItemKeywords)
  c -> caption (kMDItemDescription)
  d -> photo date (kMDItemContentCreationDate)
  f -> f-stop (kMDItemFNumber)
  t -> exposure time (kMDItemExposureTimeSeconds)
  l -> focal length (kMDItemFocalLength)

Some examples of searches are

s k='rose'  -> find photos with the keyword rose
s c='*fireworks*'  -> find photos with fireworks in the caption anywhere

Authorizing Flickr to give Chhobi write access:

1. First you need to set the api_key and api_secret for the application. I do have this combination registered for Chhobi
and you are welcome to use the pair by emailing me a request for them.
Alternatively, you can go on Flickr and request an App key/secret pair yourself and use those from Chhobi.

2. Set the api key and secret by typing in
u key <api key>
u secret <secret>

3. Tell Chhobi to ask for authentication
u auth

This will open up a browser window and take you to Flickr's authentication page. Say yes to giving permission to
Chhobi. Copy the code Flicker gives you in the black box.

4. Enter the authentication code you just got
u code <code>

Now the credentials for Chhobi writing to you account are set. These credentials are stored, in plain text, in the
chhobi configuration file in your home directory.

"""
import logging
logger = logging.getLogger(__name__)
import Tkinter as tki, tempfile, argparse, ConfigParser
from PIL import Image, ImageTk
import libchhobi as lch, dirbrowser as dirb, libflickr, exiftool
from cStringIO import StringIO
from os.path import join, expanduser

def resize_image(img, size, orientation):
  """The transpose is a fairly cheap operation, so we don't bother to resize before we transpose."""
  if orientation == 3: img = img.transpose(Image.ROTATE_180)
  elif orientation == 6: img = img.transpose(Image.ROTATE_270)
  elif orientation == 8: img = img.transpose(Image.ROTATE_90)
  img.thumbnail(size, Image.ANTIALIAS)
  return img

class MultiPanel():
  """We want to setup a pseudo tabbed widget with three treeviews. One showing the disk, one the pile and
  the third the search results. All three treeviews should be hooked up to exactly the same event handlers
  but only one of them should be visible at any time.
  Based off http://code.activestate.com/recipes/188537/
  """
  def __init__(self, parent):
    #This is the frame that we display
    self.fr = tki.Frame(parent, bg='black')
    self.fr.pack(side='top', expand=True, fill='both')
    self.widget_list = []
    self.active_widget = None #Is an integer

  def __call__(self):
    """This returns a reference to the frame, which can be used as a parent for the widgets you push in."""
    return self.fr

  def add_widget(self, wd):
    if wd not in self.widget_list:
      self.widget_list.append(wd)
    if self.active_widget is None:
      self.set_active_widget(0)
    return len(self.widget_list) - 1 #Return the index of this widget

  def set_active_widget(self, wdn):
    if wdn >= len(self.widget_list) or wdn < 0:
      logger.error('Widget index out of range')
      return
    if self.widget_list[wdn] == self.active_widget: return
    if self.active_widget is not None: self.active_widget.forget()
    self.widget_list[wdn].pack(fill='both', expand=True)
    self.active_widget = self.widget_list[wdn]

class App(object):

  def __init__(self):
    self.root = tki.Tk()
    self.root.wm_title('Chhobi2')
    self.load_prefs()
    self.init_vars()
    self.setup_window()
    self.etool = exiftool.PersistentExifTool()
    self.setup_uploader()
    self.tab.widget_list[0].set_dir_root(self.config.get('DEFAULT','root'))

  def cleanup_on_exit(self):
    """Needed to shutdown the exiftool and save configuration."""
    self.etool.close()
    if self.showing_preview: self.hide_photo_preview_pane() #This will close the preview pane cleanly (saving geom etc.)
    self.config.set('DEFAULT', 'geometry', self.root.geometry())
    with open(self.config_fname, 'wb') as configfile:
      self.config.write(configfile)
    self.root.quit() #Allow the rest of the quit process to continue

  def load_prefs(self):
    self.config_fname = expanduser('~/chhobi2.cfg')
    self.config_default = {
        'root': './',
        'geometry': 'none',
        'preview geometry': 'none',
        'preview delay': '250',
        'apikey': 'none',
        'apisecret': 'none',
        'oauthtoken': 'none',
        'oauthtokensecret': 'none'
    }
    self.config = ConfigParser.ConfigParser(self.config_default)
    self.config.read(self.config_fname)

  def init_vars(self):
    self.cmd_state = 'Idle'
    self.one_key_cmds = ['1', '2', '3', 'r', 'a', 'x', 'h', 'p', '[', ']']
    self.command_prefix = ['d', 'c', 'k', 's', 'z', 'u']
    #If we are in Idle mode and hit any of these keys we move into a command mode and no longer propagate keystrokes to the browser window
    self.pile = set([]) #We temporarily 'hold' files here
    self.cmd_history = lch.CmdHist(memory=20)
    self.showing_preview = False #If true, will update the preview image periodically
    self.preview_delay = self.config.getint('DEFAULT', 'preview delay')

  def setup_uploader(self):
    nf = lambda str: str if str != 'none' else None
    api_key = nf(self.config.get('DEFAULT', 'apikey'))
    api_secret = nf(self.config.get('DEFAULT', 'apisecret'))
    oauth_token = nf(self.config.get('DEFAULT', 'oauthtoken'))
    oauth_token_secret = nf(self.config.get('DEFAULT', 'oauthtokensecret'))
    self.fup = libflickr.Fup(api_key=api_key, api_secret=api_secret,
                             oauth_token=oauth_token, oauth_token_secret=oauth_token_secret,
                             headers={'User-agent': 'Chhobi'})

  def setup_window(self):
    def add_dir_browse(parent):
      dir_win = dirb.DirBrowse(parent, bd=0)
      #dir_win.pack(side='top', expand=True, fill='both')
      dir_win.treeview.bind("<<TreeviewSelect>>", self.selection_changed, add='+')
      dir_win.treeview.bind('<<TreeviewOpen>>', self.open_external, add='+')
      return dir_win

    self.tab = MultiPanel(self.root)
    for n in [0,1,2]:
      self.tab.add_widget(add_dir_browse(self.tab()))

    fr = tki.Frame(self.root, bg='black')
    fr.pack(side='top', fill='x')

    #A trick to force the thumbnail_label to a particular size
    f = tki.Frame(fr, height=150, width=150)
    f.pack_propagate(0) # don't shrink
    f.pack(side='left')
    self.thumbnail_label = tki.Label(f, bg='black')
    self.thumbnail_label.pack(fill='both', expand=True)
    self.setup_info_text(fr)

    self.cmd_win = tki.Text(self.root, undo=True, width=50, height=3, fg='black', bg='white')
    self.cmd_win['font'] = ('consolas', '12')
    self.cmd_win.pack(side='top', fill='x')
    self.cmd_win.bind("<Key>", self.cmd_key_trap)

    self.log_win = tki.Text(self.root, width=50, height=1, fg='yellow', bg='black', font=('arial', '10'), highlightthickness=0)
    self.log_win.pack(side='top', fill='x')

    self.chhobi_icon = tki.PhotoImage(file="icon_sm.pgm") #This is the photo we show for blank

    geom=self.config.get('DEFAULT', 'geometry')
    if geom != 'none':
      self.root.geometry(geom)

    self.root.wm_protocol("WM_DELETE_WINDOW", self.cleanup_on_exit)


  def setup_info_text(self, fr):
    """Info window set up is a little complicated."""
    self.info_text = tki.Text(fr, width=40, height=12, fg='white', bg='black', padx=5, pady=5, highlightthickness=0)#highlightthickness removes the border so we get a cool uniform black band
    self.info_text['font'] = ('courier', '11')
    self.info_text.pack(side='left', fill='x', expand=True)
    self.info_text.tag_configure('caption', font='helvetica 11 bold', relief='raised')
    self.info_text.tag_configure('keywords', font='helvetica 11 italic')


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
    dir_win = self.tab.active_widget
    dir_win.treeview.focus_set()
    dir_win.treeview.event_generate('<Key>', keycode=event.keycode)
    self.cmd_win.focus_set()

  def get_thumbnail(self, finfo, orientation):
    if finfo[1]=='file:photo':
      im_data = self.etool.get_thumbnail_image(finfo[0])
      if len(im_data):
        thumbnail = Image.open(StringIO(im_data))
      else:
        logger.debug('No embedded thumnail for {:s}. Generating on the fly.'.format(finfo[0]))
        #Slow process of generating thumbnail on the fly
        if finfo[1]=='file:video': return self.chhobi_icon
        thumbnail = Image.open(finfo[0])
      thumbnail = resize_image(thumbnail, (150, 150), orientation)
      #thumbnail.thumbnail((150,150), Image.ANTIALIAS) #Probably slows us down?
      #thumbnail = orient_image(thumbnail, orientation)
    else:
      thumbnail = Image.open(StringIO(lch.get_thumbnail_from_xattr(finfo[0])))
    return ImageTk.PhotoImage(thumbnail)

  def selection_changed(self, event=None):
    files = self.tab.active_widget.file_selection()
    logger.debug(files)
    if len(files):
      exiv_data = self.etool.get_metadata_for_files(files)
      self.display_exiv_info(exiv_data)
      orn = exiv_data[0].get('Orientation',None)
      photo = self.get_thumbnail(files[0], orn)
      self.thumbnail_label.config(image=photo)
      self.thumbnail_label.image = photo #Keep a reference
      if self.showing_preview:
        if hasattr(self,'showing_after_id'):
          self.root.after_cancel(self.showing_after_id)
        self.showing_after_id = self.root.after(self.preview_delay, self.update_photo_preview, files[0], orn)
    else:
      self.info_text.delete(1.0, tki.END)
      self.thumbnail_label.config(image=self.chhobi_icon)

  def display_exiv_info(self, exiv_data):
    cap_set = set([exiv_data[0].get('Caption-Abstract', '')])
    key_set = set([ky for ky in exiv_data[0].get('Keywords', [])])
    for n in range(1,len(exiv_data)):
      cap_set &= set([exiv_data[n].get('Caption-Abstract', '')])
      key_set &= set([ky for ky in exiv_data[n].get('Keywords', [])])

    self.info_text.delete(1.0, tki.END)
    if len(cap_set):
      self.info_text.insert(tki.END, cap_set.pop(), ('caption',))
    info_text = '\n'
    if len(key_set):
      info_text += key_set.pop()
      for key in key_set:
        info_text += ', ' + key
      info_text += '\n'
    self.info_text.insert(tki.END, info_text, ('keywords',))

    info_text = '\n'
    if len(exiv_data) == 1:
      for k in ['CreateDate', 'FNumber', 'ShutterSpeed', 'ISO', 'FocalLength', 'DOF','LensID','Model']:
        if exiv_data[0].has_key(k):
          info_text += k.ljust(14) + ': ' + str(exiv_data[0][k]) + '\n'
    else:
      info_text += '(Showing common info)'
    self.info_text.insert(tki.END, info_text)

  def single_key_command_execute(self, chr):
    if chr == '1':
      self.show_browser()
    elif chr =='2':
      self.show_search()
    elif chr == '3':
      self.show_pile()
    elif chr == 'r':
      self.reveal_in_finder()
    elif chr == 'a':
      self.add_selected_to_pile()
    elif chr == 'x':
      self.remove_selected_from_pile()
    elif chr == 'p':
      self.show_photo_preview_pane()
    elif chr == '[':
      self.rotate_selection(dir='ccw')
    elif chr == ']':
      self.rotate_selection(dir='cw')
    elif chr == 'h':
      self.show_help()

  def command_execute(self, event):
    command = self.cmd_win.get(1.0, tki.END)
    files = self.tab.active_widget.file_selection()
    if command[0] == 'd':
      dir_root = command[2:].strip()
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
    elif command[:1] == 'u':
      self.uploader(command[1:].strip())

    self.cmd_win.delete(1.0, tki.END)
    self.cmd_state = 'Idle'
    self.cmd_history.add(command) #Does not distinguish between valid and invalid commands. Ok?

  def log_command(self, cmd):
    if hasattr(self, 'log_win_after_id'):
      self.log_win.after_cancel(self.log_win_after_id)
    self.log_win.insert(tki.END, '|' + cmd)
    self.log_win_after_id = self.log_win.after(2000, self.clear_log_command)

  def clear_log_command(self):
    self.log_win.delete(1.0, tki.END)

  def command_cancel(self):
    self.cmd_win.delete(1.0, tki.END)
    self.cmd_state = 'Idle'
    self.log_command('Command canceled.')

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
    self.config.set('DEFAULT', 'root', new_root)
    self.tab.widget_list[0].set_dir_root(new_root) #0 is the disk browser

  def search_execute(self, query_str):
    self.log_command('Searching for {:s}'.format(lch.query_to_rawquery(query_str)))
    files = lch.execute_query(query_str, root = self.config.get('DEFAULT', 'root'))
    self.tab.widget_list[1].virtual_flat(files, title='Search result') #1 is the search window
    self.show_search()
    self.log_command('Found {:d} files.'.format(len(files)))

  def open_external(self, event):
    files = self.tab.active_widget.file_selection()#Only returns files
    if len(files): lch.quick_look_file([fi[0] for fi in files])

  def reveal_in_finder(self):
    files_folders = self.tab.active_widget.all_selection()#Returns both files and folders
    if len(files_folders): lch.reveal_file_in_finder([fi[0] for fi in files_folders])

  def add_selected_to_pile(self):
    files = self.tab.active_widget.file_selection()#Only returns files
    l0 = len(self.pile)
    for f in files:
      self.pile.add(f[0])
    l1 = len(self.pile)
    self.log_command('Added {:d} files to pile.'.format(l1-l0))

  def remove_selected_from_pile(self):
    files = self.tab.active_widget.file_selection()#Only returns files
    l0 = len(self.pile)
    for f in files:
      self.pile.discard(f[0])
    l1 = len(self.pile)
    self.log_command('Removed {:d} files from pile.'.format(l0-l1))

  def clear_pile(self):
    self.pile.clear()
    self.log_command('Pile cleared')

  def show_pile(self):
    self.tab.widget_list[2].virtual_flat(self.pile, title='Showing pile.')
    self.tab.set_active_widget(2)
    self.selection_changed()
    self.log_command('Picture pile')

  def show_browser(self):
    self.tab.set_active_widget(0)
    self.selection_changed()
    self.log_command('File browser')

  def show_search(self):
    self.tab.set_active_widget(1)
    self.selection_changed()
    self.log_command('Search results')

  def resize_and_show(self, size):
    size = (int(size[0]), int(size[1]))
    out_dir = tempfile.mkdtemp()
    for n,file in enumerate(self.pile):
      outfile = join(out_dir, '{:06d}.jpg'.format(n))
      im = Image.open(file)
      im.thumbnail(size, Image.ANTIALIAS)
      im.save(outfile, 'JPEG')
    lch.reveal_file_in_finder([out_dir])

  def show_photo_preview_pane(self):
    if self.showing_preview: return
    self.showing_preview = True
    self.preview_pane = tki.Toplevel()
    self.preview_pane.title('Photo preview')
    fr = tki.Frame(self.preview_pane, bg='black')
    fr.pack(fill='both', expand=True)
    self.preview_label = tki.Label(fr, bg='black')
    self.preview_label.pack(fill='both', expand=True)
    self.preview_pane.wm_protocol("WM_DELETE_WINDOW", self.hide_photo_preview_pane)
    geom=self.config.get('DEFAULT', 'preview geometry')
    if geom == 'none': geom = '500x500+20+20'
    self.preview_pane.geometry(geom)
    self.preview_pane.update_idletasks()
    #Otherwise the geometry does not get set and our first image is wrong size (0) when we call update_photo_preview

    files = self.tab.active_widget.file_selection()
    if len(files) > 0:
      exiv_data = self.etool.get_metadata_for_files([files[0]])
      orn = exiv_data[0].get('Orientation',None)
      self.update_photo_preview(files[0], orn)

    self.cmd_win.focus_force() #Want to keep focus in command window

  def hide_photo_preview_pane(self):
    if hasattr(self,'showing_after_id'):
      self.root.after_cancel(self.showing_after_id)
    self.showing_preview = False
    self.config.set('DEFAULT', 'preview geometry', self.preview_pane.geometry())
    self.preview_pane.destroy()

  def update_photo_preview(self, finfo, orientation):
    if finfo[1]=='file:video': return
    size = [int(x) for x in self.preview_pane.geometry().split('+')[0].split('x')]
    photo_preview = ImageTk.PhotoImage(resize_image(Image.open(finfo[0]), size, orientation))
    self.preview_label.config(image=photo_preview)
    self.preview_label.image = photo_preview #Keep a reference

  def rotate_selection(self, dir):
    files = self.tab.active_widget.file_selection()
    self.etool.rotate_images(files, dir)
    self.selection_changed()

  def uploader(self, command):
    """
    u key <string>   - Set the api_key
                   If you change the api_key or api_secret, you need to authorize again
    u secret <string>- Set the api_secret
    u auth           - authorize Flickr to give Chhobi permissions to upload photos
                       This will only work if the api_key and secret is set
                       This will open a browser window to the page where Flickr will as for your authorization
                       After you authorize Flickr you will receive a code.
    u code <code>    - enter the code you get after enabling authorization.
                       This allows Chhobi to get tokens and a secret that will let Chhobi upload photos to your account.
    u                - upload currently selected file(s) in the disk browser window
    u p              - upload all files in the pile
    """
    if command == '':
      self.fup.upload_files([f[0] for f in self.tab.widget_list[0].file_selection()],self.log_command)#Only returns files
    elif command == 'p':
      self.fup.upload_files(self.pile, self.log_command)
    elif command[:3] == 'key':
      self.fup.set_state(api_key = command[3:].strip())
      self.config.set('DEFAULT','apikey', self.fup.api_key)
      self.log_command('Set api key')
    elif command[:6] == 'secret':
      self.fup.set_state(api_secret = command[6:].strip())
      self.config.set('DEFAULT','apisecret', self.fup.api_secret)
      self.log_command('Set api secret')
    elif command[:4] == 'auth':
      self.fup.setup_authorization()
      self.log_command('Asking for authorization')
    elif command[:4] == 'code':
      self.fup.authorize(command[4:].strip())
      self.config.set('DEFAULT','oauthtoken', self.fup.oauth_token)
      self.config.set('DEFAULT','oauthtokensecret', self.fup.oauth_token_secret)
      self.log_command('Authorized')

  def show_help(self):
    top = tki.Toplevel()
    top.title("Help")
    msg = tki.Text(top, font=('consolas', 11), wrap=tki.WORD)
    msg.insert(tki.END, __doc__)
    msg.pack()
    self.log_command('Showing help')

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
  parser.add_argument('-d', default=False, action='store_true', help='Print debugging messages')
  args,_ = parser.parse_known_args()
  if args.d:
    level=logging.DEBUG
  else:
    level=logging.INFO
  logging.basicConfig(level=level)

  app = App()
  app.root.mainloop()