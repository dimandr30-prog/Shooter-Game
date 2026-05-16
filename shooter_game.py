from pygame import *
from random import randint

WIDTH, HEIGHT = 700, 500
FPS = 60

clock = time.Clock()

# ---------------- PARTICLES ----------------
class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = randint(-5, 5)
        self.vy = randint(-5, 5)
        self.life = 40
        self.size = randint(2, 4)
        self.color = (255, randint(100, 255), 0)

    def update(self):
        self.x += self.vx * 0.95
        self.y += self.vy * 0.95
        self.vy += 0.15
        self.vx *= 0.98
        self.life -= 1

    def draw(self, surface):
        if self.life > 0:
            draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)


class Star:
    def __init__(self):
        self.x = randint(0, WIDTH)
        self.y = randint(0, HEIGHT)
        self.speed = randint(1, 3)
        self.size = randint(1, 3)

    def update(self):
        self.y += self.speed
        if self.y > HEIGHT:
            self.y = 0
            self.x = randint(0, WIDTH)

    def draw(self, surface):
        draw.circle(surface, (200, 200, 255), (self.x, self.y), self.size)


particles = []
menu_particles = []
stars = [Star() for _ in range(80)]


def spawn_explosion(x, y):
    for _ in range(25):
        particles.append(Particle(x, y))


# ---------------- SPRITES ----------------
class GameSprite(sprite.Sprite):
    def __init__(self, img, x, y, w, h, speed):
        super().__init__()
        self.image = transform.scale(image.load(img), (w, h))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = speed

    def draw(self, surface):
        surface.blit(self.image, self.rect)


class Player(GameSprite):
    def __init__(self, x, y):
        super().__init__("rocket.png", x, y, 70, 100, 5)

        self.cooldown = 0
        self.ammo = 15
        self.max_ammo = 15

        self.reloading = False
        self.reload_timer = 0

    def update(self, mode):
        keys = key.get_pressed()

        if keys[K_LEFT]:
            self.rect.x = max(0, self.rect.x - self.speed)
        if keys[K_RIGHT]:
            self.rect.x = min(WIDTH - self.rect.width, self.rect.x + self.speed)

        if mode == "realistic":
            if self.cooldown > 0:
                self.cooldown -= 1

            if self.ammo <= 0:
                self.reloading = True

            if self.reloading:
                self.reload_timer += 1
                if self.reload_timer >= 90:
                    self.ammo = self.max_ammo
                    self.reloading = False
                    self.reload_timer = 0

        else:
            self.cooldown = 0
            self.reloading = False
            self.ammo = self.max_ammo
            self.reload_timer = 0

    def shoot(self, bullets, mode):
        if mode != "realistic":
            bullets.add(Bullet(self.rect.centerx, self.rect.top))
            return

        if self.reloading:
            return

        if self.cooldown == 0 and self.ammo > 0:
            bullets.add(Bullet(self.rect.centerx, self.rect.top))
            self.ammo -= 1
            self.cooldown = 15


class Enemy(GameSprite):
    def __init__(self, speed_range):
        x = randint(50, WIDTH - 120)
        y = randint(-200, -40)
        speed = randint(*speed_range)
        super().__init__("ufo.png", x, y, 70, 50, speed)

    def update(self):
        self.rect.y += self.speed * 0.85
        if self.rect.y > HEIGHT:
            self.rect.y = randint(-150, -50)
            self.rect.x = randint(50, WIDTH - self.rect.width - 50)
            return True
        return False


class Bullet(GameSprite):
    def __init__(self, x, y):
        super().__init__("bullet.png", x - 5, y, 10, 20, 10)

    def update(self):
        self.rect.y -= self.speed
        if self.rect.y < 0:
            self.kill()


class Asteroid(GameSprite):
    def __init__(self):
        x = randint(50, WIDTH - 80)
        y = randint(-200, -50)
        super().__init__("asteroid.png", x, y, 60, 60, randint(2, 4))

    def update(self):
        self.rect.y += self.speed


# ---------------- INIT ----------------
init()
mixer.init()

window = display.set_mode((WIDTH, HEIGHT))
display.set_caption("Space Shooter")

background = transform.scale(image.load("galaxy.jpg"), (WIDTH, HEIGHT))

mixer.music.load("space.ogg")
mixer.music.set_volume(0.5)
mixer.music.play(-1)

fire_sound = mixer.Sound("fire.ogg")

font_big = font.SysFont("Arial", 40)
font_small = font.SysFont("Arial", 22)

settings = {
    "easy": {"miss": 5, "hits": 10, "speed": (2, 3)},
    "normal": {"miss": 8, "hits": 13, "speed": (3, 4)},
    "hard": {"miss": 15, "hits": 30, "speed": (4, 4)},
    "infinite": {"miss": 999999, "hits": 999999, "speed": (3, 5)},
    "realistic": {"miss": 250, "hits": 420, "speed": (4, 4)},
}

state = "menu"
difficulty = "easy"


def start_game(diff):
    global player, enemies, bullets, asteroids, hits, missed, start_time

    particles.clear()
    menu_particles.clear()

    player = Player(300, 400)
    enemies = sprite.Group()
    bullets = sprite.Group()
    asteroids = sprite.Group()

    for _ in range(5):
        enemies.add(Enemy(settings[diff]["speed"]))

    hits = 0
    missed = 0
    start_time = time.get_ticks()


def draw_menu_background():
    window.blit(background, (0, 0))

    for star in stars:
        star.update()
        star.draw(window)

    if randint(0, 10) == 0:
        menu_particles.append(Particle(randint(0, WIDTH), HEIGHT))

    for p in menu_particles[:]:
        p.update()
        if p.life <= 0:
            menu_particles.remove(p)
        else:
            p.draw(window)


# ---------------- MAIN LOOP ----------------
running = True
paused = False

while running:
    mouse_pos = mouse.get_pos()

    for e in event.get():
        if e.type == QUIT:
            running = False

        if e.type == KEYDOWN:

            # ESC = pause/unpause
            if e.key == K_ESCAPE and state == "game":
                paused = not paused

            if e.key == K_m:
                state = "menu"
                paused = False

            # prevent shooting while paused
            if state == "game" and not paused and e.key == K_SPACE:
                player.shoot(bullets, difficulty)
                fire_sound.play()

            if e.key == K_SPACE:
                if state in ("lose", "win"):
                    paused = False
                    state = "game"
                    start_game(difficulty)

    # ---------------- MENU ----------------
    if state == "menu":
        draw_menu_background()

        title = font_big.render("SPACE SHOOTER", True, (255, 255, 255))
        window.blit(title, (180, 60))

        buttons = {
            "easy": (Rect(250, 140, 200, 40), (100, 255, 100)),
            "normal": (Rect(250, 220, 200, 40), (255, 255, 100)),
            "hard": (Rect(250, 300, 200, 40), (255, 120, 120)),
            "infinite": (Rect(250, 380, 200, 40), (120, 180, 255)),
            "realistic": (Rect(250, 460, 200, 40), (180, 180, 180)),
        }

        for name, (rect, color) in buttons.items():
            draw.rect(window, color, rect, border_radius=12)
            if rect.collidepoint(mouse_pos):
                draw.rect(window, (255, 255, 255), rect, 2, border_radius=12)

            window.blit(font_small.render(name.upper(), True, (0, 0, 0)),
                        (rect.x + 10, rect.y + 5))

        if mouse.get_pressed()[0]:
            for name, (rect, _) in buttons.items():
                if rect.collidepoint(mouse_pos):
                    difficulty = name
                    start_game(name)
                    state = "game"
                    paused = False

        display.update()
        clock.tick(FPS)
        continue

    # ---------------- GAME ----------------
    if state == "game":
        window.blit(background, (0, 0))

        if paused:
            pause_text = font_big.render("PAUSED", True, (255, 255, 255))
            info_text = font_small.render("Press ESC to continue", True, (200, 200, 200))

            window.blit(pause_text, (250, 180))
            window.blit(info_text, (220, 250))

            display.update()
            clock.tick(FPS)
            continue

        # 💥 PARTICLES
        for p in particles[:]:
            p.update()
            if p.life <= 0:
                particles.remove(p)
            else:
                p.draw(window)

        player.update(difficulty)
        bullets.update()
        enemies.update()
        asteroids.update()

        for enemy in enemies:
            if enemy.update():
                missed += 1

        for bullet in bullets:
            hits_list = sprite.spritecollide(bullet, enemies, False)
            if hits_list:
                bullet.kill()
                for enemy in hits_list:
                    spawn_explosion(enemy.rect.centerx, enemy.rect.centery)
                    enemy.rect.y = randint(-150, -50)
                    hits += 1

        if sprite.spritecollide(player, asteroids, False):
            state = "lose"

        player.draw(window)
        enemies.draw(window)
        bullets.draw(window)
        asteroids.draw(window)

        max_miss = settings[difficulty]["miss"]
        win_hits = settings[difficulty]["hits"]

        window.blit(font_small.render(f"Hits: {hits}/{win_hits}", True, (255, 255, 255)), (10, 10))
        window.blit(font_small.render(f"Missed: {missed}/{max_miss}", True, (255, 255, 255)), (10, 35))

        if difficulty == "realistic":
            window.blit(font_small.render(f"Reload: {player.ammo}/{player.max_ammo}", True, (255, 255, 255)), (10, 60))

            if player.reloading:
                window.blit(font_small.render("Reloading..", True, (255, 100, 100)), (10, 85))

        if missed >= max_miss:
            state = "lose"

        if win_hits is not None and hits >= win_hits:
            state = "win"

        display.update()
        clock.tick(FPS)

    # ---------------- LOSE ----------------
    if state == "lose":
        window.blit(background, (0, 0))
        window.blit(font_big.render("YOU LOST", True, (255, 80, 80)), (250, 150))
        window.blit(font_small.render("Press SPACE to respawn", True, (255, 255, 255)), (220, 260))
        window.blit(font_small.render("Press M to menu", True, (255, 255, 255)), (250, 290))
        display.update()
        clock.tick(FPS)

    # ---------------- WIN ----------------
    if state == "win":
        window.blit(background, (0, 0))
        window.blit(font_big.render("YOU WIN!", True, (80, 255, 120)), (250, 180))
        window.blit(font_small.render("Press SPACE to replay", True, (255, 255, 255)), (220, 260))
        window.blit(font_small.render("Press M to menu", True, (255, 255, 255)), (250, 290))
        display.update()
        clock.tick(FPS)

quit()