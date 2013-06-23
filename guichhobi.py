"""The GUI consists of six panels.
-----------------------
|         A           |
-----------------------
|         B           |
-----------------------
|         C     | X| O|
-----------------------
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
C is the path panel that shows the full path the currently selected
D is the comments pane where you can read and edit the photo comments
E is the keywords pane where the keywords are listed (one to a line) and can be edited
F is the EXIF pane where a bunch of read only EXIF data is shown
The X button cancels any changes that have been made
The O button saves changes

If you edit the caption or the keywords (you will know because the field will change color) selecting a different image will have not update the image metadata display untill you cancel or save the changes

Starting the program with the -d option will print debugger messages to the console
"""
import Tkinter as tki, threading, Queue
import libchhobi as lch

def query_finder(q):
  """q is a Queue object."""
  selected_files = set([])
  while True:
    if q.empty():
      new_selected_files = set(lch.get_paths_of_selected())
      if new_selected_files != selected_files:
        selected_files = new_selected_files
        q.put(selected_files)

class App(object):

  def __init__(self):
    self.root = tki.Tk()
    self.root.wm_title('Chhobi2')

    self.setup_window()
    self.setup_finder_polling()

  def setup_window(self):
    self.query_win = tki.Text(self.root, undo=True, width=50, height=3)
    self.query_win['font'] = ('consolas', '12')
    self.query_win.pack(side='top', expand=True, fill='both')
    self.query_win.insert(tki.INSERT,'Hi there')

    self.rawquery_win = tki.Text(self.root, undo=True, width=50, height=2, bg='black', fg='white')
    self.rawquery_win['font'] = ('consolas', '9')
    self.rawquery_win.pack(side='top', expand=True, fill='both')
    self.rawquery_win.insert(tki.INSERT,'Hi there')

    fr = tki.Frame(self.root)
    fr.pack(side='top', expand=True, fill='both')
    self.path_win = tki.Text(fr, undo=True, width=30, height=2, bg='gray')
    self.path_win.pack(side='left', expand=True, fill='both')
    self.button_cancel = tki.Button(fr, text="X", fg="red")
    self.button_cancel.pack(side='left')
    self.button_ok = tki.Button(fr, text="O", fg="red")
    self.button_ok.pack(side='left')

    self.comment_win = tki.Text(self.root, undo=True, width=40, height=3)
    self.comment_win['font'] = ('consolas', '12')
    self.comment_win.pack(expand=True, fill='both')

    fr = tki.Frame(self.root)
    fr.pack(side='top', expand=True, fill='both')
    self.keywords_win = tki.Text(fr, undo=True, width=30, height=10, bg='gray')
    self.keywords_win['font'] = ('consolas', '10')
    self.keywords_win.pack(side='left', expand=True, fill='both')
    self.exif_win = tki.Text(fr, undo=True, width=30, height=2, bg='gray')
    self.exif_win['font'] = ('consolas', '10')
    self.exif_win.pack(side='left', expand=True, fill='both')

  def setup_finder_polling(self):
    self.queue = Queue.Queue(maxsize=1)
    self.poll_interval = 250
    self.poll_thread = threading.Thread(target=query_finder, name='FinderPoller', args=(self.queue,))
    self.poll_thread.start()
    self.start_poll()

  def start_poll(self):
    self._poll_job_id = self.root.after(self.poll_interval, self.poll)

  def stop_poll(self):
    self.root.after_cancel(self._poll_job_id)

  def poll(self):
    if self.queue.qsize():
      self.selected_files = self.queue.get()
      self.path_win.delete(1.0,tki.END)
      self.path_win.insert(tki.END, self.selected_files)
    self._poll_job_id = self.root.after(self.poll_interval, self.poll)

app = App()
app.root.mainloop()