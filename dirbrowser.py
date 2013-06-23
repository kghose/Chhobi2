"""A Tk widget that allows us to browse the file system. Based off code presented at
http://stackoverflow.com/questions/14404982/python-gui-tree-walk
By mmgp (http://stackoverflow.com/users/1832154/mmgp)
"""
import os, sys, Tkinter as tki, ttk

class DirBrowse(tki.Frame):
  def __init__(self, parent, dir_root='./', **options):
    tki.Frame.__init__(self, parent, **options)
    self.treeview = ttk.Treeview(columns=("fullpath", "type"),show='tree',displaycolumns=())
    self.treeview.pack(fill='both', expand=True)
    self.set_dir_root(dir_root)
    self.treeview.bind('<<TreeviewOpen>>', self.update_tree)

  def set_dir_root(self, startpath):
    map(self.treeview.delete, self.treeview.get_children()) #Delete the original
    self.start_path = startpath
    dfpath = os.path.abspath(startpath)
    node = self.treeview.insert('', 'end', text=dfpath,
                           values=[dfpath, "directory"], open=True)
    self.fill_tree(node)

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

      fname = os.path.split(p)[1]
      oid = self.treeview.insert(node, 'end', text=fname, values=[p, ptype], iid=p)
      if ptype == 'directory':
        self.treeview.insert(oid, 0, text='dummy')

  def virtual_flat(self, files):
    # Set the contents to a flat listing of files. Useful for 'virtual' folders we create on the fly
    map(self.treeview.delete, self.treeview.get_children()) #Delete the original
    ins = self.treeview.insert
    #Special first node, instructs us to go back to the real listing
    ptype = 'back to root'
    ins('','end', text='Back to real listing', values=['real listing', ptype], iid='real listing')
    ptype = None
    for file in files:
      fname = os.path.split(file)[1]
      ins('','end', text=fname, values=[file, ptype], iid=file)

  def update_tree(self, event):
    self.fill_tree(self.treeview.focus())