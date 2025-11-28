import tkinter as tk
from engine.engine import WordleEngine
from ui.graphic import WordleUI

def main():

    engine = WordleEngine("./data/words.txt")

    root = tk.Tk()
    app = WordleUI(root, engine)

    root.mainloop()

if __name__ == "__main__":
    main()