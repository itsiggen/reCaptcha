from PPO import PPO, Memory
from envs.piecewiseA import piecewiseA
from envs.bezierA import bezierA
from envs.bezierB import bezierB
from envs.abstractB import abstractB
from envs.abstractC import abstractC
import gym
import torch
import numpy as np
import os
import argparse

def main():
    """
    Parse input arguments
    """
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-env', default='bezierB-v0', type=str,
                        help='website environment to load')
    parser.add_argument('-train', default=True, type=bool,
                        help='train or test')
    parser.add_argument('-resume', default=True, type=bool,
                        help='resume previous training')
    parser.add_argument('-max_episodes', default=5, type=int,
                        help='max number of episodes')
    parser.add_argument('-max_steps', default=100, type=int,
                        help='max number of steps in an episode')
    parser.add_argument('-update', default=20, type=int,
                        help='steps until next policy update')
    parser.add_argument('-action_std', default=0.2, type=float,
                        help='the action distribution std')
    parser.add_argument('-epochs', default=80, type=int,
                        help='num of epochs for policy updates')
    parser.add_argument('-eps_clip', default=0.2, type=float,
                        help='PPO clip parameter')
    parser.add_argument('-gamma', default=0.9, type=float,
                        help='discount factor')
    parser.add_argument('-lr', default=0.0003, type=float,
                        help='learning rate')
    parser.add_argument('-seed', default=0, type=int,
                        help='PRNG seed')
    
    args = parser.parse_args()

    #############################################
    
    # Create environment
    env = gym.make(args.env, max_req=args.max_steps)
    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.shape[0]
    action_low = env.action_space.low
    action_high = env.action_space.high
    
    torch.manual_seed(args.seed)
    env.seed(args.seed)
    np.random.seed(args.seed)
    
    memory = Memory()
    betas = (0.9, 0.999)
    ppo = PPO(state_dim, action_dim, args.action_std, action_low, action_high,
              args.lr, betas, args.gamma, args.epochs, args.eps_clip)

    # logging variables
    episode_reward = 0
    step = 0
    
    # load old policy
    if args.resume and os.path.exists('./PPO_'+args.env+'.pt'):
        print("Loading previously saved model ... ")
        ppo.policy_old.load_state_dict(torch.load('./PPO_'+args.env+'.pt'))
        print("Loaded")
    
    # training loop
    for i_episode in range(1, args.max_episodes+1):
        state = env.reset()
        episode_reward = 0
        for t in range(args.max_steps):
            step +=1
            # Running policy_old:
            action = ppo.select_action(state, memory)
            state, reward, done, _ = env.step(action)
            
            # Saving reward and is_terminals:
            memory.rewards.append(reward)
            memory.is_terminals.append(done)
            
            # update if its time
            if step % args.update == 0:
                ppo.update(memory)
                memory.clear_memory()
                step = 0
            episode_reward += reward
            if done:
                break
        
        # if in training mode, save every 2 episodes
        if args.train and i_episode % 2 == 0:
            torch.save(ppo.policy.state_dict(), './PPO_'+args.env+'.pt')
            
        episode_reward = round(episode_reward/i_episode, 2)
        
        print('Episode {} \t Avg reward: {}'.format(i_episode, episode_reward))
        
if __name__ == '__main__':
    main()