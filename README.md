# Space Invaders: A journey through the path of Atari's Games with Reinforcement Learnig

## Master's in Data Science and Engineering - Advanced Topics of Inteligent Systems

Author: Cátia Teixeira 


### Description

This work explores the intersection of classic video game adaptation, particularly focusing on Space Invaders, within the context of reinforcement learning (RL).

The implemented deep learning models are Dueling Deep Recurrent Q-Networks (DDRQN) and Dueling Deep Transformer Network (DDTN) with network improvements such as Prioritized Experience Replay (PER), Multi-Step Learning and Dueling Architecture itself.

The work also includes conclusions from initial trials with several parameters variation using a simpler Deep Recurrent Q-Network (DRQN). The results showed that both agents were able to learn over time and achieve an acceptable average score. DDRQN
achieved slightly better performance, but overall both agents evolution are very similar. 
Improvements to the network and memory depth of the agent were crucial in achieving these results.

- **Observation space:** The observation space consists of a sequence of encoded features extracted from raw frames using a CNN. Each frame passes through the CNN to produce a set of high-level features that represent the visual information
captured in that frame. These feature vectors then form a series of observations that serve as input.

- **Action space:** The formulated agent has 4 actions. In this sense, the spaceship being a two-dimensional shooter, the
possible actions are as follows:

  - Move left

  - Move right

  - Shoot bullet

  - Do nothing

- **Experiences:** Experiences are a tuple containing:
   
  - Initial State (Single frame)

  - Action

  - Reward

  - Final State (Single Frame)

  - Game Over Flag

### Instructions

0. All main files import game_v2.py and segment_tree.py
1. Open main_1.ipynb  and run all cells to try the DDRQN model
2. Open main_2.ipynb  and run all cells to try the DDTQN model
3. Open main_3.ipynb  and run all cells to try the reandom agent
