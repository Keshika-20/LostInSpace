from simulation.environment import Environment
from simulation.exploration_map import ExplorationMap
from simulation.models import RoverState
from simulation.rover import Rover

def test_move_deducts_energy_once_and_invalid_move_does_not():
    env=Environment(12,12,seed=8); m=ExplorationMap(env); m.observe(env,env.base,3); s=RoverState(position=env.base); rover=Rover(env,s,m)
    before=s.energy; p=s.position
    ok,_=rover.move_to((p[0]+1,p[1]))
    if ok: assert s.energy==before-rover.move_cost
    else: assert s.position==p and s.energy==before
    before=s.energy; p=s.position; ok,_=rover.move_to((p[0]+2,p[1]))
    assert not ok and s.position==p and s.energy==before
