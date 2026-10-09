class ExplorationMap:
    def __init__(self, environment):
        self.rows,self.cols=environment.rows,environment.cols
        self.known=[[None for _ in range(self.cols)] for _ in range(self.rows)] # None unknown; 0 open; 1 obstacle
        self.resources={}
        self.base=environment.base
    def observe(self, environment, position, radius=3):
        r0,c0=position
        for r in range(max(0,r0-radius),min(self.rows,r0+radius+1)):
            for c in range(max(0,c0-radius),min(self.cols,c0+radius+1)):
                if (r-r0)**2+(c-c0)**2 <= radius*radius:
                    self.known[r][c]=environment.grid[r][c]
                    for item in environment.resources:
                        if item.position==(r,c):
                            item.discovered=True
                            self.resources[item.position]=item
    def is_known(self,p): return self.known[p[0]][p[1]] is not None
    def traversable(self,p): return self.is_known(p) and self.known[p[0]][p[1]]==0
    @property
    def explored_count(self): return sum(x is not None for row in self.known for x in row)
    @property
    def coverage(self): return 100*self.explored_count/(self.rows*self.cols)
