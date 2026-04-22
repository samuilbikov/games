import random
import sys

import pygame


WIDTH, HEIGHT = 960, 540
FPS = 60
GRAVITY = 0.9
PLAYER_SPEED = 5
JUMP_POWER = -16
ENEMY_SPEED = 2
COIN_COUNT = 8


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cat Platformer")
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 28)
big_font = pygame.font.SysFont("arial", 46, bold=True)


def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


class Platform:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, surface):
        pygame.draw.rect(surface, (70, 120, 70), self.rect, border_radius=8)
        grass = pygame.Rect(self.rect.x, self.rect.y, self.rect.w, 8)
        pygame.draw.rect(surface, (110, 180, 110), grass, border_radius=4)


class Coin:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 18, 18)
        self.collected = False

    def draw(self, surface):
        if self.collected:
            return
        pygame.draw.circle(surface, (255, 215, 0), self.rect.center, 9)
        pygame.draw.circle(surface, (245, 190, 0), self.rect.center, 9, 2)


class Enemy:
    def __init__(self, x, y, left_limit, right_limit):
        self.rect = pygame.Rect(x, y, 34, 34)
        self.vel_x = ENEMY_SPEED
        self.left_limit = left_limit
        self.right_limit = right_limit

    def update(self):
        self.rect.x += self.vel_x
        if self.rect.left <= self.left_limit or self.rect.right >= self.right_limit:
            self.vel_x *= -1

    def draw(self, surface):
        pygame.draw.rect(surface, (200, 70, 70), self.rect, border_radius=6)
        eye1 = pygame.Rect(self.rect.x + 7, self.rect.y + 9, 5, 5)
        eye2 = pygame.Rect(self.rect.x + 22, self.rect.y + 9, 5, 5)
        pygame.draw.rect(surface, (255, 255, 255), eye1)
        pygame.draw.rect(surface, (255, 255, 255), eye2)


class Player:
    def __init__(self):
        self.rect = pygame.Rect(80, HEIGHT - 160, 40, 48)
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.facing = 1

    def move_and_collide(self, platforms):
        self.rect.x += self.vel_x
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vel_x > 0:
                    self.rect.right = p.rect.left
                elif self.vel_x < 0:
                    self.rect.left = p.rect.right

        self.rect.y += self.vel_y
        self.on_ground = False
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vel_y > 0:
                    self.rect.bottom = p.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = p.rect.bottom
                    self.vel_y = 0

    def update(self, keys, platforms):
        self.vel_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -PLAYER_SPEED
            self.facing = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = PLAYER_SPEED
            self.facing = 1

        self.vel_y += GRAVITY
        self.vel_y = clamp(self.vel_y, -100, 20)
        self.move_and_collide(platforms)

    def jump(self):
        if self.on_ground:
            self.vel_y = JUMP_POWER
            self.on_ground = False

    def draw(self, surface):
        # Cat-inspired simple character body.
        pygame.draw.rect(surface, (90, 140, 230), self.rect, border_radius=10)
        head = pygame.Rect(self.rect.x + 4, self.rect.y - 18, 32, 24)
        pygame.draw.rect(surface, (110, 160, 240), head, border_radius=8)

        if self.facing == 1:
            ear1 = [(head.x + 6, head.y + 6), (head.x + 12, head.y - 8), (head.x + 18, head.y + 6)]
            ear2 = [(head.x + 20, head.y + 6), (head.x + 26, head.y - 8), (head.x + 32, head.y + 6)]
            eye_x = head.x + 22
        else:
            ear1 = [(head.x + 0, head.y + 6), (head.x + 6, head.y - 8), (head.x + 12, head.y + 6)]
            ear2 = [(head.x + 14, head.y + 6), (head.x + 20, head.y - 8), (head.x + 26, head.y + 6)]
            eye_x = head.x + 8

        pygame.draw.polygon(surface, (110, 160, 240), ear1)
        pygame.draw.polygon(surface, (110, 160, 240), ear2)
        pygame.draw.circle(surface, (255, 255, 255), (eye_x, head.y + 12), 3)

        tail_dir = 1 if self.facing == 1 else -1
        tail_start = (self.rect.centerx - 15 * tail_dir, self.rect.centery)
        tail_end = (self.rect.centerx - 28 * tail_dir, self.rect.centery - 6)
        pygame.draw.line(surface, (90, 140, 230), tail_start, tail_end, 6)


def create_level():
    platforms = [
        Platform(0, HEIGHT - 40, WIDTH, 40),
        Platform(120, HEIGHT - 140, 180, 20),
        Platform(360, HEIGHT - 220, 160, 20),
        Platform(590, HEIGHT - 170, 160, 20),
        Platform(760, HEIGHT - 260, 140, 20),
        Platform(520, HEIGHT - 320, 140, 20),
        Platform(250, HEIGHT - 320, 90, 20),
    ]

    coins = []
    random.seed(4)
    for _ in range(COIN_COUNT):
        p = random.choice(platforms[1:])
        x = random.randint(p.rect.left + 16, p.rect.right - 24)
        y = p.rect.top - 22
        coins.append(Coin(x, y))

    enemies = [
        Enemy(150, HEIGHT - 74, 50, 350),
        Enemy(620, HEIGHT - 204, 570, 760),
        Enemy(785, HEIGHT - 294, 760, 900),
    ]
    goal = pygame.Rect(880, HEIGHT - 330, 30, 70)
    return platforms, coins, enemies, goal


def draw_hud(surface, score, total_coins, game_state):
    score_text = font.render(f"Coins: {score}/{total_coins}", True, (35, 35, 35))
    surface.blit(score_text, (20, 16))

    if game_state == "lost":
        msg = big_font.render("You got caught! Press R to retry", True, (180, 40, 40))
        surface.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 - 35))
    elif game_state == "won":
        msg = big_font.render("You win! Press R to play again", True, (30, 140, 70))
        surface.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 - 35))


def reset_world():
    player = Player()
    platforms, coins, enemies, goal = create_level()
    return player, platforms, coins, enemies, goal, "playing"


def main():
    player, platforms, coins, enemies, goal, game_state = reset_world()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w, pygame.K_SPACE):
                    if game_state == "playing":
                        player.jump()
                if event.key == pygame.K_r:
                    player, platforms, coins, enemies, goal, game_state = reset_world()

        keys = pygame.key.get_pressed()
        if game_state == "playing":
            player.update(keys, platforms)
            for enemy in enemies:
                enemy.update()
                if player.rect.colliderect(enemy.rect):
                    game_state = "lost"

            if player.rect.top > HEIGHT + 100:
                game_state = "lost"

            for coin in coins:
                if not coin.collected and player.rect.colliderect(coin.rect):
                    coin.collected = True

            all_collected = all(c.collected for c in coins)
            if all_collected and player.rect.colliderect(goal):
                game_state = "won"

        screen.fill((170, 220, 255))
        pygame.draw.rect(screen, (240, 250, 255), (0, 0, WIDTH, 120))

        # Goal flag
        pygame.draw.line(screen, (90, 90, 90), (goal.x + 5, goal.y), (goal.x + 5, goal.bottom), 4)
        flag_color = (40, 180, 80) if all(c.collected for c in coins) else (230, 130, 50)
        pygame.draw.polygon(
            screen,
            flag_color,
            [(goal.x + 7, goal.y + 8), (goal.x + 32, goal.y + 18), (goal.x + 7, goal.y + 28)],
        )

        for platform in platforms:
            platform.draw(screen)
        for coin in coins:
            coin.draw(screen)
        for enemy in enemies:
            enemy.draw(screen)
        player.draw(screen)
        draw_hud(screen, sum(coin.collected for coin in coins), len(coins), game_state)

        if game_state == "playing" and not all(c.collected for c in coins):
            reminder = font.render("Collect all coins, then reach the flag!", True, (40, 40, 40))
            screen.blit(reminder, (WIDTH // 2 - reminder.get_width() // 2, 18))

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
