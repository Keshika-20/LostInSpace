from simulation.environment import Environment
from simulation.exploration_map import ExplorationMap

def test_seed_reproducibility():
    a,b=Environment(seed=23),Environment(seed=23)
    assert a.grid==b.grid
    assert [x.position for x in a.resources]==[x.position for x in b.resources]

def test_observation_reveals_local_area_only():
    env=Environment(20,20,seed=3); m=ExplorationMap(env); m.observe(env,(10,10),2)
    assert m.known[10][10] is not None
    assert m.known[0][0] is None

def test_map_coverage_bounded():
    env=Environment(12,12); m=ExplorationMap(env); m.observe(env,env.base,3)
    assert 0 < m.coverage < 100
