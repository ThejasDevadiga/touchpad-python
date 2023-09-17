import tkinter as tk

class TouchPad(tk.Canvas):
    def __init__(self, master, bg_color, path_color, grid_size, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.bg_color = bg_color
        self.path_color = path_color
        self.grid_size = grid_size
        self.configure(bg=bg_color)
        self.bind("<B1-Motion>", self.draw)
        self.bind("<Button-1>", self.draw)

    def draw(self, event):
        x, y = event.x, event.y
        # Snap coordinates to the nearest grid line
        x = (x // self.grid_size) * self.grid_size
        y = (y // self.grid_size) * self.grid_size
        self.create_oval(x-4, y-4, x+4, y+4, fill=self.path_color)

root = tk.Tk()
root.title("Touchpad")

# Set the background color and path color
bg_color = "#F1F1F1"
path_color = "white"
grid_size = 10  # Size of the grid cells

# Create a canvas to draw the grid
grid_canvas = tk.Canvas(root, width=800, height=500, bg=bg_color)
grid_canvas.grid(row=0, column=0)

# Draw the grid lines
for i in range(0, 300, grid_size):
    grid_canvas.create_line(i, 0, i, 800, fill='black', tags='grid')
    grid_canvas.create_line(0, i, 500, i, fill='black', tags='grid')

# Create the touchpad
touchpad = TouchPad(root, width=800, height=500, bg_color=bg_color, path_color=path_color, grid_size=grid_size)
touchpad.grid(row=0, column=0)

root.mainloop()
