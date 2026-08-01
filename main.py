"""getmusic -- 图形界面版"""

import tkinter as tk
from gui import GetMusicApp

if __name__ == "__main__":
    root = tk.Tk()
    GetMusicApp(root)
    root.mainloop()