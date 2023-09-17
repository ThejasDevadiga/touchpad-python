import tkinter as tk
import websocket 
import json
import threading
import re

class TouchPad:
    def __init__(self, master, width, height):
        self.master = master
        self.width = width
        self.bg_color = '#070f24'
        self.path_color = 'white'
        self.master.configure(bg=self.bg_color)
        self.height = height
        self.prev_x = 0
        self.prev_y = 0
        self.grid_size = 10  # default grid size
        self.canvas = tk.Canvas(self.master, width=self.width, height=self.height, bg=self.bg_color)
        self.canvas.grid(row=0,column=0)
        self.selected_points = []
        # create background grid lines
        self.draw_grid()
        # create "Clear" button
        self.clear_button = tk.Button(self.master, height=3, width=8, text="Clear", command=self.clear_canvas)
        self.clear_button.grid(row=1,column=1)
        
        self.progress_bar = tk.Scale(self.master,bg=self.bg_color, from_=1, to=10, orient=tk.VERTICAL, length=300, label="Grid Size",fg='white' ,command=self.update_grid)
        self.progress_bar.set(self.grid_size)
        self.progress_bar.grid(row=0,column=1)
        self.oval_size = 2
        self.img = tk.PhotoImage(file="C:/Users/mrdev/projects/path-Finder/main/car1.png")
        self.canvas.bind("<B1-Motion>", self.draw)
    

    def bot_tracker(self,position):
        x, y = position
        self.canvas.create_image(x, y, image=self.img, tags="img")

    def draw(self, event):
        global ws
        if self.prev_x is not None and self.prev_y is not None:
            self.canvas.create_line(self.prev_x, self.prev_y, event.x, event.y, fill=self.path_color, width=4,tags="line")
        self.prev_x = event.x
        self.prev_y = event.y
        self.selected_points.append((event.x, event.y))
        # print("Sel point : ",self.selected_points[-2],self.selected_points[-1])
        if ws is not None:ws.send(f'({event.x},{event.y})')
        else:print("Not connected")
        # print(event.x, event.y)
        # draw green oval at position
    def del_sel_point(self,pos):
        if len(self.selected_points) > 0:
            self.selected_points.remove(pos)
    def clear_canvas(self):
        self.canvas.delete("all")
        self.prev_x = None
        self.prev_y = None
        self.selected_points = []
        # redraw grid lines
        self.draw_grid()

    def delete_line(self, start, end):
        for line in self.canvas.find_withtag("line"):
            del_line  = [float(start[0]), float(start[1]), float(end[0]), float(end[1])]
            if self.canvas.coords(line) ==del_line:
                self.canvas.delete(line)
                break


    def delete_img(self,pos):
        for img in self.canvas.find_withtag("img"):
            if self.canvas.coords(img) == [pos[0], pos[1]]:
                self.canvas.delete(img)
                break

    def draw_grid(self):
        # delete old grid lines
        self.canvas.delete("grid")
        # create new grid lines
        for i in range(self.grid_size):
            x = (i+1) * self.width/(self.grid_size+1)
            self.canvas.create_line(x, 0, x, self.height, fill='gray', tags="grid")
        for i in range(self.grid_size):
            y = (i+1) * self.height/(self.grid_size+1)
            self.canvas.create_line(0, y, self.width, y, fill='gray', tags="grid")
        # for i in range(self.grid_size):
        #     y = (i+1) * self.height/(self.grid_size+1)
        #     self.canvas.create_line(0, y, self.width, y, fill='gray', tags="grid")

    def update_grid(self, value):
        self.clear_canvas()
        self.grid_size = int(value)
        self.draw_grid()


def connect_ws():
    global ws
    def on_open(ws):
        ji = {
            "isfirst": "true",
            "device": "pc"
        }
        ws.send(json.dumps(ji))
        
    def on_message(ws, message:str):
        global app
        global prv_position
        pat = r"\(\d+,\d+\)"
        if re.match(pat,message):
            msg = message.replace("(","").replace(")","").split(",") 
            pos = (int(msg[0]),int(msg[1]))
            if prv_position ==None:
                prv_position = pos
            app.bot_tracker(position=pos)
            # print("del lines : ",prv_position,pos)
            app.delete_line(prv_position,pos)
            app.delete_img(prv_position)
            prv_position = pos
       
        response = json.loads(message)
        conection = response["conection"]
        print("conection: ", conection)
        if conection == "true":
            print("Connection Established")
            devices = json.loads(response["devices"])
            print(f"Mobile: {devices['mobile']}\tPC: {devices['pc']}\tESP: {devices['ESP']}")

        elif conection == "newConnection" or conection == "lost":
            devices = json.loads(response["devices"])
            print(f"Mobile: {devices['mobile']}\tPC: {devices['pc']}\tESP: {devices['ESP']}")

        elif conection == "Sending":
            devices = json.loads(response["devices"])
            print(f"Mobile: {devices['mobile']}\tPC: {devices['pc']}\tESP: {devices['ESP']}")
            
        elif conection == "alreadyConected" or conection == "close":
            ws.close()
        
    def on_close(ws):
        print("Close connection")
        ws.close()  
    ws = websocket.WebSocketApp('ws://localhost:8765/', on_open=on_open, on_message=on_message, on_close=on_close)
    websocket.WebSocket
    print("con :",ws)
    ws.run_forever()
if __name__ == '__main__':
    ws = None
    prv_position= None
    root = tk.Tk()
    ws_thread = threading.Thread(target=connect_ws) 
    ws_thread.start()
    app = TouchPad(root, 1000, 600)
    root.mainloop()
