import math, random
import pygame
from ui import theme

class MapRenderer:
    """Large scrollable planetary atlas with procedural albedo, crater rims, rocks and HUD overlays."""
    def __init__(self, rows=48, cols=48, cell_size=19):
        self.rows,self.cols,self.cell_size=rows,cols,cell_size
        self.offset=(0,0); self._terrain={}
    def _terrain_color(self,r,c):
        key=(r,c)
        if key not in self._terrain:
            n=math.sin(r*.31+c*.17)*7 + math.cos(c*.28-r*.12)*5
            rng=random.Random(r*10007+c*191)
            n+=rng.uniform(-12,12)
            self._terrain[key]=(max(40,min(184,int(112+n))),max(24,min(115,int(66+n*.48))),max(18,min(84,int(46+n*.3))))
        return self._terrain[key]
    def draw(self,screen,rect,environment,known_map,state,controller,small_font):
        pygame.draw.rect(screen,(5,10,15),rect,border_radius=7); pygame.draw.rect(screen,theme.BORDER,rect,1,border_radius=7)
        title=small_font.render('TACTICAL SURFACE MAP  /  SECTOR 07',True,theme.CYAN); screen.blit(title,(rect.x+12,rect.y+9))
        view=pygame.Rect(rect.x+8,rect.y+31,rect.w-16,rect.h-77); pygame.draw.rect(screen,(13,20,24),view)
        cs=max(5,min(self.cell_size,(view.w-6)//min(self.cols,48),(view.h-6)//min(self.rows,48)))
        totalw=self.cols*cs; totalh=self.rows*cs
        ox=view.x+(view.w-totalw)//2; oy=view.y+(view.h-totalh)//2
        self.offset=(ox,oy); self.cell_size=cs
        for r in range(self.rows):
            for c in range(self.cols):
                x,y=ox+c*cs,oy+r*cs
                if x+cs<view.x or y+cs<view.y or x>view.right or y>view.bottom: continue
                known=known_map.known[r][c]
                if known is None: color=(11,20,25)
                elif known==1: color=(48,48,47)
                else: color=self._terrain_color(r,c)
                pygame.draw.rect(screen,color,(x,y,cs-1,cs-1))
                if known==1 and cs>=10:
                    pygame.draw.line(screen,(88,80,72),(x+2,y+2),(x+cs-3,y+cs-3),1)
                # Faint grid coordinates / mineral flecks keep map tactile rather than toy-like.
                if known==0 and cs>=12 and (r*7+c*13)%11==0:
                    pygame.draw.circle(screen,(191,119,76),(x+cs//2,y+cs//2),1)
        # Route behind markers.
        if controller.route and len(controller.route)>1:
            pts=[(ox+c*cs+cs//2,oy+r*cs+cs//2) for r,c in controller.route]
            pygame.draw.lines(screen,(27,41,49),False,pts,5); pygame.draw.lines(screen,theme.CYAN,False,pts,2)
        # Base
        br,bc=environment.base; bx,by=ox+bc*cs+cs//2,oy+br*cs+cs//2
        pygame.draw.circle(screen,theme.GREEN,(bx,by),max(4,cs//2),1); pygame.draw.rect(screen,(208,220,209),(bx-3,by-3,6,6))
        # Discovered resources only
        for pos,res in known_map.resources.items():
            r,c=pos; x,y=ox+c*cs+cs//2,oy+r*cs+cs//2
            col=theme.PURPLE if not res.collected else theme.MUTED
            pygame.draw.polygon(screen,col,[(x,y-cs//3),(x+cs//3,y),(x,y+cs//3),(x-cs//3,y)])
            if res.collected: pygame.draw.line(screen,(12,20,24),(x-2,y),(x+2,y),1)
        # Rover with chassis, wheels, sensor mast and direction cue.
        rr,cc=state.position; rx,ry=ox+cc*cs+cs//2,oy+rr*cs+cs//2
        wheel=max(2,cs//7)
        for dx in (-cs//4,cs//4):
            for dy in (-cs//4,cs//4): pygame.draw.circle(screen,(20,26,29),(rx+dx,ry+dy),wheel)
        pygame.draw.rect(screen,(207,218,218),(rx-cs//3,ry-cs//4,2*cs//3,cs//2),border_radius=2)
        pygame.draw.rect(screen,(60,85,91),(rx-cs//6,ry-cs//8,cs//3,cs//4),border_radius=1)
        pygame.draw.circle(screen,theme.CYAN,(rx,ry-cs//3),max(2,cs//8),1)
        pygame.draw.circle(screen,(240,250,255),(rx,ry),max(2,cs//8))
        # frame labels and legend
        coverage=f"COVERAGE {known_map.coverage:05.1f}%   |   {self.rows} × {self.cols} CELLS"
        screen.blit(small_font.render(coverage,True,theme.MUTED),(rect.x+12,rect.bottom-38))
        legend=[(theme.CYAN,'ROVER'),(theme.PURPLE,'SAMPLE'),((80,80,79),'ROCK'),(theme.GREEN,'BASE')]
        lx=rect.x+12
        for col,label in legend:
            pygame.draw.circle(screen,col,(lx+4,rect.bottom-15),4); screen.blit(small_font.render(label,True,theme.TEXT),(lx+13,rect.bottom-22)); lx+=90
