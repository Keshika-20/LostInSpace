class Rover:
    def __init__(self, environment, state, exploration_map, move_cost=0.7):
        self.environment,self.state,self.exploration_map=environment,state,exploration_map
        self.move_cost=move_cost
    def move_to(self, destination):
        r,c=self.state.position; nr,nc=destination
        if abs(r-nr)+abs(c-nc)!=1: return False, "Move must be one adjacent cell."
        if not self.environment.traversable(destination): return False, "Blocked terrain or map boundary."
        if self.state.energy < self.move_cost: return False, "Insufficient energy."
        self.state.position=destination; self.state.energy=max(0,self.state.energy-self.move_cost); self.state.moves+=1
        self.exploration_map.observe(self.environment,destination)
        return True, "Movement complete."
