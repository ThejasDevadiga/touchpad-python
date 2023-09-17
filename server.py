import asyncio
import websockets
import re
import numpy as np
import math
 

class Calc_velocity:
    def __init__(self,W,H,R):
        self.W = W
        self.H= H
        self.R = R
        self.vel = []
        self.MaxRpm=360
        self.MinRpm=250
        self.position = [100,100,0]
        self.actual_position =[100,100,0]
        self.actual_path = [0,0]
        self.x= []
        self.y = []
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
        r =  np.array([
            [np.cos(phi), 0],
            [np.sin(phi), 0],
            [0, 1]
        ])
        return r
    def toTangent(self, RPM):
        c = 2 * np.pi
        return c * RPM / 60
    def smoothstep(self,x,x_max):
        x_min=0
        N=4
        x = np.clip((x - x_min) / (x_max - x_min), 0, 1)

        result = 0
        for n in range(0, N + 1):
            result += comb(N + n, n) * comb(2 * N + 1, N - n) * (-x) ** n

        result *= x ** (N + 1)
        return result
    
    def normalize(self,dphi):
        if(dphi>np.pi):
            dphi = -(2*np.pi - dphi)
        elif(dphi<-np.pi):
            dphi = 2*np.pi + dphi
        # if dphi!=dphi1:
            # print("changed_dphi : ",dphi)
        return dphi
    def forwardKine(self,lrpm,rrpm,timestep):
        wheelVel = np.array([
            [self.toTangent(lrpm)],
            [self.toTangent(rrpm)]])  
            
        Rt=self.RT(self.actual_position[2])
            
        Eta = np.round(np.array(np.dot(Rt,np.dot(self.J,wheelVel))),decimals=4)
            
        self.actual_position[0]+=timestep*Eta[0][0]
        self.actual_position[1]+=timestep*Eta[1][0]
        self.actual_position[2]+=timestep*Eta[2][0]
        self.actual_path += [self.actual_position[0],self.actual_position[1]]

        
            
            
connected = set()

async def register(websocket):
    global position
    try:
        position = None
        connected.add(websocket)
        print(f"Client {websocket.remote_address} connected")
    except Exception as e:
        print(f"Error in registering client {websocket.remote_address}: {e}")


async def unregister(websocket):
    try:
        connected.remove(websocket)
        print(f"Client {websocket.remote_address} disconnected")
    except Exception as e:
        print(f"Error in unregistering client {websocket.remote_address}: {e}")

async def broadcast(message):
    objects_position_list = [(363,207),(419,372)]
    global position
    global interrupt
 
    bot = Calc_velocity(17,10,4)
    for websocket in connected.copy():
        try:
            pattern = r'\((-?\d+(\.\d+)?),\s*(-?\d+(\.\d+)?),\s*(-?\d+(\.\d+)?)\)'
            match = re.match(pattern, message)
            if match :
                if interrupt:
                    print("Interrupt activated !! can't move forward...")
                else:
                    Vl = float(match.group(1))
                    Vr = float(match.group(3))
                    time = float(match.group(5))
                    bot.actual_position = position
                    bot.forwardKine(Vl,Vr,time)
                    position = bot.actual_position
                    for obj_position in objects_position_list:
                        distance_btw_obj_bot = round(np.sqrt((obj_position[1]-position[1])**2 + (obj_position[0] - position[0])**2), 2)
                        if distance_btw_obj_bot<=2:
                            print("Object ahead !!! position :",position)
                            print("\n\nSending message to:", websocket.remote_address)
                            await websocket.send(f"INTR({round(position[0],4)},{round(position[1],4)},{round(position[2],4)})")
                            interrupt = True
                            break       
                    else:
                        print("\n\nSending message to:", websocket.remote_address)
                        
                        await websocket.send(f"({round(position[0],4)},{round(position[1],4)},{round(position[2],4)})")
                        print(f"Current position is : [{position[0]}X,{position[1]}Y,{math.degrees(position[2])}degree]")    
            else:
                await websocket.send(f"{message}")
        except websockets.ConnectionClosed:
            print(f"Client {websocket.remote_address} disconnected unexpectedly")
            await unregister(websocket)

async def my_handler(websocket, path):
    global position
    global interrupt
    try:
        await register(websocket)
        try:
            async for message in websocket:
                print(f"\nReceived message from client: {message}\n\n")
                if message == "newClient":
                    print("Sending message is: connected" )
                    await websocket.send("connected")
                elif message.startswith("{"):
                    print("new connection !!!")
                    await websocket.send("connected")
                elif "[" in message: 
                    received_position =  [float(i) for i in message[1:-1].split(",")]
                    if position is not None:
                        position = pid_control(position,received_position)
                    else:
                        position = received_position
                    print(f"Current position :{position[0],position[1],position[2]}")
                    await websocket.send(f"{position[0],position[1],position[2]}")
                elif message =="DEACT INTR" :
                    print("Sending message is: Interrupt deactivated " )
                    await broadcast("Interrupt deactivated ")
                    interrupt = False
                elif "exit" in message:
                    print("Sending message is: exit" )
                    await websocket.send("Exiting....")
                    await unregister(websocket)
                else:
                    await broadcast(message)
        except websockets.ConnectionClosed:
            print(f"Client {websocket.remote_address} disconnected unexpectedly")
            await unregister(websocket)
        except Exception as e:
            print(f"Error in handling message from client {websocket.remote_address}: {e}")
            await unregister(websocket)
    except Exception as e:
        print(f"Error in connection with client {websocket.remote_address}: {e}")
        await unregister(websocket)
async def main():
    
    try:
        print("ws://localhost:8765/")
         
        async with websockets.serve(my_handler, "localhost", 8765):
            await asyncio.Future()
    except Exception as e:
        print(f"Error in WebSocket server: {e}")

if __name__ == "__main__":
    
    position = None
    interrupt = False 
    asyncio.run(main())
