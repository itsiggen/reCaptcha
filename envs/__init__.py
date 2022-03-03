from gym.envs.registration import register
import gym

for env in list(gym.envs.registry.env_specs):
     if 'piecewiseA-v0' in env:
          del gym.envs.registry.env_specs[env]
          
for env in list(gym.envs.registry.env_specs):
     if 'bezierA-v0' in env:
          del gym.envs.registry.env_specs[env]

for env in list(gym.envs.registry.env_specs):
     if 'bezierB-v0' in env:
          del gym.envs.registry.env_specs[env]

for env in list(gym.envs.registry.env_specs):
     if 'abstractB-v0' in env:
          del gym.envs.registry.env_specs[env]
          
for env in list(gym.envs.registry.env_specs):
     if 'abstractC-v0' in env:
          del gym.envs.registry.env_specs[env]

register(
        id='piecewiseA-v0',
        entry_point='envs.piecewiseA:piecewiseA',
        )

register(
        id='bezierA-v0',
        entry_point='envs.bezierA:bezierA',
        )

register(
        id='bezierB-v0',
        entry_point='envs.bezierB:bezierB',
        )

register(
        id='abstractB-v0',
        entry_point='envs.abstractB:abstractB',
        )

register(
        id='abstractC-v0',
        entry_point='envs.abstractC:abstractC',
        )