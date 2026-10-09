import pygame

class Controls:
    """UI emits intent strings only; simulation state is changed by main/controller."""
    def __init__(self):
        self.buttons={}; self.paused=True; self.speed=1
    def draw(self,screen,font,small_font,rect):
        pygame.draw.rect(screen,(10,22,30),rect,border_radius=8); pygame.draw.rect(screen,(48,83,99),rect,1,border_radius=8)
        title=font.render("MISSION CONTROLS",True,(71,210,232)); screen.blit(title,(rect.x+14,rect.y+10))
        specs=[("START / RESUME", "START"),("PAUSE SIMULATION","PAUSE"),("RESET MISSION","RESET"),("SCAN LOCAL AREA","SCAN"),("COLLECT AT SITE","COLLECT")]
        self.buttons={}; y=rect.y+43
        for label,action in specs:
            b=pygame.Rect(rect.x+12,y,rect.w-24,29); self.buttons[action]=b
            color=(20,48,60) if action not in ('RESET',) else (49,31,31)
            pygame.draw.rect(screen,color,b,border_radius=4); pygame.draw.rect(screen,(52,111,130),b,1,border_radius=4)
            t=small_font.render(label,True,(220,235,239)); screen.blit(t,t.get_rect(center=b.center)); y+=36
    def handle_event(self,event):
        if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            for action,rect in self.buttons.items():
                if rect.collidepoint(event.pos): return action
        if event.type==pygame.KEYDOWN:
            mapping={pygame.K_SPACE:'PAUSE',pygame.K_RETURN:'START',pygame.K_r:'RESET',pygame.K_TAB:'SCAN',pygame.K_e:'COLLECT'}
            return mapping.get(event.key)
        return None
