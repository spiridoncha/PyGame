#/usr/bin/env python
# coding: utf

import math
import pygame
import random
import itertools

SIZE = 640, 480

def intn(*arg):
    return map(int,arg)

def Init(sz):
    '''Turn PyGame on'''
    global screen, screenrect
    pygame.init()
    screen = pygame.display.set_mode(sz)
    screenrect = screen.get_rect()

class GameMode:
    '''Basic game mode class'''
    def __init__(self):
        self.background = pygame.Color("black")

    def Events(self,event):
        '''Event parser'''
        pass

    def Draw(self, screen):
        screen.fill(self.background)

    def Logic(self, screen):
        '''What to calculate'''
        pass

    def Leave(self):
        '''What to do when leaving this mode'''
        pass

    def Init(self):
        '''What to do when entering this mode'''
        pass

class Ball:
    '''Simple ball class'''

    def __init__(self, filename, pos = (0.0, 0.0), speed = (0.0, 0.0)):
        '''Create a ball from image'''
        self.fname = filename
        self.surface = pygame.image.load(filename)
        self.rect = self.surface.get_rect()
        self.speed = speed
        self.pos = pos
        self.newpos = pos
        self.active = True

    def draw(self, surface):
        surface.blit(self.surface, self.rect)

    def action(self):
        '''Proceed some action'''
        if self.active:
            self.pos = self.pos[0]+self.speed[0], self.pos[1]+self.speed[1]

    def logic(self, surface):
        x,y = self.pos
        dx, dy = self.speed
        if x < self.rect.width/2:
            x = self.rect.width/2
            dx = -dx
        elif x > surface.get_width() - self.rect.width/2:
            x = surface.get_width() - self.rect.width/2
            dx = -dx
        if y < self.rect.height/2:
            y = self.rect.height/2
            dy = -dy
        elif y > surface.get_height() - self.rect.height/2:
            y = surface.get_height() - self.rect.height/2
            dy = -dy
        self.pos = x,y
        self.speed = dx,dy
        self.rect.center = intn(*self.pos)

class RotateBall(Ball):
    '''Rotate Ball class'''

    def __init__(self, filename, pos = (0.0, 0.0), speed = (0.0, 0.0), angle = 90, scale = 1):
        '''Create a ball from image'''
        Ball.__init__(self, filename, pos, speed)
        x, y = self.surface.get_size()
        self.rect = self.surface.get_rect()
        self.angle = angle
        self.scale = scale
        self.mask = pygame.mask.from_surface(self.surface).scale((int(scale*x), int(scale*y)))
        self.surface = pygame.transform.scale(self.surface, (int(scale*x), int(scale*y)))
        self.mass = scale

    def action(self):
        if self.active:
            if random.random() > 0.3:
                self.surface = pygame.transform.rotate(self.surface, self.angle)
            self.rect = self.surface.get_rect(center=self.rect.center)
            self.pos = self.pos[0]+self.speed[0], self.pos[1]+self.speed[1]


class Universe:
    '''Game universe'''

    def __init__(self, msec, tickevent = pygame.USEREVENT):
        '''Run a universe with msec tick'''
        self.msec = msec
        self.tickevent = tickevent

    def Start(self):
        '''Start running'''
        pygame.time.set_timer(self.tickevent, self.msec)

    def Finish(self):
        '''Shut down an universe'''
        pygame.time.set_timer(self.tickevent, 0)

class GameWithObjects(GameMode):

    def __init__(self, objects=[]):
        GameMode.__init__(self)
        self.objects = objects

    def locate(self, pos):
        return [obj for obj in self.objects if obj.rect.collidepoint(pos)]

    def Events(self, event):
        GameMode.Events(self, event)
        if event.type == Game.tickevent:
            for obj in self.objects:
                obj.action()

    def Logic(self, surface):
        GameMode.Logic(self, surface)
        for obj in self.objects:
            obj.logic(surface)

    def Draw(self, surface):
        GameMode.Draw(self, surface)
        for obj in self.objects:
            obj.draw(surface)

class GameWithDnD(GameWithObjects):

    def __init__(self, *argp, **argn):
        GameWithObjects.__init__(self, *argp, **argn)
        self.oldposInBall = False
        self.drag = None

    def itIsRotateBall(self, pos):
        for i in self.objects:
            try:
                if i.mask.get_at((pos[0] - i.rect.topleft[0], pos[1] - i.rect.topleft[1])):
                    return True
            except:
                pass
        return False

    def Events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            click = self.locate(event.pos)
            self.oldposInBall = False
            if click and self.itIsRotateBall(event.pos):
                self.drag = click[0]
                self.oldposInBall = True
                self.drag.active = False
        elif event.type == pygame.MOUSEMOTION and event.buttons[0]:
            if self.drag:
                self.drag.pos = event.pos
                self.drag.speed = event.rel
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            click = self.locate(event.pos)
            if click and self.oldposInBall:
                self.drag.active = True
                self.drag = None
        GameWithObjects.Events(self, event)

class GameWithDnDAndGravityAndContact(GameWithDnD):
    def Events(self, event):
        for obj in self.objects:
            if obj.active and event.type == Game.tickevent:
                obj.speed = (obj.speed[0], obj.speed[1] + 0.5) 
        GameWithDnD.Events(self, event)

    def Logic(self, surface):
        #contact
        for obj in itertools.combinations(self.objects, 2):
            doff0 = obj[0].mask.centroid()[0] - obj[1].mask.centroid()[0]
            doff1 = obj[0].mask.centroid()[1] - obj[1].mask.centroid()[1]
            boff0 = obj[0].pos[0] - obj[1].pos[0]
            boff1 = obj[0].pos[1] - obj[1].pos[1]
            offset = (int(doff0 + boff0), int(doff1 + boff1))
            if obj[0].mask.overlap_area(obj[1].mask, offset):
                theta = math.atan2(obj[0].pos[1] - obj[1].pos[1], obj[0].pos[0] - obj[1].pos[0])
                cosTheta = math.cos(theta)
                sinTheta = math.sin(theta)
                x0_new = (obj[0].speed[0]*cosTheta + obj[0].speed[1]*sinTheta)
                y0_new = (obj[0].speed[1]*cosTheta - obj[0].speed[0]*sinTheta)
                x1_new = (obj[1].speed[0]*cosTheta + obj[1].speed[1]*sinTheta)
                y1_new = (obj[1].speed[1]*cosTheta - obj[1].speed[0]*sinTheta)
                v0 = (obj[0].mass - obj[1].mass)*x0_new + 2*obj[1].mass*x1_new 
                v1 = 2*obj[0].mass*x0_new + (obj[1].mass - obj[0].mass)*x1_new
                x0_new = v0/(obj[0].mass + obj[1].mass)
                x1_new = v1/(obj[0].mass + obj[1].mass)
                obj[0].speed = (x0_new*cosTheta - y0_new*sinTheta), (y0_new*cosTheta + x0_new*sinTheta)
                obj[1].speed = (x1_new*cosTheta - y1_new*sinTheta), (y1_new*cosTheta + x1_new*sinTheta)
                obj[0].pos = (obj[0].pos[0] + obj[0].speed[0], obj[0].pos[1] + obj[0].speed[1])
                obj[1].pos = (obj[1].pos[0] + obj[1].speed[0], obj[1].pos[1] + obj[1].speed[1])
        GameWithDnD.Logic(self, surface)

Init(SIZE)
Game = Universe(50)

Run = GameWithDnDAndGravityAndContact()
for i in xrange(5):
    x, y = random.randrange(screenrect.w), random.randrange(screenrect.h)
    dx , dy = 0, 0
    angle = 90
    scale = 0.3 + random.random()
    Run.objects.append(RotateBall("ball.gif", (x,y), (dx,dy), angle, scale))

Game.Start()
Run.Init()
again = True
while again:
    event = pygame.event.wait()
    if event.type == pygame.QUIT:
        again = False
    Run.Events(event)
    Run.Logic(screen)
    Run.Draw(screen)
    pygame.display.flip()
Game.Finish()
pygame.quit()
