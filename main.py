import tkinter as tk
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from engine.engine import WordleEngine
from ui.graphic import WordleUI

def main():
    data_path = os.path.join(current_dir, "data", "words.txt")
    
    if not os.path.exists(data_path):
        print(f"Warning: {data_path} not found. Please ensure data/words.txt exists.")
        return
    try:
        engine = WordleEngine(data_path)
    except Exception as e:
        print(f"Error loading engine: {e}")
        return

    root = tk.Tk()
    root.eval('tk::PlaceWindow . center')
    
    app = WordleUI(root, engine)

    root.mainloop()

if __name__ == "__main__":
    main()