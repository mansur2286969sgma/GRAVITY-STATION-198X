"""
Pixel Art and Texture Generator for Gravity Station.
Generates authentic retro 8-bit / 16-bit space station sprites and tiles.
"""

import pygame
import math

TILE_SIZE = 32

# Sci-Fi Retro Color Palette
COLOR_BLACK = (10, 10, 18)
COLOR_HULL_DARK = (34, 38, 54)
COLOR_HULL_MID = (58, 64, 88)
COLOR_HULL_LIGHT = (90, 100, 130)
COLOR_RIVET = (130, 140, 175)

COLOR_CYAN_GLOW = (50, 220, 255)
COLOR_CYAN_DIM = (20, 110, 150)
COLOR_ORANGE_GLOW = (255, 140, 40)
COLOR_ORANGE_DIM = (160, 70, 15)
COLOR_RED_ALARM = (255, 60, 70)
COLOR_GREEN_ACTIVE = (50, 240, 120)

COLOR_SUIT_WHITE = (230, 235, 245)
COLOR_SUIT_SHADOW = (160, 170, 195)
COLOR_VISOR_GOLD = (255, 200, 50)
COLOR_VISOR_SHINE = (255, 245, 180)


def create_hull_tile():
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill(COLOR_HULL_MID)

    # Beveled edges
    pygame.draw.line(surf, COLOR_HULL_LIGHT, (0, 0), (TILE_SIZE - 1, 0), 2)
    pygame.draw.line(surf, COLOR_HULL_LIGHT, (0, 0), (0, TILE_SIZE - 1), 2)
    pygame.draw.line(surf, COLOR_HULL_DARK, (0, TILE_SIZE - 1), (TILE_SIZE - 1, TILE_SIZE - 1), 2)
    pygame.draw.line(surf, COLOR_HULL_DARK, (TILE_SIZE - 1, 0), (TILE_SIZE - 1, TILE_SIZE - 1), 2)

    # Rivets in corners
    for rx, ry in [(4, 4), (TILE_SIZE - 5, 4), (4, TILE_SIZE - 5), (TILE_SIZE - 5, TILE_SIZE - 5)]:
        surf.set_at((rx, ry), COLOR_RIVET)
        surf.set_at((rx + 1, ry), COLOR_HULL_DARK)

    # Center metallic panel detail
    pygame.draw.rect(surf, COLOR_HULL_DARK, (8, 8, 16, 16), 1)
    pygame.draw.line(surf, COLOR_CYAN_DIM, (10, 16), (22, 16), 1)

    return surf


def create_hazard_tile():
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill(COLOR_HULL_DARK)
    # Yellow & Black hazard stripes
    for i in range(-TILE_SIZE, TILE_SIZE * 2, 8):
        pts = [(i, 0), (i + 4, 0), (i + 4 + TILE_SIZE, TILE_SIZE), (i + TILE_SIZE, TILE_SIZE)]
        pygame.draw.polygon(surf, (230, 180, 20), pts)
    pygame.draw.rect(surf, (20, 20, 20), (0, 0, TILE_SIZE, TILE_SIZE), 2)
    return surf


def create_spike_tile(upside_down=False):
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    spikes = 4
    w = TILE_SIZE / spikes
    for s in range(spikes):
        x1 = s * w
        x2 = (s + 0.5) * w
        x3 = (s + 1) * w
        if not upside_down:
            pts = [(x1, TILE_SIZE), (x2, 8), (x3, TILE_SIZE)]
        else:
            pts = [(x1, 0), (x2, TILE_SIZE - 8), (x3, 0)]
        pygame.draw.polygon(surf, COLOR_RED_ALARM, pts)
        # Inner highlight
        if not upside_down:
            pygame.draw.line(surf, (255, 180, 180), (x2, 10), (x2, TILE_SIZE - 2), 1)
        else:
            pygame.draw.line(surf, (255, 180, 180), (x2, 2), (x2, TILE_SIZE - 10), 1)
    return surf


def create_crate_sprite():
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill((65, 80, 110))
    pygame.draw.rect(surf, (110, 130, 170), (0, 0, TILE_SIZE, TILE_SIZE), 3)
    # Diagonal brace
    pygame.draw.line(surf, (40, 50, 75), (3, 3), (TILE_SIZE - 4, TILE_SIZE - 4), 2)
    pygame.draw.line(surf, (40, 50, 75), (TILE_SIZE - 4, 3), (3, TILE_SIZE - 4), 2)
    # Glowing anti-grav core symbol in center
    pygame.draw.circle(surf, COLOR_CYAN_DIM, (16, 16), 6)
    pygame.draw.circle(surf, COLOR_CYAN_GLOW, (16, 16), 3)
    return surf


def create_switch_sprites():
    # Unpressed (active / red light)
    unpressed = pygame.Surface((TILE_SIZE, 10), pygame.SRCALPHA)
    pygame.draw.rect(unpressed, COLOR_HULL_LIGHT, (2, 4, 28, 6), border_radius=2)
    pygame.draw.rect(unpressed, COLOR_RED_ALARM, (10, 1, 12, 4), border_radius=1)

    # Pressed (down / green light)
    pressed = pygame.Surface((TILE_SIZE, 10), pygame.SRCALPHA)
    pygame.draw.rect(pressed, COLOR_HULL_LIGHT, (2, 6, 28, 4), border_radius=2)
    pygame.draw.rect(pressed, COLOR_GREEN_ACTIVE, (10, 5, 12, 2), border_radius=1)

    return unpressed, pressed


def create_door_sprite(opened=False):
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE * 2), pygame.SRCALPHA)
    if not opened:
        # Closed blast door
        surf.fill((45, 52, 75))
        pygame.draw.rect(surf, (80, 95, 135), (0, 0, TILE_SIZE, TILE_SIZE * 2), 3)
        # Laser barrier grid
        for y in range(8, TILE_SIZE * 2 - 8, 10):
            pygame.draw.line(surf, COLOR_RED_ALARM, (4, y), (TILE_SIZE - 5, y), 2)
        # Central lock indicator
        pygame.draw.rect(surf, COLOR_RED_ALARM, (10, TILE_SIZE - 6, 12, 12), border_radius=2)
    else:
        # Open door frame (retracted)
        pygame.draw.rect(surf, COLOR_HULL_LIGHT, (0, 0, 6, TILE_SIZE * 2))
        pygame.draw.rect(surf, COLOR_HULL_LIGHT, (TILE_SIZE - 6, 0, 6, TILE_SIZE * 2))
        # Subtle green forcefield haze
        barrier = pygame.Surface((TILE_SIZE - 12, TILE_SIZE * 2 - 8), pygame.SRCALPHA)
        barrier.fill((50, 240, 120, 40))
        surf.blit(barrier, (6, 4))
    return surf


def create_portal_sprite(frame=0):
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE * 2), pygame.SRCALPHA)
    # Airlock pod frame
    pygame.draw.rect(surf, COLOR_HULL_LIGHT, (0, 0, TILE_SIZE, TILE_SIZE * 2), 2, border_radius=6)
    
    # Swirling vortex rings
    center_y = TILE_SIZE
    center_x = 16
    for r in range(12, 3, -3):
        color = COLOR_CYAN_GLOW if (r + frame) % 6 < 3 else COLOR_ORANGE_GLOW
        pygame.draw.ellipse(surf, color, (center_x - r, center_y - r * 1.6, r * 2, r * 3.2), 2)
    
    # Core glow
    pygame.draw.circle(surf, (255, 255, 255), (center_x, center_y), 3)
    return surf


def create_grav_orb_sprite(pulse_tick=0):
    surf = pygame.Surface((24, 24), pygame.SRCALPHA)
    scale = math.sin(pulse_tick * 0.1) * 2
    r = int(7 + scale)
    # Glowing outer corona
    pygame.draw.circle(surf, (255, 140, 40, 90), (12, 12), r + 3)
    pygame.draw.circle(surf, COLOR_ORANGE_GLOW, (12, 12), r)
    pygame.draw.circle(surf, (255, 240, 200), (12, 12), max(2, r - 3))
    # Orbiting dots
    angle = pulse_tick * 0.15
    ox = 12 + math.cos(angle) * (r + 2)
    oy = 12 + math.sin(angle) * (r + 2)
    pygame.draw.circle(surf, COLOR_CYAN_GLOW, (int(ox), int(oy)), 2)
    return surf


def create_player_frames():
    """Generates animated pixel-art astronaut frames for normal gravity."""
    frames = {"idle": [], "walk": [], "jump": None}

    def draw_astronaut(leg_offset_l=0, leg_offset_r=0, body_bob=0, jump=False):
        surf = pygame.Surface((24, 30), pygame.SRCALPHA)
        # Oxygen tank on back
        pygame.draw.rect(surf, (90, 100, 130), (3, 7 + body_bob, 4, 13), border_radius=2)
        pygame.draw.rect(surf, COLOR_CYAN_GLOW, (4, 9 + body_bob, 2, 4)) # Battery light

        # Body torso (White suit)
        pygame.draw.rect(surf, COLOR_SUIT_WHITE, (6, 9 + body_bob, 12, 12), border_radius=2)
        pygame.draw.rect(surf, COLOR_SUIT_SHADOW, (6, 17 + body_bob, 12, 4)) # Belt

        # Helmet
        pygame.draw.rect(surf, COLOR_SUIT_WHITE, (6, 1 + body_bob, 12, 10), border_radius=4)
        # Visor (Gold with shine)
        pygame.draw.rect(surf, COLOR_VISOR_GOLD, (11, 3 + body_bob, 7, 5), border_radius=2)
        surf.set_at((12, 4 + body_bob), COLOR_VISOR_SHINE)

        # Legs and Magnetic Boots
        if not jump:
            # Left leg
            pygame.draw.rect(surf, COLOR_SUIT_WHITE, (7, 21, 4, 6 + leg_offset_l))
            pygame.draw.rect(surf, (40, 48, 65), (6, 26 + leg_offset_l, 5, 3)) # Boot
            surf.set_at((6, 28 + leg_offset_l), COLOR_CYAN_GLOW) # Mag sole
            # Right leg
            pygame.draw.rect(surf, COLOR_SUIT_WHITE, (13, 21, 4, 6 + leg_offset_r))
            pygame.draw.rect(surf, (40, 48, 65), (13, 26 + leg_offset_r, 5, 3)) # Boot
            surf.set_at((17, 28 + leg_offset_r), COLOR_CYAN_GLOW) # Mag sole
        else:
            # Tucked legs for jump
            pygame.draw.rect(surf, COLOR_SUIT_WHITE, (7, 21, 4, 4))
            pygame.draw.rect(surf, (40, 48, 65), (6, 24, 5, 3))
            pygame.draw.rect(surf, COLOR_SUIT_WHITE, (13, 20, 4, 4))
            pygame.draw.rect(surf, (40, 48, 65), (13, 23, 5, 3))

        return surf

    # Idle animation (subtle breathing bob)
    frames["idle"].append(draw_astronaut(0, 0, 0))
    frames["idle"].append(draw_astronaut(0, 0, 1))

    # Walk animation (4 steps)
    frames["walk"].append(draw_astronaut(-2, 2, 0))
    frames["walk"].append(draw_astronaut(0, 0, 1))
    frames["walk"].append(draw_astronaut(2, -2, 0))
    frames["walk"].append(draw_astronaut(0, 0, 1))

    # Jump frame
    frames["jump"] = draw_astronaut(0, 0, -1, jump=True)

    return frames
