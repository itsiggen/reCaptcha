import gym
import os
from math import sin, cos, radians, atan2, degrees, sqrt
import numpy as np
import pandas as pd
from random import randrange, choice, uniform
from gym import spaces
import pyautogui as ag
import requests
import datetime
import time

# Global environment definitions

FPS = 50
ag.PAUSE = 0.01
file_dir = os.getcwd()
csv_folder = 'storage'
ag.FAILSAFE = False

class piecewiseA(gym.Env):
    
    def __init__(self, max_steps=100, step_size = 20, interval = 120):
        self.action_space = spaces.Box(np.array([0,-1]), np.array([+1,+1]), dtype=np.float32)
        self.observation_space = spaces.Box(np.array([-1000,-1000,-1000,-1000,0]),
                    np.array([1000,1000,1000,1000,1000]), dtype='uint8')
        self.hour = datetime.datetime.now().strftime("%Y-%m-%d-%H")
        self.max_steps = max_steps
        self.step_size = step_size
        self.goal_size = 5
        self.trajectory_dir = -1
        self.episode_inc = -1
        self.interval = interval
        self.scores = []
        self.delays = []
        self.times = []
        self.tabscores = [[], []]

    def reset(self):
        # Set direction towards to / away from trigger button
        self.trajectory_dir *= -1
        time.sleep(1)
        # Set goal state
        self.episode_inc += 1
        self.goal_state = self.episode_inc % 4
        # Current position and direction of the agent
        self.init_pos = ag.position()
        self.agent_pos = self.init_pos
        self.goal_pos = self.getGoal()
        self.init_dir = self.posToAngle(self.goal_pos, self.agent_pos)
        self.agent_dir = self.init_dir
        self.dist = self.posToDist(self.agent_pos, self.goal_pos)
        self.lasts = None
        self.speed = 0
        self.reward = 0.0
        self.prev_reward = 0.0
        self.t = 0.0
        self.start = time.time()
        
        # Control the time delay between each query
        if self.episode_inc != 0:
            if self.goal_state == 0:
                time.sleep(uniform(self.interval*0.75, self.interval*1.25))
            elif self.goal_state == 2:
                time.sleep(uniform(self.interval*0.05, self.interval*0.1))
        
        # These fields should have been defined by the start of the episode
        assert self.agent_pos is not None
        assert self.goal_pos is not None

        # Step count since episode start
        self.step_count = 0

        # Return first observation
        obs = self.gen_obs()
        return obs
    
    def step(self, action):
        self.step_count += 1
        self.t += 1.0/FPS
        done = False
        
        # Convert to relative angle and distance
        distance = max(action[0]*self.dist/self.step_size, 2)
        angle = (action[1]*25*self.trajectory_dir + self.agent_dir) % 360
        
        # Move to new position
        self.agent_pos = self.angleToPos(self.agent_pos, distance, angle)
        ag.moveTo(self.agent_pos[0], self.agent_pos[1])
        
        # Calculate the new direction and speed
        self.agent_dir = self.posToAngle(self.agent_pos, self.goal_pos)
        self.speed = distance
            
        # Generate new observation/state
        obs = self.gen_obs()
        
        if self.goalBox():
            if self.trajectory_dir == 1:
                time.sleep(uniform(0.2, 0.5))
                ag.mouseDown()
                time.sleep(uniform(0.08, 0.12))
                ag.mouseUp()
                time.sleep(uniform(0.8, 1))
                try:
                    r = requests.get("http://localhost:5000/alterego/result")
                    self.result = r.json()["score"]
                    self.lasts = r.json()["challenge_ts"]
                except:
                    print("Server returned no score")
                    self.result = 0
                tab = 0 if self.goal_state == 0 else 1
                self.tabscores[tab].append(self.result)
                self.reward += self.gen_reward(tab, self.result)
                now = datetime.datetime.now()
                # Compute total delay
                delay = time.time() - self.start
                self.update_stats(self.score, delay, tab, now)
                self.log_results()
            else:
                time.sleep(uniform(0.2, 0.5))
                ag.click()
                time.sleep(uniform(0.2, 0.5))
            done = True
            
        # Add penalty on steps taken
        self.reward -= 0.001
        step_reward = self.reward - self.prev_reward
        self.prev_reward = self.reward
    
        return obs, step_reward, done, {}
    
    def posToDist(self, p0, p1):
        dx = (p0[0]-p1[0])**2
        dy = (p0[1]-p1[1])**2
        return sqrt(dx + dy)
    
    def posToAngle(self, p0, p1):
        angle = degrees(atan2(p1[1] - p0[1], p1[0] - p0[0]))
        return angle % 360
            
    def angleToPos(self, p0, distance, angle):
        theta = radians(int(angle))
        point = [int(p0[0] + distance * cos(theta)), int(p0[1] + distance * sin(theta))]
        return point
        
    def goalBox(self):
        a = self.agent_pos[0] >= self.goal_pos[0]-self.goal_size and self.agent_pos[0] <= self.goal_pos[0]+self.goal_size
        b = self.agent_pos[1] >= self.goal_pos[1]-self.goal_size and self.agent_pos[1] <= self.goal_pos[1]+self.goal_size
        return a and b
        
    def gen_obs(self):
        initx = self.goal_pos[0] - self.init_pos[0]
        inity = self.goal_pos[1] - self.init_pos[1]
        currx = self.goal_pos[0] - self.agent_pos[0]
        curry = self.goal_pos[1] - self.agent_pos[1]
        obs = np.array([initx, inity, currx, curry, int(self.dist)])
        return obs
    
    def gen_reward(self, tab, result):
        if self.episode_inc == 0 or self.episode_inc == 1:
            reward = 0
        else:
            reward = result - self.tabscores[tab][-1]
            if result >= 0.7: reward += 0.01   
        return reward                

    def getGoal(self):
        if self.goal_state == 0:
            goal = [490, 510]
        elif self.goal_state == 1:
            goal = [135, 1060]            
        elif self.goal_state == 2:
            goal = [490, 510]
        elif self.goal_state == 3:
            goal = [583, 1060]
        return goal
    
    def update_stats(self, score, delay, tab, now):
        self.tabscores[tab].append(score)
        self.scores.append(score)
        self.delays.append(delay)
        self.tabs.append(tab)
        self.times.append(now().strftime("%Y-%m-%d %H:%M:%S"))
            
    def log_results(self):
        # Dataframes for scores & timestamps
        column_names = ["score", "delay", "tabs", "time"]
        self.df = pd.DataFrame(columns = column_names)
        df = pd.DataFrame({'score': self.scores, 'delay': self.delays, 'tabs': self.tabs, 'time': self.times})
        file_path = os.path.join(file_dir, csv_folder, 'piecewiseA-'+self.hour+'.csv')
        df.to_csv(file_path, index=False)
    
    def getScores(self):
        return(self.scores)