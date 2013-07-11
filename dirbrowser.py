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
  def __init__(self, parent, dir_root=None, file_types=['jpg', 'tiff', 'gif', 'png', 'raw', 'nef', 'avi'], **options):
    tki.Frame.__init__(self, parent)
    self.file_types = file_types
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

  def fill_tree(self, node):
    if self.treeview.set(node, "type") != 'directory':
      return
    path = self.treeview.set(node, "fullpath")
    self.treeview.delete(*self.treeview.get_children(node)) # Delete the possibly 'dummy' node present.
    for p in os.listdir(path):
      p = os.path.join(path, p)
      if os.path.isdir(p):
        ptype = 'directory'
      else: #We are a regular file
        P = p.lower()
        this_type = [str for str in self.file_types if P.endswith(str)]
        if len(this_type) == 0: continue
        ptype = 'file'

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
    ptype = 'file'
    for file in files:
      fname = os.path.split(file)[1]
      ins('','end', text=file, values=[file, ptype], iid=file)
    self.set_initial_focus()

  def update_tree(self, event):
    self.fill_tree(self.treeview.focus())

  def file_selection(self):
    tv = self.treeview
    files = self.treeview.selection()
    return [fi for fi in files if tv.item(fi)['values'][1]=='file']  #if os.path.isfile(fi)]

  def all_selection(self):
    #from IPython import embed; embed()
    tv = self.treeview
    files = self.treeview.selection()
    return [fi for fi in files if (tv.item(fi)['values'][1]!='back to root') and (tv.item(fi)['values'][1]!='dummy')] #Only exclude the virtual listing head