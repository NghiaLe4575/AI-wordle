import tkinter as tk
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from engine.engine import WordleEngine
from ui.graphic import WordleUI

def main():

    engine = WordleEngine("./data/words.txt")

    root = tk.Tk()
    root.eval('tk::PlaceWindow . center')
    
    app = WordleUI(root, engine)

    root.mainloop()

if __name__ == "__main__":
    main()