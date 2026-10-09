import pygame
from ui import theme

class Dashboard:
    def __init__(self): self.logs=["LANDER TELEMETRY LINK ESTABLISHED","LOCAL TERRAIN SCAN COMPLETE","AUTONOMOUS NAVIGATION READY"]
    def log(self,message):
        self.logs.append(message.upper()); self.logs=self.logs[-5:]
    def _panel(self,screen,rect,title,font):
        pygame.draw.rect(screen,theme.PANEL,rect,border_radius=7); pygame.draw.rect(screen,theme.BORDER,rect,1,border_radius=7)
        screen.blit(font.render(title,True,theme.CYAN),(rect.x+12,rect.y+9))
        pygame.draw.line(screen,theme.BORDER,(rect.x+12,rect.y+32),(rect.right-12,rect.y+32),1)
    def draw(self,screen,font,small,state,known_map,controller,rects,paused):
        # Telemetry card
        r=rects['telemetry']; self._panel(screen,r,'ROVER TELEMETRY',font)
        values=[('POWER RESERVE',f'{state.energy:05.1f} %',state.energy/100,theme.GREEN if state.energy>30 else theme.RED),('MAP COVERAGE',f'{known_map.coverage:05.1f} %',known_map.coverage/100,theme.CYAN),('SAMPLE CARGO',f'{state.carried_data:05.1f} MB',min(1,state.carried_data/100),theme.PURPLE)]
        y=r.y+44
        for label,value,ratio,color in values:
            screen.blit(small.render(label,True,theme.MUTED),(r.x+13,y)); v=small.render(value,True,theme.TEXT); screen.blit(v,(r.right-v.get_width()-13,y))
            bar=pygame.Rect(r.x+13,y+18,r.w-26,5); pygame.draw.rect(screen,(29,45,53),bar,border_radius=3); pygame.draw.rect(screen,color,(bar.x,bar.y,int(bar.w*max(0,min(1,ratio))),bar.h),border_radius=3); y+=44
        # Mission card
        r=rects['mission']; self._panel(screen,r,'MISSION / TARGET ACQUISITION',font)
        state_txt='PAUSED' if paused else state.mission_state
        screen.blit(font.render(state_txt,True,theme.AMBER if paused else theme.GREEN),(r.x+13,r.y+43))
        target=controller.target
        lines=[f'ROVER POSITION   {state.position[0]:02d} : {state.position[1]:02d}',
               f'ACTIVE TARGET    {target.name if target else "NONE IN KNOWN MAP"}',
               f'SCIENTIFIC VALUE {target.value:.1f}' if target else 'SCIENTIFIC VALUE --',
               f'DATA PAYLOAD     {target.data_size:.1f} MB' if target else 'DATA PAYLOAD     --',
               f'MOVEMENT CYCLES  {state.moves:04d}']
        y=r.y+70
        for line in lines:
            screen.blit(small.render(line[:42],True,theme.TEXT if y<r.y+135 else theme.MUTED),(r.x+13,y)); y+=20
        # Event log
        r=rects['events']; self._panel(screen,r,'FLIGHT DIRECTOR / EVENT STREAM',font)
        for i,line in enumerate(self.logs[-4:]):
            col=theme.GREEN if i==len(self.logs[-4:])-1 else theme.MUTED
            screen.blit(small.render(f'{i+1:02d}  {line[:46]}',True,col),(r.x+13,r.y+43+i*20))
        # Environment status
        r=rects['status']; self._panel(screen,r,'SURFACE CONDITIONS',font)
        for i,line in enumerate(['ATMOSPHERE  THIN CO₂','SURFACE TEMP  -63 °C','WIND GUSTS    18 km/h','TERRAIN       BASALT / REGOLITH']):
            screen.blit(small.render(line,True,theme.TEXT),(r.x+13,r.y+43+i*20))
