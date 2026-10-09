from simulation.environment import Environment
from simulation.exploration_map import ExplorationMap
from simulation.models import RoverState
from simulation.rover import Rover
from mission.mission_controller import MissionController

def test_stage_1_to_5_objects_integrate():
    env=Environment(24,24,seed=17); known=ExplorationMap(env); state=RoverState(position=env.base); known.observe(env,state.position,4); rover=Rover(env,state,known); controller=MissionController(env,rover,known)
    assert state.position==env.base and known.coverage>0
    out=controller.step(); assert out['ok'] is True
    assert 0<=state.energy<=100
