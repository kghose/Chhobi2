"""A Tk widget that allows us to browse the file system. Based off code presented at
http://stackoverflow.com/questions/14404982/python-gui-tree-walk
By mmgp (http://stackoverflow.com/users/1832154/mmgp)
"""
import os, sys, Tkinter as tki, ttk

class DirBrowse(tki.Frame):
  def __init__(self, parent, root='./', **options):
    tki.Frame.__init__(self, parent, **options)

    self.treeview = ttk.Treeview(columns=("fullpath", "type"),show='tree',displaycolumns=())
    self.treeview.pack(fill='both', expand=True)
    self.set_root(root)
    self.treeview.bind('<<TreeviewOpen>>', self.update_tree)

  def set_root(self, startpath):
    dfpath = os.path.abspath(startpath)
    node = self.treeview.insert('', 'end', text=dfpath,
                           values=[dfpath, "directory"], open=True)
    self.fill_tree(node)

  def fill_tree(self, node):
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
      oid = self.treeview.insert(node, 'end', text=fname, values=[p, ptype])
      if ptype == 'directory':
        self.treeview.insert(oid, 0, text='dummy')

  def update_tree(self, event):
    self.fill_tree(self.treeview.focus())