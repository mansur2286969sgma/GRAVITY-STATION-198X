"""
GRAVITY STATION: 198X
A Retro 8-bit Pixel Art Sci-Fi Puzzle Platformer with Gravity Inversion.
Created in Pygame.
"""

import sys
import os
import pygame
import math
import random

# Import local modules
from sound_gen import SoundManager
from sprites import (
    TILE_SIZE,
    create_hull_tile,
    create_hazard_tile,
    create_spike_tile,
    create_crate_sprite,
    create_switch_sprites,
    create_door_sprite,
    create_portal_sprite,
    create_grav_orb_sprite,
    create_player_frames,
    COLOR_CYAN_GLOW,
    COLOR_ORANGE_GLOW,
    COLOR_GREEN_ACTIVE,
    COLOR_RED_ALARM,
    COLOR_SUIT_WHITE,
    COLOR_VISOR_GOLD
)
from particles import ParticleManager, Starfield
from levels import ALL_LEVELS

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 576
FPS = 60

MOVE_SPEED = 3.6
JUMP_FORCE = 7.5
GRAVITY_ACCEL = 0.42
MAX_FALL_SPEED = 8.5


class Crate:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.vx = 0
        self.vy = 0
        self.grounded = False

    def update_physics(self, gravity_dir, solid_rects, other_crates):
        # Apply gravity
        self.vy += GRAVITY_ACCEL * gravity_dir
        if abs(self.vy) > MAX_FALL_SPEED:
            self.vy = math.copysign(MAX_FALL_SPEED, self.vy)

        # Vertical movement & collision
        self.rect.y += int(self.vy)
        self.grounded = False

        colliders = solid_rects + [c.rect for c in other_crates if c != self]
        for r in colliders:
            if self.rect.colliderect(r):
                if self.vy > 0:  # Moving down
                    self.rect.bottom = r.top
                    self.vy = 0
                    if gravity_dir == 1:
                        self.grounded = True
                elif self.vy < 0:  # Moving up
                    self.rect.top = r.bottom
                    self.vy = 0
                    if gravity_dir == -1:
                        self.grounded = True

        # Horizontal deceleration / friction
        self.rect.x += int(self.vx)
        for r in colliders:
            if self.rect.colliderect(r):
                if self.vx > 0:
                    self.rect.right = r.left
                elif self.vx < 0:
                    self.rect.left = r.right
                self.vx = 0
        self.vx *= 0.6
        if abs(self.vx) < 0.1:
            self.vx = 0


class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x + 4, y + 2, 20, 28)
        self.vx = 0.0
        self.vy = 0.0
        self.gravity_dir = 1  # 1 = Down, -1 = Up (ceiling)
        self.grounded = False
        self.facing_right = True
        self.anim_frame = 0
        self.anim_timer = 0
        self.is_moving = False
        self.alive = True

    def update(self, keys, solid_rects, crates, sounds, particles):
        if not self.alive:
            return

        # Horizontal movement
        move_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_x -= 1
            self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_x += 1
            self.facing_right = True

        self.vx = move_x * MOVE_SPEED
        self.is_moving = move_x != 0

        # Jump
        if (keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_SPACE]) and self.grounded:
            self.vy = -JUMP_FORCE * self.gravity_dir
            self.grounded = False
            sounds.play("jump")
            particles.add_jump_dust(self.rect.centerx, self.rect.bottom if self.gravity_dir == 1 else self.rect.top, self.gravity_dir)

        # Gravity
        self.vy += GRAVITY_ACCEL * self.gravity_dir
        if abs(self.vy) > MAX_FALL_SPEED:
            self.vy = math.copysign(MAX_FALL_SPEED, self.vy)

        # Move X & Collisions (Walls + Crates)
        self.rect.x += int(self.vx)
        colliders = solid_rects.copy()

        # Check crate push
        for crate in crates:
            if self.rect.colliderect(crate.rect):
                # Try pushing crate
                push_dir = 1 if self.vx > 0 else -1
                old_x = crate.rect.x
                crate.rect.x += push_dir * 3
                # Check if crate collides with walls or other crates
                crate_colliders = solid_rects + [c.rect for c in crates if c != crate]
                blocked = False
                for cr in crate_colliders:
                    if crate.rect.colliderect(cr):
                        blocked = True
                        break
                if blocked:
                    crate.rect.x = old_x
                    if push_dir > 0:
                        self.rect.right = crate.rect.left
                    else:
                        self.rect.left = crate.rect.right
                else:
                    crate.vx = push_dir * 1.5
                    sounds.play("push")

        for r in colliders:
            if self.rect.colliderect(r):
                if self.vx > 0:
                    self.rect.right = r.left
                elif self.vx < 0:
                    self.rect.left = r.right

        # Move Y & Collisions
        self.rect.y += int(self.vy)
        self.grounded = False
        all_y_colliders = solid_rects + [c.rect for c in crates]

        for r in all_y_colliders:
            if self.rect.colliderect(r):
                if self.vy > 0:  # Moving Down
                    self.rect.bottom = r.top
                    self.vy = 0
                    if self.gravity_dir == 1:
                        self.grounded = True
                elif self.vy < 0:  # Moving Up
                    self.rect.top = r.bottom
                    self.vy = 0
                    if self.gravity_dir == -1:
                        self.grounded = True

        # Animation timer
        self.anim_timer += 1
        if self.is_moving:
            if self.anim_timer % 7 == 0:
                self.anim_frame = (self.anim_frame + 1) % 4
        else:
            if self.anim_timer % 30 == 0:
                self.anim_frame = (self.anim_frame + 1) % 2

    def flip_gravity(self, sounds, particles):
        if not self.alive:
            return False
        if not self.grounded:
            return False  # Can only flip when anchored to a surface!

        self.gravity_dir *= -1
        self.grounded = False
        sounds.play("flip")
        particles.add_gravity_flip_burst(self.rect.centerx, self.rect.centery, self.gravity_dir)
        return True


class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption("GRAVITY STATION: 198X")

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_large = pygame.font.SysFont("Consolas", 32, bold=True)
        self.font_mid = pygame.font.SysFont("Consolas", 20, bold=True)
        self.font_small = pygame.font.SysFont("Consolas", 14)

        # Managers & Systems
        self.sounds = SoundManager()
        self.particles = ParticleManager()
        self.starfield = Starfield(SCREEN_WIDTH, SCREEN_HEIGHT)

        # Load sprites
        self.hull_tile = create_hull_tile()
        self.hazard_tile = create_hazard_tile()
        self.spike_down = create_spike_tile(upside_down=False)
        self.spike_up = create_spike_tile(upside_down=True)
        self.crate_sprite = create_crate_sprite()
        self.switch_unpressed, self.switch_pressed = create_switch_sprites()
        self.door_closed = create_door_sprite(opened=False)
        self.door_opened = create_door_sprite(opened=True)
        self.player_frames = create_player_frames()

        # State
        self.state = "TITLE"  # TITLE, PLAYING, LEVEL_CLEAR, DYING, GAME_WON
        self.current_level_idx = 0
        self.crt_effect = True
        self.screen_shake = 0
        self.death_timer = 0
        self.level_clear_timer = 0
        self.global_tick = 0

        # Scanline surface
        self.scanlines = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for y in range(0, SCREEN_HEIGHT, 3):
            pygame.draw.line(self.scanlines, (0, 0, 0, 45), (0, y), (SCREEN_WIDTH, y), 1)

        self.load_level(self.current_level_idx)
        self.sounds.start_music()

    def load_level(self, idx):
        self.current_level_idx = idx
        level_data = ALL_LEVELS[idx]
        self.level_name = level_data["name"]
        self.level_hint = level_data["hint"]
        layout = level_data["map"]

        self.solid_rects = []
        self.spikes = []       # list of (rect, upside_down)
        self.switches = []     # list of dict: {rect, pressed, is_ceiling}
        self.doors = []        # list of dict: {rect, opened}
        self.lasers = []       # list of dict: {emitter_pos, end_y, active}
        self.crates = []
        self.portal_rect = None
        self.player = None

        for r_idx, row in enumerate(layout):
            for c_idx, ch in enumerate(row):
                x = c_idx * TILE_SIZE
                y = r_idx * TILE_SIZE

                if ch == "#":
                    self.solid_rects.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))
                elif ch == "P":
                    self.player = Player(x, y)
                elif ch == "C":
                    self.crates.append(Crate(x, y))
                elif ch == "E":
                    # Exit portal (2 tiles high: base at y, top at y - 32)
                    self.portal_rect = pygame.Rect(x, y - TILE_SIZE, TILE_SIZE, TILE_SIZE * 2)
                elif ch == "S":
                    # Floor switch
                    sw_rect = pygame.Rect(x, y + 22, TILE_SIZE, 10)
                    self.switches.append({"rect": sw_rect, "pressed": False, "is_ceiling": False})
                elif ch == "T":
                    # Ceiling switch
                    sw_rect = pygame.Rect(x, y, TILE_SIZE, 10)
                    self.switches.append({"rect": sw_rect, "pressed": False, "is_ceiling": True})
                elif ch == "D":
                    # Blast door
                    d_rect = pygame.Rect(x, y - TILE_SIZE, TILE_SIZE, TILE_SIZE * 2)
                    self.doors.append({"rect": d_rect, "opened": False})
                elif ch == "^":
                    sp_rect = pygame.Rect(x + 2, y + 14, TILE_SIZE - 4, 18)
                    self.spikes.append((sp_rect, False))
                elif ch == "v":
                    sp_rect = pygame.Rect(x + 2, y, TILE_SIZE - 4, 18)
                    self.spikes.append((sp_rect, True))
                elif ch == "L":
                    self.lasers.append({"x": x + 16, "y": y + 32, "active": True})

        if not self.player:
            self.player = Player(64, 400)

    def trigger_death(self):
        if self.player.alive:
            self.player.alive = False
            self.state = "DYING"
            self.death_timer = 40
            self.screen_shake = 12
            self.sounds.play("death")
            self.particles.add_death_explosion(self.player.rect.centerx, self.player.rect.centery)

    def update(self):
        self.global_tick += 1

        if self.screen_shake > 0:
            self.screen_shake -= 1

        if self.state == "TITLE":
            return

        if self.state == "DYING":
            self.death_timer -= 1
            if self.death_timer <= 0:
                self.load_level(self.current_level_idx)
                self.state = "PLAYING"
            return

        if self.state == "LEVEL_CLEAR":
            self.level_clear_timer -= 1
            if self.level_clear_timer <= 0:
                if self.current_level_idx + 1 < len(ALL_LEVELS):
                    self.load_level(self.current_level_idx + 1)
                    self.state = "PLAYING"
                else:
                    self.state = "GAME_WON"
                    self.sounds.play("win")
            return

        if self.state == "GAME_WON":
            return

        # PLAYING STATE
        keys = pygame.key.get_pressed()

        # Update crates
        active_solid_rects = self.solid_rects.copy()
        for d in self.doors:
            if not d["opened"]:
                active_solid_rects.append(d["rect"])

        for crate in self.crates:
            crate.update_physics(self.player.gravity_dir, active_solid_rects, self.crates)

        # Update player
        self.player.update(keys, active_solid_rects, self.crates, self.sounds, self.particles)

        # Update switches
        any_switch_changed = False
        all_pressed = True if len(self.switches) > 0 else False

        for sw in self.switches:
            # Check if player or any crate touches the switch
            was_pressed = sw["pressed"]
            is_touched = self.player.rect.colliderect(sw["rect"])
            for c in self.crates:
                if c.rect.colliderect(sw["rect"]):
                    is_touched = True
                    break

            sw["pressed"] = is_touched
            if not is_touched:
                all_pressed = False

            if not was_pressed and is_touched:
                self.sounds.play("switch")
                self.particles.add_switch_spark(sw["rect"].centerx, sw["rect"].centery)
                any_switch_changed = True

        # Update doors state
        if len(self.switches) > 0:
            for d in self.doors:
                prev = d["opened"]
                d["opened"] = all_pressed
                if not prev and d["opened"]:
                    self.sounds.play("door")

        # Update and check Lasers
        for laser in self.lasers:
            lx = laser["x"]
            ly = laser["y"]
            # Cast ray down to find obstacle (solid wall, door, or crate)
            hit_y = SCREEN_HEIGHT - 32
            for y_check in range(ly, SCREEN_HEIGHT - 32, 4):
                point_rect = pygame.Rect(lx - 2, y_check, 4, 4)
                # Check collision with solid tiles
                hit = False
                for r in self.solid_rects:
                    if r.colliderect(point_rect):
                        hit_y = r.top
                        hit = True
                        break
                # Check collision with crates
                for c in self.crates:
                    if c.rect.colliderect(point_rect):
                        hit_y = c.rect.top
                        hit = True
                        break
                if hit:
                    break

            laser["end_y"] = hit_y
            self.particles.add_laser_sparks(lx, hit_y)

            # Check if player touches laser beam
            laser_beam_rect = pygame.Rect(lx - 3, ly, 6, max(0, hit_y - ly))
            if self.player.rect.colliderect(laser_beam_rect):
                self.trigger_death()

        # Check Spikes
        for sp_rect, _ in self.spikes:
            if self.player.rect.colliderect(sp_rect):
                self.trigger_death()

        # Check Out of bounds
        if self.player.rect.top > SCREEN_HEIGHT or self.player.rect.bottom < 0:
            self.trigger_death()

        # Check Exit Portal
        if self.portal_rect and self.player.rect.colliderect(self.portal_rect):
            # Check if doors are blocking
            blocked = False
            for d in self.doors:
                if not d["opened"] and self.player.rect.colliderect(d["rect"]):
                    blocked = True
                    break
            if not blocked and self.player.alive:
                self.state = "LEVEL_CLEAR"
                self.level_clear_timer = 50
                self.sounds.play("win")

    def draw(self):
        # Base background fill
        self.screen.fill((12, 14, 24))

        # Render drifting starfield
        self.starfield.update_and_draw(self.screen)

        # Compute camera shake offset
        ox = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        oy = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0

        game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        # 1. Draw solid walls
        for r in self.solid_rects:
            game_surface.blit(self.hull_tile, (r.x, r.y))

        # 2. Draw Exit Portal
        if self.portal_rect:
            portal_surf = create_portal_sprite(frame=self.global_tick // 4)
            game_surface.blit(portal_surf, (self.portal_rect.x, self.portal_rect.y))

        # 3. Draw Switches
        for sw in self.switches:
            s_img = self.switch_pressed if sw["pressed"] else self.switch_unpressed
            if sw["is_ceiling"]:
                s_img = pygame.transform.flip(s_img, False, True)
            game_surface.blit(s_img, (sw["rect"].x, sw["rect"].y))

        # 4. Draw Doors
        for d in self.doors:
            d_img = self.door_opened if d["opened"] else self.door_closed
            game_surface.blit(d_img, (d["rect"].x, d["rect"].y))

        # 5. Draw Spikes
        for sp_rect, upside_down in self.spikes:
            sp_img = self.spike_up if upside_down else self.spike_down
            # Align with tile
            tx = (sp_rect.x // TILE_SIZE) * TILE_SIZE
            ty = (sp_rect.y // TILE_SIZE) * TILE_SIZE
            game_surface.blit(sp_img, (tx, ty))

        # 6. Draw Lasers
        for laser in self.lasers:
            lx = laser["x"]
            ly = laser["y"]
            ey = laser.get("end_y", SCREEN_HEIGHT)

            # Emitter box
            pygame.draw.rect(game_surface, (70, 80, 110), (lx - 12, ly - 32, 24, 10), border_radius=2)
            pygame.draw.rect(game_surface, COLOR_RED_ALARM, (lx - 6, ly - 24, 12, 4))

            # Pulsing beam
            beam_width = 3 + int(math.sin(self.global_tick * 0.4) * 1.5)
            # Outer glow
            pygame.draw.line(game_surface, (255, 60, 70, 120), (lx, ly), (lx, ey), beam_width + 4)
            # Core beam
            pygame.draw.line(game_surface, (255, 230, 230), (lx, ly), (lx, ey), max(1, beam_width - 1))

        # 7. Draw Crates
        for crate in self.crates:
            game_surface.blit(self.crate_sprite, (crate.rect.x, crate.rect.y))
            # Directional arrow indicator showing current crate gravity
            arrow_color = COLOR_CYAN_GLOW if self.player.gravity_dir == 1 else COLOR_ORANGE_GLOW
            cy = crate.rect.centery
            cx = crate.rect.centerx
            dy = 5 * self.player.gravity_dir
            pygame.draw.line(game_surface, arrow_color, (cx, cy - dy), (cx, cy + dy), 2)
            pygame.draw.line(game_surface, arrow_color, (cx - 3, cy + dy - 3 * self.player.gravity_dir), (cx, cy + dy), 2)
            pygame.draw.line(game_surface, arrow_color, (cx + 3, cy + dy - 3 * self.player.gravity_dir), (cx, cy + dy), 2)

        # 8. Draw Player
        if self.player.alive:
            if not self.player.grounded:
                p_surf = self.player_frames["jump"]
            elif self.player.is_moving:
                p_surf = self.player_frames["walk"][self.player.anim_frame % 4]
            else:
                p_surf = self.player_frames["idle"][self.player.anim_frame % 2]

            # Flip horizontal if facing left
            if not self.player.facing_right:
                p_surf = pygame.transform.flip(p_surf, True, False)

            # Flip vertical if inverted gravity!
            if self.player.gravity_dir == -1:
                p_surf = pygame.transform.flip(p_surf, False, True)

            game_surface.blit(p_surf, (self.player.rect.x - 2, self.player.rect.y - 1))

        # 9. Update & Draw Particles
        self.particles.update_and_draw(game_surface)

        # Blit game surface to screen with camera shake
        self.screen.blit(game_surface, (ox, oy))

        # 10. UI Overlay
        self.draw_ui()

        # 11. CRT Scanline filter
        if self.crt_effect:
            self.screen.blit(self.scanlines, (0, 0))

        pygame.display.flip()

    def draw_ui(self):
        # Title bar HUD
        hud_bg = pygame.Surface((SCREEN_WIDTH, 34), pygame.SRCALPHA)
        hud_bg.fill((14, 18, 30, 210))
        self.screen.blit(hud_bg, (0, 0))
        pygame.draw.line(self.screen, (50, 65, 95), (0, 34), (SCREEN_WIDTH, 34), 1)

        # Level name
        lvl_txt = self.font_mid.render(self.level_name, True, (240, 245, 255))
        self.screen.blit(lvl_txt, (14, 7))

        # Gravity status badge
        grav_color = COLOR_CYAN_GLOW if self.player.gravity_dir == 1 else COLOR_ORANGE_GLOW
        grav_name = "DOWN ∇" if self.player.gravity_dir == 1 else "UP Δ"
        badge_txt = self.font_mid.render(f"GRAVITY: {grav_name}", True, grav_color)
        self.screen.blit(badge_txt, (SCREEN_WIDTH - 200, 7))

        # Bottom Hint Bar
        hint_bg = pygame.Surface((SCREEN_WIDTH, 26), pygame.SRCALPHA)
        hint_bg.fill((14, 18, 30, 190))
        self.screen.blit(hint_bg, (0, SCREEN_HEIGHT - 26))
        pygame.draw.line(self.screen, (50, 65, 95), (0, SCREEN_HEIGHT - 26), (SCREEN_WIDTH, SCREEN_HEIGHT - 26), 1)

        hint_render = self.font_small.render(f"{self.level_hint}  |  [R] Рестарт  [M] Звук  [F1] CRT-фильтр", True, (170, 190, 220))
        self.screen.blit(hint_render, (14, SCREEN_HEIGHT - 20))

        # Level Clear Overlay
        if self.state == "LEVEL_CLEAR":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((10, 30, 20, 170))
            self.screen.blit(overlay, (0, 0))
            msg = self.font_large.render("SECTOR CLEARED!", True, COLOR_GREEN_ACTIVE)
            self.screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, SCREEN_HEIGHT // 2 - 20))

        # Game Won Screen
        elif self.state == "GAME_WON":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((8, 12, 28, 220))
            self.screen.blit(overlay, (0, 0))

            t1 = self.font_large.render("MISSION ACCOMPLISHED!", True, COLOR_CYAN_GLOW)
            t2 = self.font_mid.render("Станция спасена! Все гравитационные шлюзы пройдены.", True, (240, 245, 255))
            t3 = self.font_mid.render("Нажмите [ENTER] для повтора  |  [ESC] Выход", True, COLOR_ORANGE_GLOW)

            self.screen.blit(t1, (SCREEN_WIDTH // 2 - t1.get_width() // 2, SCREEN_HEIGHT // 2 - 60))
            self.screen.blit(t2, (SCREEN_WIDTH // 2 - t2.get_width() // 2, SCREEN_HEIGHT // 2 - 10))
            self.screen.blit(t3, (SCREEN_WIDTH // 2 - t3.get_width() // 2, SCREEN_HEIGHT // 2 + 50))

        # Title Screen
        elif self.state == "TITLE":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((10, 14, 26, 230))
            self.screen.blit(overlay, (0, 0))

            title = self.font_large.render("GRAVITY STATION: 198X", True, COLOR_CYAN_GLOW)
            sub = self.font_mid.render("Ретро-платформер с инверсией гравитации", True, (200, 215, 240))
            prompt = self.font_mid.render("Нажмите [ENTER] или [ПРОБЕЛ] чтобы начать", True, COLOR_ORANGE_GLOW)

            # Controls help box
            box = pygame.Rect(SCREEN_WIDTH // 2 - 240, SCREEN_HEIGHT // 2 + 10, 480, 150)
            pygame.draw.rect(self.screen, (25, 32, 52), box, border_radius=6)
            pygame.draw.rect(self.screen, (60, 80, 120), box, 2, border_radius=6)

            lines = [
                "УПРАВЛЕНИЕ:",
                "• [A/D] или [Стрелки] - Бег влево / вправо",
                "• [W] или [ПРОБЕЛ] - Прыжок",
                "• [G], [SHIFT] или [Z] - СМЕНА ГРАВИТАЦИИ (стоя на полу/потолке)",
                "• [R] - Быстрый рестарт уровня",
                "• [M] - Вкл/Выкл музыку и звуки  |  [F1] - CRT фильтр"
            ]
            for idx, line in enumerate(lines):
                col = COLOR_VISOR_GOLD if idx == 0 else (210, 225, 245)
                fnt = self.font_mid if idx == 0 else self.font_small
                t = fnt.render(line, True, col)
                self.screen.blit(t, (box.x + 18, box.y + 14 + idx * 21))

            self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 120))
            self.screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, SCREEN_HEIGHT // 2 - 80))
            self.screen.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, SCREEN_HEIGHT // 2 - 35))

    def run(self):
        running = True
        while running:
            self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

                    # Title / Game Won transition
                    if self.state == "TITLE":
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.state = "PLAYING"
                            self.sounds.play("door")

                    elif self.state == "GAME_WON":
                        if event.key == pygame.K_RETURN:
                            self.load_level(0)
                            self.state = "PLAYING"

                    elif self.state == "PLAYING":
                        # Gravity flip
                        if event.key in (pygame.K_g, pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_z, pygame.K_c):
                            if self.player.flip_gravity(self.sounds, self.particles):
                                self.screen_shake = 5

                        # Restart level
                        elif event.key == pygame.K_r:
                            self.load_level(self.current_level_idx)
                            self.sounds.play("switch")

                        # Toggle Sound
                        elif event.key == pygame.K_m:
                            self.sounds.toggle()

                        # Toggle CRT effect
                        elif event.key == pygame.K_F1:
                            self.crt_effect = not self.crt_effect

            self.update()
            self.draw()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
