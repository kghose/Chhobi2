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
    node = self.treeview.insert('', 'end', text=dfpath, iid=dfpath,
                           values=[dfpath, "directory"], open=True)
    self.fill_tree(node)
    tv = self.treeview
    tv.selection_set(tv.get_children()[0])

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
      ins('','end', text=file, values=[file, ptype], iid=file)

  def update_tree(self, event):
    self.fill_tree(self.treeview.focus())

  def file_selection(self):
    files = self.treeview.selection()
    return [fi for fi in files if os.path.isfile(fi)]

  def key_command(self, cmd):
    print cmd
    response = 'ok'
    tv = self.treeview
    sel = tv.selection()
    if sel == '': #Nothing selected, first thing to do is select something and return
      tv.selection_set(tv.get_children()[0])
      return response

    if cmd =='n':
      next = tv.next(tv.selection())
      if next == '':#End of leaves OR nothing slected
        next = tv.parent(tv.selection())
        if next == '': #End of tree even at root level
          next = tv.get_children()[0] #Loop to the topmost one
        else:
          next = tv.next(next)
      tv.selection_set(next)
    elif cmd =='p':
      prev = tv.prev(tv.selection())
      if prev == '':#End of leaves
        prev = tv.parent(tv.selection())
        if prev == '': #End of tree even at root level
          prev = tv.get_children()[-1] #Loop to the last one
      tv.selection_set(prev)
    elif cmd == '.': #Try and get to leaves
      tv.focus(tv.selection())
      self.update_tree(None)
      next = tv.get_children(tv.selection())
      if next == '': #Leaf node
        response = 'leaf'
      else:
        tv.selection_set(next[0])
    elif cmd == ',': #Try and get to parent
      next = tv.parent(tv.selection())
      if next == '': #Parent node
        tv.selection_set(tv.get_children()[0]) #Loop to the topmost one
      else:
        tv.selection_set(next)
    tv.see(tv.selection()) #Make sure we can see this
    return response #Right now will usually return 'ok' will return 'leaf' for '.' and leaf node