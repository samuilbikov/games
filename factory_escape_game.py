import math
import random
import sys

import pygame


WIDTH, HEIGHT = 1000, 620
FPS = 60
PLAYER_SPEED = 2.6
MONSTER_PATROL_SPEED = 1.5
MONSTER_CHASE_SPEED = 2.2
VISION_RADIUS = 210
MAX_STAMINA = 220


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Factory Escape: Chapter Zero")
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 24)
small_font = pygame.font.SysFont("consolas", 18)
big_font = pygame.font.SysFont("consolas", 42, bold=True)


WALLS = [
    pygame.Rect(0, 0, WIDTH, 16),
    pygame.Rect(0, HEIGHT - 16, WIDTH, 16),
    pygame.Rect(0, 0, 16, HEIGHT),
    pygame.Rect(WIDTH - 16, 0, 16, HEIGHT),
    pygame.Rect(100, 110, 280, 16),
    pygame.Rect(100, 110, 16, 210),
    pygame.Rect(100, 320, 270, 16),
    pygame.Rect(370, 110, 16, 226),
    pygame.Rect(470, 16, 16, 220),
    pygame.Rect(470, 300, 16, 200),
    pygame.Rect(600, 120, 250, 16),
    pygame.Rect(600, 120, 16, 290),
    pygame.Rect(600, 410, 250, 16),
    pygame.Rect(850, 120, 16, 306),
    pygame.Rect(220, 450, 280, 16),
    pygame.Rect(220, 450, 16, 120),
    pygame.Rect(220, 570, 280, 16),
]


def draw_text_center(surface, text, y, renderer, color):
    img = renderer.render(text, True, color)
    surface.blit(img, (WIDTH // 2 - img.get_width() // 2, y))


class Actor:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.vx = 0
        self.vy = 0

    def _collide_axis(self, walls, horizontal):
        for wall in walls:
            if self.rect.colliderect(wall):
                if horizontal:
                    if self.vx > 0:
                        self.rect.right = wall.left
                    elif self.vx < 0:
                        self.rect.left = wall.right
                else:
                    if self.vy > 0:
                        self.rect.bottom = wall.top
                    elif self.vy < 0:
                        self.rect.top = wall.bottom

    def move(self, walls):
        self.rect.x += int(self.vx)
        self._collide_axis(walls, horizontal=True)
        self.rect.y += int(self.vy)
        self._collide_axis(walls, horizontal=False)


class Player(Actor):
    def __init__(self, x, y):
        super().__init__(x, y, 28, 28)
        self.stamina = MAX_STAMINA
        self.keycards = 0

    def update(self, keys, walls):
        dx = 0
        dy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1

        sprint = keys[pygame.K_LSHIFT] and self.stamina > 0 and (dx != 0 or dy != 0)
        speed = PLAYER_SPEED * (1.8 if sprint else 1.0)
        if sprint:
            self.stamina = max(0, self.stamina - 1.1)
        else:
            self.stamina = min(MAX_STAMINA, self.stamina + 0.75)

        if dx != 0 and dy != 0:
            scale = speed / math.sqrt(2)
            self.vx = dx * scale
            self.vy = dy * scale
        else:
            self.vx = dx * speed
            self.vy = dy * speed

        self.move(walls)

    def draw(self, surface):
        pygame.draw.rect(surface, (100, 210, 255), self.rect, border_radius=6)
        pygame.draw.rect(surface, (30, 100, 160), self.rect, 2, border_radius=6)


class Monster(Actor):
    def __init__(self, x, y):
        super().__init__(x, y, 34, 34)
        self.path = [
            pygame.Vector2(760, 520),
            pygame.Vector2(760, 180),
            pygame.Vector2(560, 180),
            pygame.Vector2(560, 520),
        ]
        self.path_index = 0
        self.alerted = False
        self.freeze_timer = 0

    def can_see_player(self, player, walls):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist > VISION_RADIUS:
            return False
        ray_steps = int(dist // 10) + 1
        for i in range(1, ray_steps + 1):
            t = i / ray_steps
            x = int(self.rect.centerx + dx * t)
            y = int(self.rect.centery + dy * t)
            point_rect = pygame.Rect(x - 1, y - 1, 2, 2)
            if any(point_rect.colliderect(w) for w in walls):
                return False
        return True

    def update(self, player, walls, power_on):
        if self.freeze_timer > 0:
            self.freeze_timer -= 1
            self.vx = 0
            self.vy = 0
            return

        if power_on and self.can_see_player(player, walls):
            self.alerted = True

        speed = MONSTER_PATROL_SPEED
        if self.alerted:
            target = pygame.Vector2(player.rect.centerx, player.rect.centery)
            speed = MONSTER_CHASE_SPEED
        else:
            target = self.path[self.path_index]

        current = pygame.Vector2(self.rect.centerx, self.rect.centery)
        direction = target - current
        dist = direction.length()
        if dist > 0:
            direction = direction.normalize()
        self.vx = direction.x * speed
        self.vy = direction.y * speed
        self.move(walls)

        if not self.alerted and dist < 9:
            self.path_index = (self.path_index + 1) % len(self.path)

    def draw(self, surface):
        body_color = (220, 50, 60) if self.alerted else (160, 40, 140)
        pygame.draw.rect(surface, body_color, self.rect, border_radius=6)
        pygame.draw.circle(surface, (255, 255, 255), (self.rect.x + 10, self.rect.y + 13), 4)
        pygame.draw.circle(surface, (255, 255, 255), (self.rect.x + 24, self.rect.y + 13), 4)
        pygame.draw.circle(surface, (20, 20, 20), (self.rect.x + 10, self.rect.y + 13), 2)
        pygame.draw.circle(surface, (20, 20, 20), (self.rect.x + 24, self.rect.y + 13), 2)


class World:
    def __init__(self):
        self.player = Player(70, 70)
        self.monster = Monster(760, 520)
        self.power_switch = pygame.Rect(294, 508, 44, 44)
        self.exit_door = pygame.Rect(922, 42, 48, 70)
        self.keycards = []
        self.power_on = False
        self.state = "intro"
        self.flash_timer = 0
        self.seed_keycards()

    def seed_keycards(self):
        points = [
            (146, 152),
            (306, 260),
            (532, 344),
            (656, 162),
            (792, 370),
            (262, 520),
        ]
        random.shuffle(points)
        self.keycards = [pygame.Rect(x, y, 20, 14) for x, y in points[:3]]

    def restart(self):
        self.__init__()

    def update(self):
        keys = pygame.key.get_pressed()
        if self.state == "intro":
            if keys[pygame.K_SPACE]:
                self.state = "playing"
            return

        if self.state in ("won", "lost"):
            if keys[pygame.K_r]:
                self.restart()
            return

        self.player.update(keys, WALLS)
        self.monster.update(self.player, WALLS, self.power_on)

        for card in self.keycards[:]:
            if self.player.rect.colliderect(card):
                self.keycards.remove(card)
                self.player.keycards += 1

        if self.player.keycards == 3 and self.player.rect.colliderect(self.power_switch):
            self.power_on = True

        if self.power_on and self.player.rect.colliderect(self.exit_door):
            self.state = "won"

        if self.player.rect.colliderect(self.monster.rect):
            self.state = "lost"
            self.flash_timer = 30

    def draw_room_details(self, surface):
        for wall in WALLS:
            pygame.draw.rect(surface, (42, 42, 52), wall)

        pygame.draw.rect(surface, (95, 78, 64), self.power_switch, border_radius=5)
        switch_light = (80, 230, 120) if self.power_on else (220, 60, 60)
        pygame.draw.circle(surface, switch_light, self.power_switch.center, 9)

        door_color = (100, 220, 110) if self.power_on else (120, 120, 120)
        pygame.draw.rect(surface, door_color, self.exit_door, border_radius=4)
        pygame.draw.rect(surface, (28, 28, 28), self.exit_door, 2, border_radius=4)

        for card in self.keycards:
            pygame.draw.rect(surface, (255, 240, 120), card, border_radius=3)
            pygame.draw.rect(surface, (120, 95, 20), card, 2, border_radius=3)

        pygame.draw.circle(surface, (50, 160, 220), (170, 390), 24)
        pygame.draw.rect(surface, (220, 130, 80), (518, 70, 46, 34), border_radius=5)
        pygame.draw.rect(surface, (230, 210, 70), (710, 468, 56, 26), border_radius=5)

    def draw_lighting(self, surface):
        darkness = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        darkness.fill((0, 0, 0, 210 if not self.power_on else 175))
        center = self.player.rect.center
        pygame.draw.circle(darkness, (0, 0, 0, 30), center, 120)
        pygame.draw.circle(darkness, (0, 0, 0, 70), center, 180, 28)
        surface.blit(darkness, (0, 0))

    def draw_hud(self, surface):
        stamina_ratio = self.player.stamina / MAX_STAMINA
        pygame.draw.rect(surface, (30, 30, 30), (18, 16, 220, 20), border_radius=5)
        pygame.draw.rect(surface, (80, 200, 130), (18, 16, int(220 * stamina_ratio), 20), border_radius=5)
        pygame.draw.rect(surface, (10, 10, 10), (18, 16, 220, 20), 2, border_radius=5)
        surface.blit(small_font.render("Stamina", True, (225, 225, 225)), (246, 15))

        text = f"Keycards: {self.player.keycards}/3"
        surface.blit(font.render(text, True, (245, 245, 180)), (18, 42))
        status = "Power: ON" if self.power_on else "Power: OFF"
        status_color = (120, 255, 140) if self.power_on else (255, 120, 120)
        surface.blit(font.render(status, True, status_color), (18, 68))
        hint = "SHIFT sprint  |  Find 3 keycards -> Activate power -> Escape"
        surface.blit(small_font.render(hint, True, (200, 200, 200)), (18, HEIGHT - 30))

    def draw_overlays(self, surface):
        if self.state == "intro":
            panel = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            panel.fill((0, 0, 0, 190))
            surface.blit(panel, (0, 0))
            draw_text_center(surface, "Factory Escape: Chapter Zero", 180, big_font, (230, 230, 255))
            draw_text_center(surface, "A toy monster woke up in the dark factory...", 260, font, (220, 220, 220))
            draw_text_center(surface, "Collect 3 keycards, turn power on, and reach the exit door.", 300, font, (220, 220, 220))
            draw_text_center(surface, "Press SPACE to start", 360, font, (255, 230, 130))
        elif self.state == "won":
            panel = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            panel.fill((0, 0, 0, 165))
            surface.blit(panel, (0, 0))
            draw_text_center(surface, "You Escaped The Factory!", 250, big_font, (120, 255, 140))
            draw_text_center(surface, "Press R to play again", 320, font, (230, 230, 230))
        elif self.state == "lost":
            if self.flash_timer > 0:
                flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                intensity = 140 + self.flash_timer * 3
                flash.fill((255, 0, 0, min(255, intensity)))
                surface.blit(flash, (0, 0))
                self.flash_timer -= 1
            draw_text_center(surface, "You Were Caught!", 250, big_font, (255, 90, 90))
            draw_text_center(surface, "Press R to restart", 320, font, (230, 230, 230))

    def draw(self, surface):
        surface.fill((20, 22, 26))
        self.draw_room_details(surface)
        self.player.draw(surface)
        self.monster.draw(surface)
        self.draw_lighting(surface)
        self.draw_hud(surface)
        self.draw_overlays(surface)


def run():
    world = World()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        world.update()
        world.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    run()
