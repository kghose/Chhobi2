"""A Tk widget that allows us to browse the file system. Based off code presented at
http://stackoverflow.com/questions/14404982/python-gui-tree-walk
By mmgp (http://stackoverflow.com/users/1832154/mmgp)
"""
import os, sys, Tkinter as tki, ttk

#class DirBrowse(tki.Frame):
class DirBrowse():
  """The item data consist of fullpath and type.
  The iids are set as the POSIX path and therefore can be used directly.
  The exceptions are:
   * The root of a virtual listing which has a ptype = 'back to root' and
   * Dummy leaves which have not been opened yet (required to show the expanding arrow) which have a
     ptype = 'dummy'
  """
  def __init__(self, parent, dir_root='./', **options):
    self.treeview = ttk.Treeview(parent, columns=("fullpath", "type"),show='tree',displaycolumns=())
    self.set_dir_root(dir_root)
    self.treeview.bind('<<TreeviewOpen>>', self.update_tree)

  def pack(self, **options):
    self.treeview.pack(**options)

  def set_auto_open(self, auto_open=False):
    """auto_open means that when we select a single node, if that node has children, we select the first child
    and so on, until we hit a leaf.."""
    if not hasattr(self, 'auto_open'):
      self.auto_open = auto_open
    if self.auto_open:
      self.treeview.bind('<<TreeviewSelect>>', self.auto_expand, add='+')
    else:
      self.treeview.unbind('<<TreeviewSelect>>', self.auto_expand)
    print self.auto_open

  def auto_expand(self, event):
    """We call this when we change selection. If our current item is a leaf node we simply return. If it has children, we select the first child..."""
    self.update_tree(event)
    print 'Boom!'
    tv = self.treeview
    node = tv.focus()
    children = tv.get_children(node)
    if len(children) == 0:
      return
    else:
      tv.focus(children[0])
      tv.selection_set(children[0])


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
    if self.treeview.set(node, "type") == 'back to root': #Special top node for virtual listing
      self.set_dir_root(self.start_path)
      return

    if self.treeview.set(node, "type") != 'directory':
      return

    path = self.treeview.set(node, "fullpath")
    # Delete the possibly 'dummy' node present.
    self.treeview.delete(*self.treeview.get_children(node))

    #parent = self.treeview.parent(node)
    for p in os.listdir(path):
      p = os.path.join(path, p)
      ptype = None
      if os.path.isdir(p):
        ptype = 'directory'
      else: #We are a regular file
        P = p.upper()
        if not P.endswith('JPG') and not P.endswith('TIFF') and not P.endswith('GIF') and not P.endswith('PNG'):
          continue
        ptype = 'file'

      fname = os.path.split(p)[1]
      oid = self.treeview.insert(node, 'end', text=fname, values=[p, ptype], iid=p)
      if ptype == 'directory':
        self.treeview.insert(oid, 0, text='dummy', values=['dummy', 'dummy'])

  def virtual_flat(self, files, title='Back to real listing'):
    # Set the contents to a flat listing of files. Useful for 'virtual' folders we create on the fly
    map(self.treeview.delete, self.treeview.get_children()) #Delete the original
    ins = self.treeview.insert
    #Special first node, instructs us to go back to the real listing
    ptype = 'back to root'
    ins('','end', text=title, values=['real listing', ptype])
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
