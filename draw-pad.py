import tkinter as tk
import json,math,time,numpy as np
import threading
from PIL import Image, ImageTk
import re
import numpy as np
import asyncio
import websockets,websocket
from websocket import WebSocketConnectionClosedException
from threading import Thread
import customtkinter as ctk
from tkinter import messagebox
import re
from math import *



class Diffrentiator:
    def __get_distance(self,src,dest):
        x2 = dest[0]
        x1 = src[0]
        y2 = dest[1]
        y1 = src[1]
        return ((x2-x1)**2+(y2-y1)**2)**(1/2)

    def __get_angle(self,src,dest):
        x2 = dest[0]
        x1 = src[0]
        y2 = dest[1]
        y1 = src[1]
        return degrees(atan((y2-y1)/(x2-x1)))

    def __diff_in_node(self,src,dest):
        ini_Cordinate = src
        fin_Cordinate = dest
        return (fin_Cordinate[0]-ini_Cordinate[0],fin_Cordinate[1]-ini_Cordinate[1])

    def __get_direction(self,src,dest):
        y2 = dest[1]
        y1 = src[1]
        # Movevalue = self.__diff_in_node(src,dest)
        
        angle = self.__get_angle(src, dest)
        return  angle
    def get_values(self,src,dest):
        return (round(self.__get_distance(src,dest),4),self.__get_direction(src,dest))

class car:
    global velocity
    def __init__(self,W,H,R):
        self.W = W
        self.H=H
        self.R = R
        self.vel = []
        self.MaxRpm=355
        self.MinRpm=250
        self.phi = 0
        self.position = [0,0,0]
        self.J_Inv = np.array([
            [1/self.R, -W/self.R],
            [1/self.R, W/self.R]
        ])
        self.J = np.array([
            [self.R/2, self.R/2],
            [-self.R/(2*W), self.R/(2*W)]
        ])

    def Ro(self,phi):
        r = np.array([
            [np.cos(phi), np.sin(phi), 0],
            [0, 0, 1]
        ])
        return r
    def RT(self,phi):
        r = np.array([
            [np.cos(phi), 0],
            [np.sin(phi), 0],
            [0, 1]
        ])
        return r
    def toTangent(self, RPM):
        c = 2 * np.pi
        return c * RPM / 60
    
    def inverseKine(self,prev,next):
        try:
            x1,y1 = prev
            x2,y2 = next
            orientation = math.atan2(y2 - y1,  x2 - x1)
            print(
                f"from  {math.degrees(self.phi)}degree to {math.degrees(orientation)}degree")
            if self.phi != orientation:
                print("So bot rotate now !!")
                dis=self.R*abs(self.phi-orientation)
                S=0.5
                time=(dis/(S*100))
                print(
                    f"Expected bot to rotate {math.degrees(orientation)}  degree")
                # print("time:",time)
                self.rotate(0,0,orientation,time)
                
            x2=round(np.sqrt((y2-y1)**2+(x2-x1)**2),2)
            S=1
            time=(x2/(S*100))
            self.phi=0        
            print("TIME:",time)
            self.rotate(0,x2,self.phi,time)
        except Exception as e:
            print("Error is :",e)

    def rotate(self,x1,x2,phi2,time):
        timestep=time/4
        print("TIME STEP:",timestep)
        y1=0
        for i in np.arange(0,time,timestep):
            dx=x2-x1
            dy=0
            dphi=phi2-self.phi
            if(dphi>np.pi):
                dphi = 2*np.pi - dphi
            
            elif(dphi<-np.pi):
                dphi = 2*np.pi + dphi
            
            dtime = abs(time-i)
            Botvel=np.array([[dx/dtime],
                            [dy/dtime],
                            [dphi/dtime]]).reshape(3,1)
            Rot=self.Ro(self.phi)
            Vs=60*(np.array(np.dot(self.J_Inv,np.dot(Rot,Botvel))).reshape(2,1))/(2*np.pi)
            # Vs=[Vs[0][0],Vs[1][0]]
            absVs = np.abs(Vs)
            maxAbsV = np.max(absVs)
            if maxAbsV > self.MaxRpm:
                Vs = [v * self.MaxRpm / maxAbsV for v in Vs] 
            absVs = np.abs(Vs)
            minAbsV = np.min(absVs)
            for k in range(2):
                if  abs(Vs[k][0]) < self.MinRpm:
                    Vs[0][0] = 0
                    Vs[1][0] = 0
                    break
            wheelVel = np.array([
            [self.toTangent(Vs[0][0])],
            [self.toTangent(Vs[1][0])]
        ])   
            Rt=self.RT(self.phi)
            Eta = np.round(np.array(np.dot(Rt,np.dot(self.J,wheelVel))),decimals=4)
            x1+=timestep*Eta[0][0]
            y1+=timestep*Eta[1][0]
            self.phi+=timestep*Eta[2][0]
            print("\n ",Vs[0][0],Vs[1][0],timestep*1000)
            ws.send(f"({Vs[0][0]},{Vs[1][0]},{timestep})")
            
        print("\n\nEXPECTED FINAL POSITION:",x1,y1,self.phi)
        print("\n\n\n")
        self.vel = []
        # return res


class AlcuinConnector:
    def __init__(self, root:tk.Tk):
        self.root = root
        self.root.title("ALCUIN BOT")
        self.root.geometry(f"{800}x{300}")
        root.configure(background="#070f24")
        root.resizable(0, 0)

        self.logo_label = ctk.CTkLabel(self.root, text=" ALCUIN CONNECTION ", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=3, padx=(250,50), pady=(50, 50))

        self.entry = ctk.CTkEntry(self.root, placeholder_text="Enter the data here")
        self.entry.grid(row=2, column=1, columnspan=3, padx=(50, 50), sticky="nsew")

        self.horiz_size = ctk.CTkEntry(self.root,width=50,height=2 ,placeholder_text="Width")
        self.vert_size = ctk.CTkEntry(self.root, width=50,placeholder_text="Height")

        self.horiz_size.grid(row=3, column=3,padx=50,pady=10,stick="nsew")
        self.vert_size.grid(row=5, column=3,padx=50,pady=10,sticky="nsew")

        self.main_button_1 = ctk.CTkButton(master=self.root, fg_color="transparent",text="Connect",command=self.connect, border_width=2, text_color=("gray10", "#DCE4EE"))
        self.main_button_1.grid(row=2, column=4,padx=50 , sticky="nsew")
        self.exit_button = ctk.CTkButton(master=self.root, fg_color="transparent",text="Exit",command=exit, border_width=2, text_color=("gray10", "#DCE4EE"))
        self.exit_button.grid(row=7, column=4,padx=50, pady=10 ,sticky="nsew")

    def show_alert(self,title,message):
        messagebox.showinfo(title, message)  

    def connect(self):
        global screen
        global IPADDRESS
        regex = r"^wss?://[\w.-]+(:\d+)?(/[\w./]*)?$"
        val = self.entry.get()
        width =self.horiz_size.get()
        height = self.vert_size.get()
        if val=="":
            self.show_alert("Alert","Please enter some data")
        elif re.match(regex, val) or True:
            val=IPADDRESS
            print(val)
            self.root.destroy()
            root = tk.Tk()
            screen =  TouchPad(root, int(600),int(600),val)
            threading.Thread(target=connect_ws,args=(val,)).start()
            root.mainloop()
        else:
            self.show_alert("Alert","Invalid URL")



class TouchPad(Diffrentiator):
    def __init__(self, master:tk.Tk, width, height,uri):
        super().__init__()
        self.carController = car(33,20,4)
        self.master = master
        self.position = [0,0,0]
        self.width = width
        self.uri =tk.StringVar()
        self.uri.set(uri)
        self.bg_color = '#070f24'
        self.path_color = 'white'
        self.master.configure(bg=self.bg_color)
        self.height = height
        self.conn = False
        self.pathPoints = []
        self.grid_size = 10 
        self.canvas = tk.Canvas(self.master, width=self.width, height=self.height, bg=self.bg_color)
        self.canvas.grid(row=0,column=1,pady=30)
        self.selected_points = [ ]
        
        self.draw_grid()

        self.clear_button = tk.Button(self.master, height=3, width=8, text="Clear", command=self.clear_canvas)
        self.clear_button.grid(row=2,column=1)
        self.connect_status = tk.StringVar()
        self.connect_status.set("Not connected")
        self.progress_bar = tk.Scale(self.master,bg=self.bg_color, from_=1, to=50, orient=tk.VERTICAL, length=300, label="Grid Size",fg='white' ,command=self.update_grid)
        self.progress_bar.set(self.grid_size)
        self.progress_bar.grid(row=0,column=2)
        self.oval_size = 2
        self.img = ImageTk.PhotoImage(Image.open("C:/Users/mrdev/projects/path-Finder/main/car1.png"))
        self.canvas.bind("<B1-Motion>", self.draw)

        self.connect_label = ctk.CTkLabel(master, text="Connection Status :",font=ctk.CTkFont(size=15, weight="bold"))
        self.connect_status_label =  tk.Label(master,  textvariable=self.connect_status,fg='red',bg="#070f24", font=ctk.CTkFont(size=20, weight="bold"))
        self.exit_button = ctk.CTkButton(master, text="Exit",command=self.close, fg_color="transparent", border_width=2,text_color=("gray10", "#DCE4EE"))
        self.reconnect_button = ctk.CTkButton(master, text="Reconect",command=self.reconnect, fg_color="transparent", border_width=2,text_color=("gray10", "#DCE4EE"))

        self.connect_label.grid(row=1, column=0,padx=20)
        self.connect_status_label.grid(row=1, column=1)
        self.reconnect_button.grid(row=1,column=2)
        self.socket = None
        self.exit_button.grid(row=2, column=2,padx=20,pady=30)
        self.start_pos = None

    def bot_tracker(self,position,prv_position):
        x, y = position
        # x1,y1 = prv_position
        # direction = math.degrees(self.line_direction(x1,y1,x,y)) 

        # if direction<0:
        #     direction =180+abs(direction)
        # direction = round(direction / 20) * 20
        # rotated_img = self.img.rotate(direction)
        # print(direction)

        # photo = ImageTk.PhotoImage(rotated_img)
        self.canvas.create_image(x, y, 
        image=self.img, tags="img")

    def line_direction(self,x1, y1, x2, y2):
        direction = math.atan2(y2-y1, x2-x1)
        return direction
    def __get_distance(self,src,dest):
        x2 = dest[0]
        x1 = src[0]
        y2 = dest[1]
        y1 = src[1]
        return ((x2-x1)**2+(y2-y1)**2)**(1/2)
        
    def draw(self, event):
        global ws
    
        #  Get the mouse Postions
        x,y = (event.x,event.y)
        # x = (x // (61-self.grid_size)) *(61- self.grid_size)
        # y = (y // (61-self.grid_size)) * (61-self.grid_size)

        new_pos = (x,y)
        # restrict the outer point
        new_pos =  self.replace_point_below_line(new_pos,(self.width-20,20),(20,20))
        new_pos =  self.replace_point_below_line(new_pos,(20,20),(20,self.height))
        new_pos =  self.replace_point_below_line(new_pos,(0,self.height-20),(self.width-20,self.height-20))
        new_pos =  self.replace_point_below_line(new_pos,(self.width-20,self.height-20),(self.width-20,0))
        new_pos =( int(new_pos[0]),int(new_pos[1]))
        
        # if no values are present 
        if self.start_pos == None:
            self.start_pos= new_pos
        if len(self.selected_points)==0:
                self.ini_position =[new_pos]
                self.selected_points = [new_pos]
        
        if self.__get_distance(self.selected_points[0],new_pos)>=30:
            print(f"New pos : {new_pos}")        
            self.send_message(new_pos)
            self.selected_points = [new_pos]


    def calculate_points_between_two_points(self,P1, P2,dist, num_points):
        interval = dist / (num_points + 1)
        line_angle = math.atan2(P2[1] - P1[1], P2[0] - P1[0])
        points = []
        for k in range(1, num_points + 1):
            theta = line_angle 
            delta_x = k * interval * math.cos(theta)
            delta_y = k * interval * math.sin(theta)
            points.append((round(P1[0] + delta_x), round(P1[1] + delta_y)))
        return points
    
    def replace_point_below_line(self,P, P1, P2):
        v = [P2[0] - P1[0], P2[1] - P1[1]]
        w = [P[0] - P1[0], P[1] - P1[1]]
        dot = v[0] * w[0] + v[1] * w[1]
        t = dot / (v[0]**2 + v[1]**2)
        projection = (P1[0] + t * v[0], P1[1] + t * v[1])
        d = (P[0] - P1[0]) * (P2[1] - P1[1]) - (P[1] - P1[1]) * (P2[0] - P1[0])
        if d < 0:
            return projection
        else:
            return P    
            
    def slope(self,pos1,pos2):
        try:
            return (pos2[1]-pos1[1])/(pos2[0]-pos1[0])
        except ZeroDivisionError:
            return 90
    def send_message(self,cur_position):
        global ws
        try:
                prev_position = self.selected_points[0]
                new_theta = self.slope(prev_position,cur_position)
                print("\n\n\nPrev pos : ",prev_position,self.carController.position[2])
                print("Curr pos : ",cur_position,new_theta)
                self.carController.inverseKine(prev_position,cur_position)
                
                    # ws.send(f"({result[0][0][0]},{result[0][1][0]},{result[1]})")
                self.canvas.create_line(prev_position[0], prev_position[1], cur_position[0], cur_position[1], fill=self.path_color,   width=4,tags="line")
    
        except websocket.WebSocketConnectionClosedExceptions as e:
                print(f"trying to reconnect...Error : {e}")
                self.showReconn()
                # threading.Thread(target=connect_ws,args=(self.uri,)).start()
                self.connect_status.set("disconnected")
                self.connect_status_label.configure(fg='red')
        except Exception as e:
                print(f"Please check websocket connection...!!Error code : {e}")
        

    def calc_deviation(self,position:tuple)->tuple:
        return self.get_values(position,(self.prev_x,self.prev_y))
    
    def del_sel_point(self,pos):
        if len(self.selected_points) > 0:
            self.selected_points.remove(pos) 
    def clear_canvas(self):
        self.canvas.delete("all")
         
        # self.selected_points = []
        self.draw_grid()

    def delete_line(self, start, end):
        for line in self.canvas.find_withtag("line"):
            del_line  = [float(start[0]), float(start[1]), float(end[0]), float(end[1])]
            if self.canvas.coords(line) ==del_line:
                self.canvas.delete(line)
                break

    def delete_img(self,prv_pos,pos):
        for img in self.canvas.find_withtag("img"):
            if self.canvas.coords(img) == [prv_pos[0], prv_pos[1]]:
                self.canvas.delete(img)
                break
        self.canvas.create_line(prv_pos[0],prv_pos[1],pos[0], pos[1], fill='green', width=4,tags="line")

    def draw_grid(self):
        self.canvas.delete("grid")
        for i in range(self.grid_size):
            x = (i+1) * self.width/(self.grid_size+1)
            self.canvas.create_line(x, 0, x, self.height, fill='gray', tags="grid")
        for i in range(self.grid_size):
            y = (i+1) * self.height/(self.grid_size+1)
            self.canvas.create_line(0, y, self.width, y, fill='gray', tags="grid")

    def update_grid(self, value):
        self.clear_canvas()
        self.grid_size = int(value)
        print(self.grid_size)
        self.draw_grid()

    def change_uri(self):
        global ws
        ws.close()
        self.master.destroy()
        con = tk.Tk()
        AlcuinConnector(con)
        con.mainloop()

    def reconnect(self):
        global ws

        if not self.conn:
            ws.close()
            print("Reconnecting.........")
            threading.Thread(target=connect_ws,args=(self.uri,)).start()

    def hideReconn(self):
        self.reconnect_button.grid_forget()
    
    def showReconn(self):
        self.reconnect_button.grid(row=1,column=2)

    def show_alert(self,title,message):
        messagebox.showinfo(title, message)  

    def close(self): 
        try:
            if self.socket:
                self.master.destroy()
                # asyncio.run(self.socket.close())
        except ValueError :
                print("Closing.....")
        exit(0)

def connect_ws(uri):
    global ws
    global screen
    global position
    global IPADDRESS
    screen.connect_status.set("Disconnected")
    screen.connect_status_label.configure(fg='red')
    screen.showReconn()
    print("connecting.........")
    def on_open(ws):
        ji ={"clientName":"alcuin","position":position}
        ws.send(json.dumps(ji))
        ws.send(ji)
    def on_message(ws, message:str):
        global screen
        global prv_position
        print("Recieved :",message)
        try:
            pat = r'\((\d+\.\d+),(\d+\.\d+)\)'
            match = re.match(pat,message)
            if match:
                msg = match.groups()
                pos =(float( msg[0]),float(msg[1]))
                if prv_position ==None:
                    prv_position = pos
                screen.bot_tracker(pos,prv_position)
                screen.delete_line(prv_position,pos)
                screen.delete_img(prv_position,pos)
                prv_position = pos
            elif message=="connected":
                screen.hideReconn()
                ws.send("[20,20,0]")
                screen.connect_status.set("Connected")
                screen.conn = True
                screen.connect_status_label.configure(fg='green')
            else:
                print("Not matched : ",message)
        except Exception as e:
            print("ERROR 463 : ",e)

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
        
    try:
        ws = websocket.WebSocketApp(IPADDRESS, on_open=on_open, on_message=on_message, on_close=on_close)

    except Exception as e:
        print("Error 492:", e)
        screen.connect_status.set("Disconnected")
        screen.connect_status_label.configure(fg='red')
        print(e)
    # if ws is not None:
    ws.run_forever()


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    ws = None
    IPADDRESS = "ws://localhost:8765/"
    screen = None
    prv_position= None
    position = [0,0,0]
    con = tk.Tk()
    AlcuinConnector(con)
    con.mainloop()
