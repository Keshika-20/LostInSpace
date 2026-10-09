def choose_target(resources, position, energy, move_cost=0.7):
    candidates=[]
    for res in resources:
        if res.collected: continue
        distance=abs(res.position[0]-position[0])+abs(res.position[1]-position[1])
        if energy > (distance+4)*move_cost:
            score=res.value/(distance+3) + res.data_size*0.15
            candidates.append((score,res))
    return max(candidates,key=lambda x:x[0])[1] if candidates else None
