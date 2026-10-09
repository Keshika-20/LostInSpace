from heapq import heappush, heappop

def find_path(start, goal, known_map):
    """A* path over explored traversable cells only; path includes start and goal."""
    if start==goal: return [start]
    rows,cols=known_map.rows,known_map.cols
    def ok(p): return 0<=p[0]<rows and 0<=p[1]<cols and known_map.traversable(p)
    if not ok(start) or not ok(goal): return None
    q=[]; heappush(q,(0,start)); came={}; cost={start:0}
    while q:
        _,cur=heappop(q)
        if cur==goal:
            path=[cur]
            while cur in came: cur=came[cur]; path.append(cur)
            return path[::-1]
        for nxt in ((cur[0]-1,cur[1]),(cur[0]+1,cur[1]),(cur[0],cur[1]-1),(cur[0],cur[1]+1)):
            if not ok(nxt): continue
            new=cost[cur]+1
            if new<cost.get(nxt,10**9):
                came[nxt]=cur; cost[nxt]=new
                h=abs(goal[0]-nxt[0])+abs(goal[1]-nxt[1]); heappush(q,(new+h,nxt))
    return None
