from simulation.environment import Environment
from simulation.exploration_map import ExplorationMap
from simulation.pathfinding import find_path

def test_path_start_goal_and_known_only():
    env=Environment(12,12,seed=2); m=ExplorationMap(env); m.observe(env,env.base,5)
    assert find_path(env.base,env.base,m)==[env.base]
    assert find_path(env.base,(0,0),m) is None

def test_path_is_adjacent_and_traversable():
    env=Environment(16,16,seed=4); m=ExplorationMap(env); m.observe(env,env.base,7)
    goal=next((r,c) for r in range(16) for c in range(16) if m.traversable((r,c)) and abs(r-env.base[0])+abs(c-env.base[1])==3)
    path=find_path(env.base,goal,m)
    assert path and path[0]==env.base and path[-1]==goal
    assert all(abs(a[0]-b[0])+abs(a[1]-b[1])==1 for a,b in zip(path,path[1:]))
