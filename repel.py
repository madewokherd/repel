# Copyright 2011 Vincent Povirk
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import random

import pygame
from pygame.locals import *

PRECISION = 32

class Object(object):
    x = 0
    y = 0
    dx = 0
    dy = 0
    
    radius = 16 << PRECISION
    
    def sort_key(self):
        return (self.x, self.y)

class Player(Object):
    radius = 16 << PRECISION
    
    pull = 8 << PRECISION

class Bullet(Object):
    radius = 2 << PRECISION
    
    pull = 1 << PRECISION

class World(object):
    def __init__(self, width, height):
        self.bullets = []
        self.players = []
        self.baddies = []
        
        self.width = width
        self.height = height
        
        self.random = random.Random()
        
    def advance(self):
        # check for collisions
        
        # move all the bullets
        for player in self.players:
            for bullet in self.bullets:
                distance_squared = (bullet.x - player.x)**2 + (bullet.y - player.y)**2
                
                pull = player.pull * bullet.pull
                
                ax = (bullet.x - player.x) * pull // distance_squared
                ay = (bullet.y - player.y) * pull // distance_squared
                
                bullet.dx += ax
                bullet.dy += ay

        for bullet in self.bullets:
            bullet.x += bullet.dx
            bullet.y += bullet.dy
        
        # move all the baddies
        
        pass

def draw_world(world, surface, x, y, w, h):
    surface.fill(Color(0,0,0,255), Rect(x, y, w, h))
    
    for player in world.players:
        px = player.x * w // world.width + x
        py = player.y * h // world.height + y
        pr = player.radius * w // world.width
        pygame.draw.circle(surface, Color(255,0,0,255), (px, py), pr)
    
    for bullet in world.bullets:
        bx = bullet.x * w // world.width + x
        by = bullet.y * h // world.height + y
        br = bullet.radius * w // world.width
        pygame.draw.circle(surface, Color(255,128,128,255), (bx, by), br)

def run(world, player, x, y, w, h):
    screen = pygame.display.get_surface()
    clock = pygame.time.Clock()
    frame = 0

    pygame.mouse.set_visible(False)

    while True:
        clock.tick(60)
        frame += 1
        
        for event in pygame.event.get():
            if event.type == QUIT:
                return
            elif event.type == MOUSEMOTION:
                player.x = event.pos[0] << PRECISION
                player.y = event.pos[1] << PRECISION
        
        if frame % 20 == 0:
            bullet = Bullet()
            bullet.x = world.random.randint(0, w - 1) << PRECISION
            bullet.y = world.random.randint(0, h - 1) << PRECISION
            world.bullets.append(bullet)
        
        world.advance()
        draw_world(world, screen, x, y, w, h)
        pygame.display.flip()

def main():
    width = 640
    height = 640

    pygame.display.set_mode((width, height))
    
    world = World(width << PRECISION, height << PRECISION)

    player = Player()
    player.y = player.x = 320 << PRECISION
    world.players.append(player)

    run(world, player, 0, 0, width, height)

if __name__ == '__main__':
    main()

