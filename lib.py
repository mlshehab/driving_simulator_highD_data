# -*- coding: utf-8 -*-
"""
Created on Tue Sep  6 14:44:54 2022

@author: mlshehab
"""

 

import pygame
from pygame.locals import *
import numpy as np

BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (200, 200, 200) 

scale_x = 4.0
scale_y = 15.0


def draw_dashed_line(start_pos, end_pos, win, dashed):
    # assuming the line is horizontal
    
    _,_,w, h = win.get_rect()
    
    # this looks nice for lane markings
    dash_size = 500/3.0
    empty = dash_size/3.0

    st = 0
    if dashed:
        pygame.draw.line(win,color= (0,0,0), start_pos = (st,start_pos[1]),end_pos = (st+ empty, start_pos[1]), width =4)
        st+= 2*empty

        while st < w:
            pygame.draw.line(win,color= (0,0,0), start_pos = (st,start_pos[1]),end_pos = (st+ 2*empty , start_pos[1]), width =4)
            st+= 3*empty
    else:
        pygame.draw.line(win,color= (0,0,0), start_pos = (st,start_pos[1]),end_pos = (end_pos[0], start_pos[1]), width =4)


class Vehicle():
    def __init__(self, x,y,w,h,v,color,picture,font,ego,id_veh):
        self.x = x
        self.y = y
        # dimensions of the rectangle
        self.w = w
        self.h = h
        # velocity
        self.v = v
        
        # color of the vehicle if we wanted to use rectangles
        self.color = color
        self.picture = picture
        self.font = font
        
        self.ego = ego
        
        
        self.text = "ego" if self.ego else ""
        self.text_image = None
        self.text_color = BLUE if self.ego else BLACK
        self.id_veh = id_veh
        
    
    def update_position(self, w,h):
        # so far the model is constant acceleration
        
        if not self.ego:
            self.x += self.v
            
        if self.x >= w:
            print("The vehicle went out of bounds!")
            self.x = 0
            
            
    def update_text(self):
        added_text = ", v = %.1f m/s, x = %0.1f"%(10.0*self.v, self.x) if self.ego else "v = %.1f m/s"%(10.0*self.v)
        self.text += added_text
    def restore_text(self):
        self.text = self.text[:3] if self.ego else ""
        
    def render_text_image(self):
        self.text_image = self.font.render(self.text, True, self.text_color)

    
        


class World():
    def __init__(self, py_game_win):
        self.py_game_win = py_game_win
        self.vehicles = []
        _,_, self.width, self.height = self.py_game_win.get_rect()
        self.t = 0
        self.v_limit = 50
    
    def add_vehicle(self, vehicle):
        self.vehicles.append(vehicle)
        


                            
                            
                            
                            
def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    
    return [array[idx],array[idx+1]] if value > array[idx] else [array[idx-1],array[idx]]


def lane_to_lane_id(lane, lowerLane):                         
    if lane == [lowerLane[0],lowerLane[1]]:
        return 1
    if lane == [lowerLane[1],lowerLane[2]]:
        return 2
    if lane == [lowerLane[2],lowerLane[3]]:
        return 3


def get_preceding_veh_id(World, ego_vehicle,lowerLane,y_min):
    vehs = World.vehicles
    ego_lane = find_nearest(lowerLane, (ego_vehicle.y/scale_y) + y_min)
    ego_lane_id = lane_to_lane_id(ego_lane,lowerLane)
    
    vehs_in_same_lane = []
    
    for veh in vehs:
        if not veh.ego: 
            veh_lane = find_nearest(lowerLane, (veh.y/scale_y) + y_min)
            if  lane_to_lane_id(veh_lane,lowerLane) == ego_lane_id:
                vehs_in_same_lane.append(veh)
                    
    x_min = 10000
    
   
    prec_id = None
    
    for veh in vehs_in_same_lane:
        if abs((ego_vehicle.x/scale_x) - (veh.x/scale_x)) < x_min and ego_vehicle.x < veh.x:
            x_min = abs(ego_vehicle.x - veh.x)
            prec_id = veh.id_veh
            
    return prec_id if prec_id else ego_vehicle.id_veh
