"""
Particle systems and Starfield effects for Gravity Station.
"""

import pygame
import random
import math

class Particle:
    def __init__(self, x, y, vx, vy, color, lifetime, size=2, fade=True):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.max_lifetime = lifetime
        self.lifetime = lifetime
        self.size = size
        self.fade = fade

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        return self.lifetime > 0

    def draw(self, surface):
        if self.lifetime <= 0:
            return
        alpha = int(255 * (self.lifetime / self.max_lifetime)) if self.fade else 255
        s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        col = (self.color[0], self.color[1], self.color[2], alpha)
        pygame.draw.circle(s, col, (self.size, self.size), self.size)
        surface.blit(s, (int(self.x - self.size), int(self.y - self.size)))

class ParticleManager:
    def __init__(self):
        self.particles = []

    def add_gravity_flip_burst(self, x, y, direction):
        # Direction: 1 = to ceiling, -1 = to floor
        colors = [(50, 220, 255), (255, 140, 40), (255, 255, 255)]
        for _ in range(18):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1.5, 4.5)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - (direction * 2.0)
            c = random.choice(colors)
            life = random.randint(15, 30)
            self.particles.append(Particle(x, y, vx, vy, c, life, size=random.randint(2, 3)))

    def add_jump_dust(self, x, y, gravity_dir):
        # Dust puffs on jump
        for _ in range(8):
            vx = random.uniform(-2.0, 2.0)
            vy = random.uniform(0.2, 1.5) * gravity_dir
            life = random.randint(10, 20)
            self.particles.append(Particle(x, y, vx, vy, (140, 160, 190), life, size=2))

    def add_switch_spark(self, x, y):
        for _ in range(12):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1.0, 3.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            life = random.randint(12, 25)
            self.particles.append(Particle(x, y, vx, vy, (50, 240, 120), life, size=2))

    def add_laser_sparks(self, x, y):
        for _ in range(3):
            vx = random.uniform(-1.5, 1.5)
            vy = random.uniform(-1.5, 1.5)
            life = random.randint(6, 14)
            self.particles.append(Particle(x, y, vx, vy, (255, 60, 70), life, size=2))

    def add_death_explosion(self, x, y):
        colors = [(255, 60, 70), (255, 180, 50), (255, 255, 255), (90, 100, 130)]
        for _ in range(35):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2.0, 6.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            c = random.choice(colors)
            life = random.randint(25, 45)
            self.particles.append(Particle(x, y, vx, vy, c, life, size=random.randint(2, 4)))

    def update_and_draw(self, surface):
        alive_particles = []
        for p in self.particles:
            if p.update():
                p.draw(surface)
                alive_particles.append(p)
        self.particles = alive_particles

class Starfield:
    def __init__(self, width, height, num_stars=70):
        self.width = width
        self.height = height
        self.stars = []
        for _ in range(num_stars):
            x = random.randint(0, width)
            y = random.randint(0, height)
            speed = random.uniform(0.1, 0.4)
            brightness = random.randint(80, 220)
            size = 1 if speed < 0.25 else 2
            self.stars.append([x, y, speed, brightness, size])

    def update_and_draw(self, surface):
        for s in self.stars:
            s[0] -= s[2] # slow drift left
            if s[0] < 0:
                s[0] = self.width
                s[1] = random.randint(0, self.height)
            b = s[3]
            color = (b, b, min(255, b + 30))
            if s[4] == 1:
                surface.set_at((int(s[0]), int(s[1])), color)
            else:
                pygame.draw.rect(surface, color, (int(s[0]), int(s[1]), 2, 2))
