import tkinter as tk
from engine import WordleEngine
from graphic import WordleUI

def main():

    engine = WordleEngine("words.txt")

    root = tk.Tk()
    app = WordleUI(root, engine)

    root.mainloop()

if __name__ == "__main__":
    main()