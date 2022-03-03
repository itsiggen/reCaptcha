import gym
import os
import numpy as np
import pandas as pd
from random import randrange, choice, uniform
from bezier import traject
from gym import spaces
import pyautogui as ag
import requests
import datetime
import random
import time

# Global environment definitializeions

FPS = 50
ag.PAUSE = 0 # Sets a pause after each PyAutoGUI call
file_dir = os.getcwd()
csv_folder = 'storage'
ag.FAILSAFE = False

class bezierA(gym.Env):
    def __init__(self, max_req=100):
        self.action_space = spaces.Box(low=-2, high=2, shape=(4,), dtype=np.float32)
        self.observation_space = spaces.Box(low=0, high=1, shape=(22,), dtype=np.float32)
        self.hour = datetime.datetime.now().strftime("%Y-%m-%d-%H")
        self.episodes = 0
        self.tab = 0
        self.max_req = max_req
        self.scores = []
        self.durations = []
        self.hovers = []  
        self.presses = []
        self.delays = []
        self.tabs = []
        self.subpages = []
        self.times = []
        self.rewards = []
        
    def reset(self):
        self.episodes += 1
        self.tabscores = [[], []]
        hover = uniform(0.2, 0.5)
        press = uniform(0.08, 0.12)
        if self.tab == 1:
            x, y = self.get_coords(0)
            traject(x, y, 1)
            self.wait_press(hover, press)
            self.tab = 0
        x, y = self.get_coords(2)
        traject(x, y, 1)
        self.wait_press(hover, press)
        # Number of low scores
        self.lows = 0
        # Get baseline score
        self.base = self.get_score()
        now = datetime.datetime.now()
        self.tabscores[self.tab].append(self.base)
        self.update_stats(self.base, 1, hover, press, 0, self.tab, now)
        self.done = False
        
        # Score requests count
        self.requests = 0
        # Next tab
        self.next = 1
        
        # Return first observation
        obs = self.gen_obs(now)
        return obs
    
    def step(self, action):
        self.requests += 1
        # Scale actions to appropriate range
        duration = self.scale_duration(action[0])
        hover = self.scale_hover(action[1])
        press = self.scale_press(action[2])
        delay = self.scale_delay(action[3])
        start = time.time()
        # Wait
        time.sleep(delay)
        # Change tab
        self.change_tab(duration, hover, press)
        self.initialize(duration)
        time.sleep(1)
        
        # Request score
        x, y = self.get_coords(2)
        traject(x, y, duration)
        self.wait_press(hover, press)
        self.score = self.get_score()
        # Decide next tab
        self.next = 0 if random.random() < .5 else 1
        
        # Generate new observation and reward
        self.tabscores[self.tab].append(self.score)
        reward = self.gen_reward()
        now = datetime.datetime.now()
        # Compute total delay
        delay = time.time() - start
        self.update_stats(self.score, duration, hover, press, delay, self.tab, now)
        obs = self.gen_obs(now)
        self.log_results()

        if self.requests >= (self.max_req-1):
            self.done = True
            self.log_results()
            time.sleep(10) # wait before next episode
        
        return obs, reward, self.done, {}
     
    def gen_obs(self, now):
        obs = []
        if len(self.tabs) < 10:
            tabs = [0] * (10 - len(self.tabs))
            tabs.extend(self.tabs)
        else:
            tabs = self.tabs[-10:]
        if len(self.tabscores[self.tab]) < 10:
            scores = [0] * (10 - len(self.tabscores[self.tab]))
            scores.extend(self.tabscores[self.tab])
        else:
            scores = self.tabscores[self.tab][-10:]
        obs.extend(tabs)
        obs.extend(scores)
        obs.append(self.requests/self.max_req)
        obs.append((now.hour*60 + now.minute)/1440)
        obs = np.array([obs], dtype='float32')
        return obs
    
    def gen_reward(self):
        # Reward is improvement on moving average of scores
        avg = sum(self.tabscores[self.tab]) / len(self.tabscores[self.tab])
        return self.score - avg
    
    def scale_duration(self, v):
        # Duration: [0.5, 1.5]
        return (v + 4) / 4

    def scale_hover(self, v):
        # Hover: [0.2, 1.1]
        return (v + 2.4) / 4

    def scale_press(self, v):
        # Press: [0.05, 0.55]
        return ((v + 2) / 8) + 0.05
    
    def scale_delay(self, v):
        # Delay: [2, 10]
        return (v + 2) * 2 + 2 
    
    def wait_press(self, hover, press):
        time.sleep(hover)
        ag.mouseDown()
        time.sleep(press)
        ag.mouseUp()
        
    def change_tab(self, duration, hover, press):
        if self.tab == 0:
            if self.next == 0:
                x, y = self.get_coords(0)
                traject(x, y, duration)
                ag.click()
                ag.click()
            elif self.next == 1:
                x, y = self.get_coords(1)
                traject(x, y, duration)
                ag.click()
                self.tab = 1
        elif self.tab == 1:
            if self.next == 0:
                x, y = self.get_coords(0)
                traject(x, y, duration)
                ag.click()
                self.tab = 0
            elif self.next == 1:
                x, y = self.get_coords(1)
                traject(x, y, duration)
                ag.click()
                ag.click()
                    
    def get_score(self):
        time.sleep(uniform(0.8, 1))
        try:
            r = requests.get("http://localhost:5000/alterego/result")
            result = r.json()["score"]
        except:
            print("Server returned no score")
            result = 0
        if result < 0.5: self.lows += 1
        return result

    def get_coords(self, loc):
        if loc == 0:
            goal = [583, 1060]
        elif loc == 1:
            goal = [135, 1060]            
        elif loc == 2:
            goal = [490, 510]
        elif loc == 3:
            goal = [490, 510]
        return goal[0], goal[1]
            
    def initialize(self, duration):
        a = choice([(100,300),(1000,1200)])
        b = choice([(200,400),(600,800)])
        traject(randrange(*a), randrange(*b), duration)
            
    def update_stats(self, score, duration, hover, press, delay, tab, now):
        self.tabscores[tab].append(score)
        self.scores.append(score)
        self.durations.append(duration)
        self.hovers.append(hover)
        self.presses.append(press)
        self.delays.append(delay)
        self.tabs.append(tab)
        self.times.append(now.strftime("%Y-%m-%d %H:%M:%S"))
    
    def log_results(self):
        # Dataframes for scores & timestamps
        column_names = ["score", "duration", "hover", "press", "delay", "tabs", "time"]
        self.df = pd.DataFrame(columns = column_names)
        df = pd.DataFrame({'score': self.scores, 'duration': self.durations, 'hover': self.hovers, \
                           'press': self.presses, 'delay': self.delays, 'tabs': self.tabs, 'time': self.times})
        file_path = os.path.join(file_dir, csv_folder, 'bezierA-'+self.hour+'.csv')
        df.to_csv(file_path, index=False)

    def getScores(self):
        return(self.scores)