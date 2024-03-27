import matplotlib.pyplot as plt
import os
import ast
import tkinter as tk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class App(tk.Tk):
    def __init__(self, screenName: str | None = None, baseName: str | None = None, className: str = "Tk", useTk: bool = True, sync: bool = False, use: str | None = None) -> None:
        super().__init__(screenName, baseName, className, useTk, sync, use)

        self.title("Graph generator")

        file_name_label = tk.Label(self, text="File name:")
        file_name_label.pack()

        self.file_name_entry = tk.Entry(self)
        self.file_name_entry.pack()

        plot_button = tk.Button(
            self, text="Plot graph", command=self.plot_graph)
        plot_button.pack()

        self.canvas = None

    def plot_graph(self):

        if self.canvas:
            self.canvas.get_tk_widget().destroy()

        file_name = self.file_name_entry.get() + ".txt"
        file_path = os.path.join(os.path.dirname(__file__), file_name)

        try:
            with open(file_path, 'r') as file:
                data = ast.literal_eval(file.read())

            fig = plt.Figure(figsize=(6, 6), dpi=100)
            ax = fig.add_subplot(111)

            for i, serie in enumerate(data):
                x, y = zip(*serie)
                ax.step(x, y, where='post', label=f'Team {i+1}')

                x_max = 7200
                y_last = serie[-1][1]
                ax.hlines(y_last, max(x), x_max, colors=f'C{i}')

            ax.set_xlim(0, 7200)
            ax.set_ylim(0, 1500)
            ax.legend()

            self.canvas = FigureCanvasTkAgg(
                fig, master=self)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        except FileNotFoundError:
            messagebox.showerror(
                "Error", "File not found. Please enter a valid file name.")


if __name__ == "__main__":

    app = App()

    app.mainloop()
