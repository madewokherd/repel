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

PRECISION = 24
MAX_BULLET_RADIUS = 2 << PRECISION

def isqrt(n):
    if n < 0:
        raise ValueError("isqrt() is only valid for positive numbers")
    
    result = 0
    
    # find the closest power of 2
    to_add = n
    while True:
        next_to_add = to_add & (to_add - 1)
        if next_to_add == 0:
            break
        else:
            to_add = next_to_add
    
    while to_add != 0:
        next_result = result+to_add
        next_square = next_result * next_result
        if next_square < n:
            result = next_result
        elif next_square == n:
            return next_result
        to_add = to_add >> 1
    
    return result

class Object(object):
    x = 0
    y = 0
    dx = 0
    dy = 0
    dead = False
    
    radius = 16 << PRECISION
    
    def sort_key(self):
        return (self.x, self.y)

    def intersects(self, other):
        if self.dead or other.dead:
            return False
    
        max_distance_squared = (self.radius + other.radius)**2
        
        distance_squared = (self.x - other.x)**2 + (self.y - other.y)**2
        
        return max_distance_squared > distance_squared

class Player(Object):
    radius = 16 << PRECISION
    
    pull = 12 << PRECISION

class Bullet(Object):
    radius = 2 << PRECISION
    
    pull = 1 << PRECISION

class Baddie(Object):
    radius = 24 << PRECISION
    
    def move(self, world):
        pass

    def shoot_direction(self, world, dx, dy):
        bullet = Bullet()
        bullet.dx = dx
        bullet.dy = dy
        distance = self.radius + bullet.radius
        
        speed = isqrt(dx*dx + dy*dy)
        
        x_distance = distance * dx / speed + cmp(dx, 0)
        y_distance = distance * dy / speed + cmp(dy, 0)

        bullet.x = self.x + x_distance
        bullet.y = self.y + y_distance

        world.bullets.append(bullet)

        return bullet

    def shoot_point(self, world, x, y, speed):
        dx = x - self.x
        dy = y - self.y

        distance = isqrt(dx*dx + dy*dy)

        dx = dx * speed / distance
        dy = dy * speed / distance

        return self.shoot_direction(world, dx, dy)

class ShootyBaddie(Baddie):
    age = 0

    def move(self, world):
        self.age += 1
        
        if self.age % 60 == 0 and world.players:
            player = world.random.choice(world.players)
            bullet = self.shoot_point(world, player.x, player.y, 5 << PRECISION)
            bullet.pull = -bullet.pull
            bullet = self.shoot_point(world, player.x, player.y, 5 << PRECISION)

class World(object):
    def __init__(self, width, height):
        self.bullets = []
        self.players = []
        self.baddies = []
        
        self.width = width
        self.height = height
        
        self.random = random.Random()

    def find_bullet(self, obj):
        min_index = 0
        max_index = len(self.bullets)-1
        
        max_distance = obj.radius + MAX_BULLET_RADIUS
        
        min_x = obj.x - max_distance
        max_x = obj.x + max_distance
        
        # search for any bullet with x in range
        while max_index >= min_index:
            index = (max_index + min_index) // 2

            if min_x >= self.bullets[index].x:
                min_index = index + 1
            elif self.bullets[index].x < max_x: # and self.bullets[index]x > min_x
                break
            else: # max_x <= self.bullets[index].x
                max_index = index - 1
        else:
            # nothing with x in range
            return None
        
        if self.bullets[index].intersects(obj):
            return self.bullets[index]

        i = index-1
        while i >= 0 and self.bullets[i].x > min_x:
            if self.bullets[i].intersects(obj):
                return self.bullets[i]
            i -= 1
        
        i = index+1
        while i < len(self.bullets) and self.bullets[i].x < max_x:
            if self.bullets[i].intersects(obj):
                return self.bullets[i]
            i += 1
        
        return None
        
    def advance(self):
        # destroy any out of range or used bullets
        for i in range(len(self.bullets)-1, -1, -1):
            bullet = self.bullets[i]
            if bullet.dead or bullet.x < 0 or bullet.y < 0 or bullet.x > self.width or bullet.y > self.height:
                self.bullets.pop(i)

        # move all baddies (including shooting)
        for baddie in self.baddies:
            baddie.move(self)

        # check for collisions
        self.bullets.sort(key=Object.sort_key)
        
        for player in self.players:
            bullet = self.find_bullet(player)
            
            if bullet is not None:
                player.dead = True
                bullet.dead = True
                
        for baddie in self.baddies:
            bullet = self.find_bullet(baddie)
            
            if bullet is not None:
                baddie.dead = True
                bullet.dead = True
            else:
                for player in self.players:
                    if baddie.intersects(player):
                        baddie.dead = True
                        player.dead = True
                        break

        # destroy any dead players/baddies
        for i in range(len(self.players)-1, -1, -1):
            player = self.players[i]
            if player.dead:
                self.players.pop(i)

        for i in range(len(self.baddies)-1, -1, -1):
            baddie = self.baddies[i]
            if baddie.dead:
                self.baddies.pop(i)

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
        if player.pull > 0:
            color = Color(255,0,0,255)
        else:
            color = Color(0,0,255,255)
        pygame.draw.circle(surface, color, (px, py), pr)
    
    for bullet in world.bullets:
        if bullet.dead:
            continue
        bx = bullet.x * w // world.width + x
        by = bullet.y * h // world.height + y
        br = bullet.radius * w // world.width
        if bullet.pull > 0:
            color = Color(255,128,128,255)
        else:
            color = Color(128,128,255,255)
        pygame.draw.circle(surface, color, (bx, by), br)
    
    for baddie in world.baddies:
        if baddie.dead:
            continue
        bx = baddie.x * w // world.width + x
        by = baddie.y * h // world.height + y
        br = baddie.radius * w // world.width
        color = Color(162,162,162,255)
        pygame.draw.circle(surface, color, (bx, by), br)

def is_next_to_player(world, x, y):
    for player in world.players:
        if (x - player.x)**2 + (y-player.y)**2 < (100 << PRECISION) ** 2:
            return True
    return False

def run(world, player, x, y, w, h):
    screen = pygame.display.get_surface()
    clock = pygame.time.Clock()
    frame = 0
    paused = False

    pygame.mouse.set_visible(False)

    while True:
        if not paused:
            clock.tick(60)
            frame += 1
        
        events = pygame.event.get()
        
        if paused and not events:
            events = [pygame.event.wait()]
        
        for event in events:
            if event.type == QUIT:
                return
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    return
                elif event.key == K_PAUSE or event.key == K_p:
                    paused = not paused
            elif paused:
                continue
            elif event.type == MOUSEMOTION:
                player.x = event.pos[0] << PRECISION
                player.y = event.pos[1] << PRECISION
            elif event.type == MOUSEBUTTONDOWN and event.button == 1:
                player.pull = -player.pull
        
        if not paused:
            if frame % 200 == 0:
                baddie = ShootyBaddie()
                baddie.x = world.random.randint(0, w - 1) << PRECISION
                baddie.y = world.random.randint(0, h - 1) << PRECISION
                while is_next_to_player(world, baddie.x, baddie.y):
                    baddie.x = world.random.randint(0, w - 1) << PRECISION
                    baddie.y = world.random.randint(0, h - 1) << PRECISION
                world.baddies.append(baddie)
            
            world.advance()

        draw_world(world, screen, x, y, w, h)

        if paused:
            if pygame.font:
                font = pygame.font.Font(None, 48)
                text = font.render("Paused", 1, Color(240, 240, 240, 255))
                textpos = text.get_rect(centerx=x+w//2, centery=y+h//2)
                screen.blit(text, textpos)

        pygame.display.flip()

def main():
    width = 640
    height = 640

    pygame.init()

    pygame.display.set_mode((width, height))
    
    world = World(width << PRECISION, height << PRECISION)

    player = Player()
    player.y = player.x = 320 << PRECISION
    world.players.append(player)

    run(world, player, 0, 0, width, height)

if __name__ == '__main__':
    main()

