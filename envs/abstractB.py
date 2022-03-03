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
import time
import math

# Global environment definitions

FPS = 50
ag.PAUSE = 0 # Sets a pause after each PyAutoGUI call
file_dir = os.getcwd()
csv_folder = 'storage'
ag.FAILSAFE = False

class abstractB(gym.Env):
    def __init__(self, max_req=50, maxsteps=4):
        self.action_space = spaces.Box(low=-2, high=2, shape=(4,), dtype=np.float32)
        self.observation_space = spaces.Box(low=0, high=1, shape=(20,), dtype=np.float32)
        self.hour = datetime.datetime.now().strftime("%Y-%m-%d-%H")
        self.episodes = 0
        self.tab = 0
        self.maxsteps = maxsteps # max number of actions before query
        self.tries = 0
        self.chars = ['0', '1', '2', '3', '4', '5', '6', '7','8', '9', 'a', 'b', 
              'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n',
              'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'space']
        self.max_req = max_req
        self.scores = []
        self.acts = []
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
        self.tabacts = [[], []]
        hover = uniform(0.2, 0.5)
        press = uniform(0.08, 0.12)
        if self.tab == 1:
            x, y = self.get_coords(0)
            traject(x, y, 1)
            self.wait_press(hover, press)
            self.tab = 0
        sub = self.change_subpage(1, hover, press)
        self.pastsub = sub
        # Number of low scores
        self.lows = 0
        self.steps = 0
        # Get baseline score
        self.base = self.get_score(press)
        now = datetime.datetime.now()
        self.tabscores[self.tab].append(self.base)
        self.tabacts[self.tab].append(0)
        self.update_stats(self.base, 1, hover, press, 600, 0, self.tab, sub, 1, now)
        self.done = False

        # Score requests count
        self.requests = 0
        # Next tab
        self.next = 0

        # Return first observation
        obs = self.gen_obs(now)
        return obs
    
    def step(self, action):
        # Scale actions to appropriate range
        duration = self.scale_duration(action[0])
        hover = self.scale_hover(action[1])
        press = self.scale_press(action[2])
        select = self.select_act(action[3])
        start = time.time()

        # Change tab
        if self.steps == 0: self.change_tab(duration, hover, press)
        time.sleep(duration)
        # Act
        self.browse(select, duration, hover, press)
        self.score = 0
        reward = 0
        
        if self.steps >= self.maxsteps:
            self.requests += 1
            ag.press('home')
            self.sub = self.change_subpage(duration, hover, press)
            time.sleep(duration)
            x, y = self.get_coords(2)
            self.goclick(x, y, duration, hover, press)
            self.score = self.get_score(press)

            self.next = 1 if self.tab == 0 else 0
            self.tabscores[self.tab].append(self.score)
            reward = self.gen_reward()
            self.pastsub = self.sub

        now = datetime.datetime.now()
        delay = time.time() - start
        self.tabacts[self.tab].append(select)
        self.update_stats(self.score, duration, hover, press, delay, reward, self.tab, self.pastsub, select, now)
        obs = self.gen_obs(now)
        self.log_results()
        
        self.steps += 1
        if self.steps > self.maxsteps:
            self.steps = 0

        if self.requests >= (self.max_req-1):
            self.done = True
            time.sleep(10) # wait before next episode
        
        return obs, reward, self.done, {}

    def goclick(self, x, y, duration, hover, press):
        traject(x, y, duration)
        self.wait_press(uniform(hover-0.02, hover+0.02), uniform(press-0.01, press+0.01))
         
    def scroll(self, duration, hover, press):
        prs = choice([3,4])
        for i in range(prs):
            ag.scroll(-1)
            time.sleep(uniform(press/2,(press/2)+0.02))
        time.sleep(hover*2)
        for i in range(prs):
            ag.scroll(-1)
            time.sleep(uniform((press/2),(press/2)+0.02))
        time.sleep(duration*2)
        ag.press('home')
            
    def typing(self, duration, hover, press):
        x, y = self.get_coords(3)
        self.goclick(x, y, duration, hover, press)
        num = choice([5,7,9])
        for i in range(num):
            key = choice(self.chars)
            ag.keyDown(key)
            time.sleep(press/10 + 0.07)
            ag.keyUp(key)
            time.sleep(hover/10 + 0.1)           
        time.sleep(duration)
        num = choice([6,8,10])
        for i in range(num):
            key = choice(self.chars)
            ag.keyDown(key)
            time.sleep(press/10 + 0.07)
            ag.keyUp(key)
            time.sleep(hover/10 + 0.1)
            
    def browse(self, select, duration, hover, press):
        if select == 0:
            self.scroll(duration, hover, press)
        elif select == 1:
            self.typing(duration, hover, press)
        elif select == 2:
            x, y = self.get_coords(2)
            self.goclick(x, y , duration, hover, press)
        
    def gen_obs(self, now):
        # Generate the observation for the current step
        obs = []
        if len(self.tabscores[self.tab]) < 10:
            scores = [0] * (10 - len(self.tabscores[self.tab]))
            scores.extend(self.tabscores[self.tab])
        else:
            scores = self.tabscores[self.tab][-10:]

        acts = [0] * (7 - self.steps)
        acts.extend(self.tabacts[self.tab][-(self.steps+1):])
        acts = [x / 3 for x in acts]
        delay = self.delays[-1]

        obs.extend(scores)
        obs.extend(acts)
        obs.append(self.requests/self.max_req)
        obs.append(delay/30)
        obs = np.array([obs], dtype='float32')
        return obs
    
    def gen_reward(self):
        # Reward is the improvement on the moving average of scores
        if len(self.tabscores[self.tab]) == 0:
            avg = self.base
        else:
            avg = sum(self.tabscores[self.tab][:-2]) / len(self.tabscores[self.tab][:-2])
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
    
    def select_act(self, v):
        return math.floor((v + 2)/1.34)
    
    def wait_press(self, hover, press):
        time.sleep(hover)
        ag.mouseDown()
        time.sleep(press)
        ag.mouseUp()
        
    def change_tab(self, duration, hover, press):
        # Change the currently active browser tab
        if self.tab == 0:
            if self.next == 0:
                x, y = self.get_coords(0)
                traject(x, y, duration)
                ag.click()
                time.sleep(0.5)
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
                time.sleep(0.5)
                ag.click()
                    
    def get_score(self, press):
        # Request reCaptcha v3 verification
        time.sleep(uniform(1.5, 2.5))
        try:
            r = requests.get("http://localhost:8080/recaptcha/event")
            result = r.json()["grc"]
        except:
            print("Server returned no score")
            result = 0
        if not result and self.tries < 3:
            ag.mouseDown()
            time.sleep(press)
            ag.mouseUp()
            self.tries += 1
            result = self.get_score(press)
        self.tries = 0
        result = 0.5 if not result else result
        if result < 0.5: self.lows += 1
        return result

    def get_coords(self, loc):
        # Retrieve coordinates, hard-coded if viewport position is fixed or via
        # browser extension & and a local server for HTML elements
        if loc == 0:
            goal = [310, 1060]
        elif loc == 1:
            goal = [84, 1060]
        elif loc == 2:
            x = choice([(50,320),(1570,1870)])
            x = randrange(*x)
            y = randrange(170,1012)
            goal = [x, y]
        elif loc == 3:
            r = requests.get("http://localhost:8080/recaptcha/event")
            result = r.json()["form"]
            x = result["x"]
            y = result["y"]
            goal = [x, y]
        return goal[0], goal[1]
        
    def change_subpage(self, sub, duration, wait, press):
        # Change subpage within the website
        if sub == 0: sub = choice([1,2,3,4,5,6,7,8,9])
        r = requests.get("http://localhost:8080/recaptcha/event")
        result = r.json()["subs"]
        if sub == 1:
            coords = result["first"]
        elif sub == 2:
            coords = result["second"]
        elif sub == 3:
            coords = result["third"]
        elif sub == 4:
            coords = result["fourth"]
        elif sub == 5:
            coords = result["fifth"]
        elif sub == 6:
            coords = result["sixth"]
        elif sub == 7:
            coords = result["seventh"]
        elif sub == 8:
            coords = result["eighth"]
        elif sub == 9:
            coords = result["ninth"]   
        traject(coords["x"], coords["y"], duration)
        self.wait_press(wait, press)
        return sub
            
    def update_stats(self, score, duration, hover, press, delay, reward, tab, subpage, act, now):
        self.scores.append(score)
        self.durations.append(duration)
        self.hovers.append(hover)
        self.presses.append(press)
        self.delays.append(delay)
        self.rewards.append(reward)
        self.tabs.append(tab)
        self.subpages.append(subpage)
        self.acts.append(act)
        self.times.append(now.strftime("%Y-%m-%d %H:%M:%S"))
    
    def log_results(self):
        # Dataframes for scores & timestamps
        df = pd.DataFrame({'score': self.scores, 'duration': self.durations, 'hover': self.hovers,\
                           'press': self.presses, 'delay': self.delays, 'reward': self.rewards,\
                           'tabs': self.tabs, 'sub': self.subpages, 'acts': self.acts, 'time': self.times})
        file_path = os.path.join(file_dir, csv_folder, 'abstractB-'+self.hour+'.csv')
        df.to_csv(file_path, index=False)

    def getScores(self):
        return(self.scores)