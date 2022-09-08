# -*- coding: utf-8 -*-
"""
Created on Thu Sep  8 11:37:49 2022

@author: mlshehab
"""

import os,glob
import argparse
import pygame
import numpy as np
import copy as cp
import pandas as pd
import pygame
import time
import sys
from lib import BLACK,RED,GREEN ,BLUE,GRAY 

PROJ_DIR=os.getcwd()

sys.path.append(PROJ_DIR)


from lib import Vehicle, World, draw_dashed_line, get_preceding_veh_id
from lib import scale_x, scale_y

high_D_data_folder = os.path.join(PROJ_DIR,'highD/data')

PARSER = argparse.ArgumentParser(description="Interactive HighD Simulator")
PARSER.add_argument('-recId', '--RECORDING_ID', default=3, type=int, help='ID of the desired highway recording')
PARSER.add_argument('-agnId', '--AGENT_ID', default=1048, type=int, help='ID of the desired ego agent')
PARSER.add_argument('-p','--path', default = high_D_data_folder, type = str, help = 'Path to the data files')

ARGS = PARSER.parse_args()


track_number = ARGS.RECORDING_ID
id_ego = ARGS.AGENT_ID
data_folder = ARGS.path


track_files = glob.glob(os.path.join(data_folder,'*tracks.csv')) # list of track files
track_recordingMeta_files = glob.glob(os.path.join(data_folder,'*recordingMeta.csv')) # list of recording Meta files
track_Meta_files = glob.glob(os.path.join(data_folder,'*tracksMeta.csv')) # list of track Meta files

default_action_1 = "KeepSpeed"
default_action_2 = "KeepLane"

trajectory = []

def main():
    df = pd.read_csv(track_files[track_number])
    df_Meta = pd.read_csv(track_Meta_files[track_number])
    df_recording_Meta = pd.read_csv(track_recordingMeta_files[track_number])
    

    
    # this is the ego vehicle dataFrame
    egoVeh = df[df["id"] == id_ego]
    
    
    #get the lane markings for annotation
    s_upper_lane = df_recording_Meta["upperLaneMarkings"].values[0]
    s_lower_lane = df_recording_Meta["lowerLaneMarkings"].values[0]
    
    upperLane = list(map(lambda x: float(x),s_upper_lane.split(';')))
    lowerLane = list(map(lambda x: float(x),s_lower_lane.split(';')))
    
    
    
    all_nearby_ids = []
    
    for v in egoVeh[["precedingId","followingId","leftPrecedingId","leftAlongsideId",\
                     "leftFollowingId","rightPrecedingId","rightAlongsideId","rightFollowingId"]]:
        dfv = egoVeh[v]
        ls = dfv.unique()
        for s in ls:
            if not s ==0:
                all_nearby_ids.append(s)
    
    # grab the starting time of the scenario
    t_min = 1e8
    t_max = -1e8
    for veh_id in all_nearby_ids:
        row = df_Meta[df_Meta["id"] == veh_id]
        t1 = row["initialFrame"].values[0]
        t2 = row["finalFrame"].values[0]
        if t1< t_min:
            t_min = t1
        if t2 > t_max:
            t_max = t2
        
    
    precedingVehs =      [ df[df["id"]==v] for v in egoVeh["precedingId"].unique()      if v!= 0]
    followingVehs =      [ df[df["id"]==v] for v in egoVeh["followingId"].unique()      if v!= 0]
    leftPreceedingVehs=  [ df[df["id"]==v] for v in egoVeh["leftPrecedingId"].unique()  if v!= 0]
    leftAlongsideVehs=   [ df[df["id"]==v] for v in egoVeh["leftAlongsideId"].unique()  if v!= 0]
    leftFollowingVehs=   [ df[df["id"]==v] for v in egoVeh["leftFollowingId"].unique()  if v!= 0]
    rightPreceedingVehs= [ df[df["id"]==v] for v in egoVeh["rightPrecedingId"].unique() if v!= 0]
    rightAlongsideVehs=  [ df[df["id"]==v] for v in egoVeh["rightAlongsideId"].unique() if v!= 0]
    rightFollowingVehs=  [ df[df["id"]==v] for v in egoVeh["rightFollowingId"].unique() if v!= 0]
    
    
    t_start = egoVeh["frame"].min()
    t_end = egoVeh["frame"].max()
    
    
    pygame.init()
    
    
    
    x_min = df["x"].min()
    x_max = df["x"].max()
    
    y_min = df["y"].min()
    y_max = df["y"].max()
    
    # create the display surface object  
    # of specific dimension proportional to the highway
    H = int(scale_y*(y_max - y_min )) + 50 + 100
    W = int((x_max-x_min)*scale_x)
    
    # height and width of car if represented as a rectangle
    car_h = (upperLane[-1] - upperLane[-2])*scale_y/2.0
    car_w = 2*car_h
    
    win = pygame.display.set_mode((W, H))
    
    
    MyWorld = World(win)
    
    # set the pygame window name 
    pygame.display.set_caption("[HighD Traffic Scenario]   Recording: %d      Agent Id: %d     Speed Limit: %.2f m/s"%\
                               (track_number+1, id_ego, MyWorld.v_limit))
    
    print("v_limt is: %f"%(MyWorld.v_limit))
    
    picture_ego = pygame.image.load('imgs/ego_car.png').convert()
    picture_ego = pygame.transform.scale(picture_ego, (car_w, car_h))
    
    picture_npc= pygame.image.load('imgs/npc_car.jpg').convert()
    picture_npc = pygame.transform.scale(picture_npc, (car_w, car_h))
    
    picture_npc_flipped  = picture_npc.copy()
    picture_npc_flipped = pygame.transform.flip(picture_npc_flipped, True, False)
    
    sysfont = pygame.font.get_default_font()
    font = pygame.font.SysFont(sysfont, 20)
    
    
    
    # TEXT TO DISPLAY WHEN USER GAINS CONTROL
    font = pygame.font.Font('freesansbold.ttf', 32)
    text = font.render('Please Press Any Key To Resume Manual Control', True, GREEN)
    
    
    textRect = text.get_rect()
    # create a rectangular object for the
    # text surface object
    
     
    # set the center of the rectangular object.
    textRect.center = (W // 2, H // 2)
    
    
    test_veh = []
    MyWorld.vehicles = []
    dt = int((1/25)*1000)
    first_time = True
    disp_vel = False
    keep_ego = False
    
    p = 0
    
    
    
    
    
    action_1 = None
    action_2 = default_action_2
    
    for t in range(t_min,t_max):
             
        pygame.time.delay(dt)
        MyWorld.t += dt
        # all vehicles which appears at this time step
        for event in pygame.event.get():
            # if event object type is QUIT  
            # then quitting the pygame  
            # and program both.  
            if event.type == pygame.QUIT:
                # it will make exit the while loop 
                run = False
                
        # stores keys pressed 
        keys = pygame.key.get_pressed()        
        
            
        df_t = df[df["frame"]==t]
    
        for d in df_t["id"]:
            dff = df[df["id"]==d]
            
            v0_npc = dff["xVelocity"].values[0]
            
            x_veh = scale_x*dff[dff["frame"]==t]["x"].values[0]
            y_veh = scale_y*dff[dff["frame"]==t]["y"].values[0] - scale_y*y_min
            
            if not d == id_ego:
                # take car of direction of vehicles
                if v0_npc > 0:
                    MyWorld.add_vehicle(Vehicle(x = x_veh, y = y_veh, w = car_w, h = car_h, \
                                            v=3, color = (255, 0, 0), picture= picture_npc,\
                                           font = font, ego = False, id_veh = d ))
                else:
                    MyWorld.add_vehicle(Vehicle(x = x_veh, y = y_veh, w = car_w, h = car_h, \
                                            v=3, color = (255, 0, 0), picture= picture_npc_flipped,\
                                           font = font, ego = False, id_veh = d ))
            else:
                # at this point the ego vehicle appears
                if first_time:
                  
                    # this tranforms m/s --> pixels/s
                    v0_ego = (egoVeh["xVelocity"].values[0])*(scale_x)*(dt/1000) 
                    
                    
                    ego_vehicle = Vehicle(x = x_veh, y = y_veh, w = car_w, h = car_h, \
                                        v=v0_ego,color = (0, 255, 0), picture= picture_ego,\
                                        font = font, ego = True, id_veh = d )
                    
                    
                    
                    MyWorld.add_vehicle(ego_vehicle)
                    
                    
                    MyWorld.py_game_win.blit(text, textRect)
                    
                    pygame.display.update()
                    first_time = False
                    disp_vel = True
                    event = pygame.event.wait()
                    
                else:
                    MyWorld.add_vehicle(ego_vehicle)
                    
                prec_id = get_preceding_veh_id(MyWorld, ego_vehicle,lowerLane,y_min)                  
                # stores keys pressed 
                keys = pygame.key.get_pressed()
    
    
                if keys[pygame.K_RIGHT]:
                    ego_vehicle.x += ego_vehicle.v
                    action_1 = default_action_1
                    
                if keys[pygame.K_UP]:
                    action_2 = "ChangeLane"
                    ego_vehicle.y -= ego_vehicle.v
                    
                if keys[pygame.K_DOWN]:
                    action_2 = "ChangeLane"
                    ego_vehicle.y += ego_vehicle.v
                    
                if keys[pygame.K_SPACE]:
                    if ego_vehicle.v < MyWorld.v_limit*(scale_x)*(dt/1000):
                        ego_vehicle.v += 0.2
                        action_1 = "Accelerate"
                    else:
                        ego_vehicle.v = MyWorld.v_limit*(scale_x)*(dt/1000)
                if keys[pygame.K_b]:
                    ego_vehicle.v -= 0.2
                    action_1 = "Decelerate"
                
                
    
                
        win.fill((255, 255, 255))
    
        for i,l in enumerate(lowerLane):
            if i == 0 or i == len(lowerLane)-1:
                draw_dashed_line((0,scale_y*(l-y_min)), (W,scale_y*(l-y_min)), win, dashed = False)
            else:
                draw_dashed_line((0,scale_y*(l-y_min)), (W,scale_y*(l-y_min)), win, dashed = True)
    
        for i,l in enumerate(upperLane):
            if i == 0 or i == len(upperLane)-1:
                draw_dashed_line((0,scale_y*(l-y_min)), (W,scale_y*(l-y_min)), win, dashed = False)
            else:
                draw_dashed_line((0,scale_y*(l-y_min)), (W,scale_y*(l-y_min)), win, dashed = True)
                
        if disp_vel and t< t_end:
            prec_id = get_preceding_veh_id(MyWorld, ego_vehicle,lowerLane,y_min)
            
            # good luck decoding this later on :)
            prec_veh_vel = df[df["id"] ==prec_id][df[df["id"] ==prec_id]["frame"]==t]["xVelocity"].values[0]
            
            trajectory.append([ego_vehicle.v*(1000/(scale_x*dt)), prec_veh_vel, action_1,action_2])
            
            action_1 = default_action_1
            action_2 = default_action_2
            
        #update the vehicle positions
        for veh in MyWorld.vehicles:
    
            MyWorld.py_game_win.blit(veh.picture, (veh.x, veh.y))
            #pygame.draw.rect(MyWorld.py_game_win, veh.color, (veh.x, veh.y, veh.w, veh.h))
            
            # this code colors the vehicle infront the ego vehicle
    
            # if disp_vel and t< t_end:
            #     if veh.id_veh == prec_id and prec_id != id_ego:
            #         veh.color = MAGENTA
    
    
                
                
        # it refreshes the window
        if disp_vel and t< t_end:
            p = (t - t_start)/float(t_end - t_start)
            txt_velocity = font.render("Ego velocity: %.2f m/s         \
            Press Space Bar to accelerate - Press 'B' to deccelerate - P = %.2f"%(ego_vehicle.v*(1000/(scale_x*dt)),p),True, GREEN)
            
            textRect_vel = txt_velocity.get_rect()
            
                # set the center of the rectangular object.
            textRect_vel.center = (W // 2, H -20 )
    
            MyWorld.py_game_win.blit(txt_velocity, textRect_vel)
    
            
        pygame.display.update() 
        
        MyWorld.vehicles = []
    
    # closes the pygame window 
    pygame.quit()
    
    
    
    
if __name__ == '__main__':
    main()
    
    
    
    
    