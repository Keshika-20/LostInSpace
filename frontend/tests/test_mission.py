from simulation.environment import Environment
from simulation.exploration_map import ExplorationMap
from simulation.models import RoverState
from simulation.rover import Rover
from mission.mission_controller import MissionController

def test_controller_returns_defined_result():
    env=Environment(20,20,seed=5); m=ExplorationMap(env); s=RoverState(position=env.base); m.observe(env,s.position,6); rover=Rover(env,s,m); c=MissionController(env,rover,m)
    result=c.step()
    assert isinstance(result,dict) and 'ok' in result and 'event' in result
