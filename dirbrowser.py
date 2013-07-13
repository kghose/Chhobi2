"""A Tk widget that allows us to browse the file system. Based off code presented at
http://stackoverflow.com/questions/14404982/python-gui-tree-walk
By mmgp (http://stackoverflow.com/users/1832154/mmgp)
"""
import os, Tkinter as tki, ttk

class DirBrowse(tki.Frame):
  """The item data consist of fullpath and type.
  The iids are set as the POSIX path and therefore can be used directly.
  The exceptions are:
   * The root of a virtual listing which has a ptype = 'back to root' and
   * Dummy leaves which have not been opened yet (required to show the expanding arrow) which have a
     ptype = 'dummy'
  """
  def __init__(self, parent, dir_root=None, photo_ext=['jpg', 'tiff', 'gif', 'png', 'raw', 'nef'], video_ext = ['avi'], **options):
    tki.Frame.__init__(self, parent)
    self.photo_ext = photo_ext
    self.video_ext = video_ext
    style = ttk.Style()
    style.map("my.Treeview",
      foreground=[('selected', 'yellow'), ('active', 'white')],
      background=[('selected', 'black'), ('active', 'black')]
    )
    self.treeview = ttk.Treeview(self, columns=("fullpath", "type"),show='tree',displaycolumns=(), style='my.Treeview')
    self.treeview.pack(expand=True, fill='both')
    if dir_root is not None: self.set_dir_root(dir_root)
    self.treeview.bind('<<TreeviewOpen>>', self.update_tree)

  def set_initial_focus(self):
    tv = self.treeview
    node = tv.get_children()[0]
    tv.focus(node)
    tv.selection_set(node)

  def set_dir_root(self, startpath):
    map(self.treeview.delete, self.treeview.get_children()) #Delete the original
    self.start_path = startpath
    dfpath = os.path.abspath(startpath)
    node = self.treeview.insert('', 'end', text=dfpath, iid=dfpath,
                           values=[dfpath, "directory"], open=True)
    self.fill_tree(node)
    self.set_initial_focus()

  def file_type(self, p):
    ptype = None
    if os.path.isdir(p):
      ptype = 'directory'
    else: #We are a regular file
      P = p.lower()
      for ext in self.photo_ext:
        if P.endswith(ext):
          ptype = 'file:photo'
          break
      if ptype is None:
        for ext in self.video_ext:
          if P.endswith(ext):
            ptype = 'file:video'
            break
    return ptype

  def fill_tree(self, node):
    if self.treeview.set(node, "type") != 'directory':
      return
    path = self.treeview.set(node, "fullpath")
    self.treeview.delete(*self.treeview.get_children(node)) # Delete the possibly 'dummy' node present.
    for p in os.listdir(path):
      p = os.path.join(path, p)
      ptype = self.file_type(p)
      if ptype is None: continue
      fname = os.path.split(p)[1]
      oid = self.treeview.insert(node, 'end', text=fname, values=[p, ptype], iid=p)
      if ptype == 'directory':
        self.treeview.insert(oid, 0, text='dummy', values=['dummy', 'dummy'])

  def virtual_flat(self, files, title='Virtual listing'):
    # Set the contents to a flat listing of files. Useful for 'virtual' folders we create on the fly
    self.treeview.delete(*self.treeview.get_children())#Delete the original
    ins = self.treeview.insert
    #Special first node, instructs us to go back to the real listing
    ptype = 'title'
    ins('','end', text=title, values=['title', ptype])
    for file in files:
      ptype = self.file_type(file)
      #fname = os.path.split(file)[1]
      ins('','end', text=file, values=[file, ptype], iid=file)
    self.set_initial_focus()

  def update_tree(self, event):
    self.fill_tree(self.treeview.focus())

  def file_selection(self):
    tv = self.treeview
    files = self.treeview.selection()
    return [tv.item(fi)['values'] for fi in files if tv.item(fi)['values'][1][:4]=='file']

  def all_selection(self):
    #from IPython import embed; embed()
    tv = self.treeview
    files = self.treeview.selection()
    return [tv.item(fi)['values'] for fi in files if (tv.item(fi)['values'][1]=='directory') or (tv.item(fi)['values'][1][:4]=='file')] #Only exclude the virtual listing head