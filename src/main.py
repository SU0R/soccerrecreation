import asyncio
import math
import time

import pygame


WIDTH = 800
HEIGHT = 575
FIELD_TOP = 5
FIELD_LEFT = 50
FIELD_RIGHT = 750
FIELD_BOTTOM = 500
FPS = 60
MATCH_SECONDS = 180

RED = (222, 47, 50)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 116, 54)
DARK_GREEN = (43, 91, 44)
BLUE = (35, 94, 230)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
MAROON = (95, 53, 65)
DARK_MAROON = (47, 34, 38)
BOX_MAROON = (128, 0, 0)
GOLD = (203, 187, 125)


def clamp(value, low, high):
    return max(low, min(high, value))


class GameState:
    """Small serializable-ish state object so realtime multiplayer can sync later."""

    def __init__(self):
        self.player_size = 25
        self.speed = 1.7
        self.ball_speed = 4.2
        self.start_time = time.time()
        self.paused_at_end = False
        self.blue_score = 0
        self.red_score = 0
        self.message = "Click a player key, then click a target. V shoots."
        self.message_until = time.time() + 4

        self.players = {
            "b1": pygame.Rect(250, 100, self.player_size, self.player_size),
            "b2": pygame.Rect(250, 400, self.player_size, self.player_size),
            "b3": pygame.Rect(405, 238, self.player_size, self.player_size),
            "r1": pygame.Rect(550, 400, self.player_size, self.player_size),
            "r2": pygame.Rect(600, 238, self.player_size, self.player_size),
            "r3": pygame.Rect(550, 100, self.player_size, self.player_size),
        }
        self.targets = {name: rect.center for name, rect in self.players.items()}
        self.keepers = {
            "blue": pygame.Rect(60, 232, 20, 40),
            "red": pygame.Rect(700, 232, 20, 40),
        }
        self.ball = pygame.Vector2(400, 250)
        self.ball_target = pygame.Vector2(400, 250)
        self.ball_owner = "b3"
        self.selected_player = None
        self.shooting = False
        self.last_scored_at = 0

    def reset_positions(self, kickoff_owner):
        self.players["b1"].topleft = (250, 100)
        self.players["b2"].topleft = (250, 400)
        self.players["b3"].topleft = (200, 238)
        self.players["r1"].topleft = (550, 400)
        self.players["r2"].topleft = (600, 238)
        self.players["r3"].topleft = (550, 100)
        self.targets = {name: rect.center for name, rect in self.players.items()}
        self.keepers["blue"].topleft = (60, 232)
        self.keepers["red"].topleft = (700, 232)
        self.ball_owner = kickoff_owner
        self.ball = pygame.Vector2(self.players[kickoff_owner].center)
        self.ball_target = self.ball.copy()
        self.selected_player = None
        self.shooting = False

    def show_message(self, text, seconds=2.5):
        self.message = text
        self.message_until = time.time() + seconds

    def time_left(self):
        return max(0, MATCH_SECONDS - int(time.time() - self.start_time))


class SoccerGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Soccer Game!")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 22)
        self.small_font = pygame.font.Font(None, 18)
        self.number_font = pygame.font.Font(None, 48)
        self.time_font = pygame.font.Font(None, 34)
        self.state = GameState()

        self.bounds = [
            pygame.Rect(45, 0, 5, 150),
            pygame.Rect(45, 350, 5, 150),
            pygame.Rect(750, 0, 5, 150),
            pygame.Rect(750, 350, 5, 150),
            pygame.Rect(45, 0, 705, 5),
            pygame.Rect(45, 495, 705, 5),
        ]
        self.dark_stripes = [
            pygame.Rect(50, 5, 70, 490),
            pygame.Rect(190, 5, 70, 490),
            pygame.Rect(330, 5, 70, 490),
            pygame.Rect(470, 5, 70, 490),
            pygame.Rect(610, 5, 70, 490),
        ]
        self.lines = [
            pygame.Rect(397, 5, 5, 490),
            pygame.Rect(0, 150, 50, 5),
            pygame.Rect(0, 150, 5, 200),
            pygame.Rect(0, 350, 50, 5),
            pygame.Rect(750, 150, 50, 5),
            pygame.Rect(750, 350, 50, 5),
            pygame.Rect(797, 150, 5, 200),
        ]
        self.blue_goal = pygame.Rect(0, 150, 50, 200)
        self.red_goal = pygame.Rect(750, 150, 50, 200)

    async def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self.handle_event(event)

            self.update(dt)
            self.draw()
            pygame.display.flip()
            await asyncio.sleep(0)

        pygame.quit()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            self.handle_key(event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.handle_click(event.pos)

    def handle_key(self, key):
        player_keys = {
            pygame.K_q: "b1",
            pygame.K_w: "b2",
            pygame.K_e: "b3",
            pygame.K_i: "r1",
            pygame.K_o: "r2",
            pygame.K_p: "r3",
        }
        pass_keys = {
            pygame.K_f: "b1",
            pygame.K_s: "b2",
            pygame.K_d: "b3",
            pygame.K_m: "r1",
            pygame.K_j: "r2",
            pygame.K_k: "r3",
        }
        if key in player_keys:
            self.state.selected_player = player_keys[key]
            self.state.shooting = False
            self.state.show_message(f"Selected {player_keys[key].upper()}. Click the field to move.")
        elif key in pass_keys:
            self.pass_to(pass_keys[key])
        elif key == pygame.K_x:
            self.try_steal("blue")
        elif key == pygame.K_l:
            self.try_steal("red")
        elif key == pygame.K_v:
            self.state.shooting = True
            self.state.selected_player = None
            self.state.ball_owner = None
            self.state.ball_target = self.state.ball.copy()
            self.state.show_message("Shooting: click where the ball should go.")
        elif key == pygame.K_r:
            self.state = GameState()

    def handle_click(self, pos):
        x = clamp(pos[0], 15, WIDTH - 15)
        y = clamp(pos[1], 15, FIELD_BOTTOM - 15)
        if self.state.shooting:
            self.state.ball_target = pygame.Vector2(x, y)
            self.state.shooting = False
            return
        if self.state.selected_player:
            self.state.targets[self.state.selected_player] = (x, y)

    def pass_to(self, player_name):
        if player_name[0] == "b" and self.state.ball_owner and self.state.ball_owner[0] == "b":
            self.state.ball_owner = player_name
            self.state.show_message(f"Blue pass to {player_name.upper()}.")
        elif player_name[0] == "r" and self.state.ball_owner and self.state.ball_owner[0] == "r":
            self.state.ball_owner = player_name
            self.state.show_message(f"Red pass to {player_name.upper()}.")

    def try_steal(self, team):
        candidates = ["b1", "b2", "b3"] if team == "blue" else ["r1", "r2", "r3"]
        closest = min(candidates, key=lambda name: self.distance_to_ball(self.state.players[name]))
        if self.distance_to_ball(self.state.players[closest]) < 60:
            self.state.ball_owner = closest
            self.state.shooting = False
            self.state.show_message(f"{closest.upper()} wins possession.")

    def distance_to_ball(self, rect):
        return math.hypot(rect.centerx - self.state.ball.x, rect.centery - self.state.ball.y)

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.move_keepers(keys)
        if self.state.time_left() <= 0:
            self.state.paused_at_end = True
            return

        for name, rect in self.state.players.items():
            self.move_rect_toward(rect, pygame.Vector2(self.state.targets[name]), self.state.speed)
            rect.x = int(clamp(rect.x, FIELD_LEFT, FIELD_RIGHT - rect.width))
            rect.y = int(clamp(rect.y, FIELD_TOP, FIELD_BOTTOM - rect.height))

        if self.state.ball_owner:
            owner = self.state.players[self.state.ball_owner]
            self.state.ball.update(owner.centerx, owner.centery)
            self.state.ball_target = self.state.ball.copy()
        else:
            direction = self.state.ball_target - self.state.ball
            if direction.length() > self.state.ball_speed:
                self.state.ball += direction.normalize() * self.state.ball_speed
            else:
                self.state.ball = self.state.ball_target.copy()

        self.check_keeper_saves()
        self.check_goals()

    def move_keepers(self, keys):
        if keys[pygame.K_a]:
            self.state.keepers["blue"].y -= 2
        if keys[pygame.K_z]:
            self.state.keepers["blue"].y += 2
        if keys[pygame.K_h]:
            self.state.keepers["red"].y -= 2
        if keys[pygame.K_n]:
            self.state.keepers["red"].y += 2
        for keeper in self.state.keepers.values():
            keeper.y = int(clamp(keeper.y, 150, 350 - keeper.height))

    def move_rect_toward(self, rect, target, speed):
        current = pygame.Vector2(rect.center)
        direction = target - current
        if direction.length() > speed:
            current += direction.normalize() * speed
            rect.center = (round(current.x), round(current.y))

    def ball_rect(self):
        return pygame.Rect(int(self.state.ball.x - 10), int(self.state.ball.y - 10), 20, 20)

    def check_keeper_saves(self):
        ball_rect = self.ball_rect()
        if self.state.keepers["blue"].colliderect(ball_rect):
            self.state.ball_owner = "b3"
            self.state.show_message("Blue keeper save!")
        elif self.state.keepers["red"].colliderect(ball_rect):
            self.state.ball_owner = "r2"
            self.state.show_message("Red keeper save!")

    def check_goals(self):
        if time.time() - self.state.last_scored_at < 1:
            return
        ball_rect = self.ball_rect()
        if self.blue_goal.colliderect(ball_rect):
            self.state.red_score += 1
            self.state.last_scored_at = time.time()
            self.state.show_message("Goal for Red!")
            self.state.reset_positions("b3")
        elif self.red_goal.colliderect(ball_rect):
            self.state.blue_score += 1
            self.state.last_scored_at = time.time()
            self.state.show_message("Goal for Blue!")
            self.state.reset_positions("r2")

    def draw(self):
        self.screen.fill(GREEN)
        for stripe in self.dark_stripes:
            pygame.draw.rect(self.screen, DARK_GREEN, stripe)
        pygame.draw.rect(self.screen, GRAY, self.blue_goal)
        pygame.draw.rect(self.screen, GRAY, self.red_goal)

        for bound in self.bounds:
            pygame.draw.rect(self.screen, WHITE, bound)
        for line in self.lines:
            pygame.draw.rect(self.screen, WHITE, line)
        pygame.draw.circle(self.screen, WHITE, (400, 250), 100, 5)
        pygame.draw.circle(self.screen, WHITE, (400, 250), 7)

        self.draw_algonquin_a(scale=1.8, xoffset=-50, yoffset=-15)
        self.draw_scoreboard()
        self.draw_players()
        pygame.draw.circle(self.screen, WHITE, (round(self.state.ball.x), round(self.state.ball.y)), 10)
        pygame.draw.circle(self.screen, BLACK, (round(self.state.ball.x), round(self.state.ball.y)), 10, 1)
        self.draw_message()

    def draw_players(self):
        for name, rect in self.state.players.items():
            color = BLUE if name[0] == "b" else RED
            pygame.draw.rect(self.screen, color, rect, border_radius=4)
            label = self.small_font.render(name.upper(), True, WHITE)
            self.screen.blit(label, label.get_rect(center=rect.center))
            if self.state.selected_player == name:
                pygame.draw.rect(self.screen, GOLD, rect.inflate(8, 8), 2, border_radius=5)

        pygame.draw.rect(self.screen, BLUE, self.state.keepers["blue"], border_radius=4)
        pygame.draw.rect(self.screen, RED, self.state.keepers["red"], border_radius=4)

    def draw_scoreboard(self):
        pygame.draw.rect(self.screen, BOX_MAROON, pygame.Rect(310, 500, 180, 75))
        pygame.draw.rect(self.screen, BOX_MAROON, pygame.Rect(45, 510, 180, 60))
        pygame.draw.rect(self.screen, BLACK, pygame.Rect(320, 530, 50, 40))
        pygame.draw.rect(self.screen, BLACK, pygame.Rect(430, 530, 50, 40))
        self.draw_algonquin_a(scale=0.65, xoffset=238, yoffset=450)

        title = self.font.render("Algonquin Titans", True, WHITE)
        teams = self.font.render("Home                 Away", True, WHITE)
        timer = self.time_font.render(f"Time: {self.state.time_left()}s", True, WHITE)
        blue_score = self.number_font.render(str(self.state.blue_score), True, WHITE)
        red_score = self.number_font.render(str(self.state.red_score), True, WHITE)

        self.screen.blit(title, title.get_rect(center=(400, 513)))
        self.screen.blit(teams, teams.get_rect(center=(400, 532)))
        self.screen.blit(timer, (58, 528))
        self.screen.blit(blue_score, blue_score.get_rect(center=(345, 550)))
        self.screen.blit(red_score, red_score.get_rect(center=(455, 550)))

        if self.state.paused_at_end:
            if self.state.blue_score > self.state.red_score:
                result = "Blue wins!"
            elif self.state.red_score > self.state.blue_score:
                result = "Red wins!"
            else:
                result = "Tie game!"
            text = self.time_font.render(result, True, GOLD)
            self.screen.blit(text, text.get_rect(center=(400, 285)))

    def draw_message(self):
        if time.time() > self.state.message_until:
            return
        surface = self.font.render(self.state.message, True, WHITE)
        bg = pygame.Rect(0, 0, surface.get_width() + 24, surface.get_height() + 12)
        bg.center = (400, 30)
        pygame.draw.rect(self.screen, BLACK, bg, border_radius=6)
        pygame.draw.rect(self.screen, GOLD, bg, 1, border_radius=6)
        self.screen.blit(surface, surface.get_rect(center=bg.center))

    def draw_algonquin_a(self, scale, xoffset, yoffset):
        points = lambda coords: [((x * scale) + xoffset, (y * scale) + yoffset) for x, y in coords]
        pygame.draw.polygon(
            self.screen,
            MAROON,
            points([(228, 124), (260, 123), (263, 126), (279, 169), (218, 169), (233, 130)]),
        )
        pygame.draw.polygon(
            self.screen,
            DARK_GREEN,
            points([(238.5, 169), (241, 162), (253.5, 155), (258, 169.5)]),
        )
        pygame.draw.polygon(self.screen, DARK_GREEN, points([(248.5, 140), (244, 153), (253, 153)]))
        pygame.draw.polygon(
            self.screen,
            DARK_MAROON,
            points(
                [
                    (242.5, 130),
                    (255, 130),
                    (244, 153),
                    (253, 153.5),
                    (241, 162),
                    (238.5, 169),
                ]
            ),
        )
        pygame.draw.polygon(self.screen, DARK_MAROON, points([(228, 124), (233, 130), (242.5, 130)]))
        pygame.draw.polygon(
            self.screen,
            DARK_MAROON,
            points([(258, 169.5), (267, 163), (255, 130), (263, 126), (279, 169)]),
        )
        outline = [
            (228, 124),
            (263, 126),
            (279, 169),
            (258, 169.5),
            (253.5, 155),
            (241, 162),
            (238.5, 169),
            (218, 169),
            (233, 130),
            (228, 124),
        ]
        pygame.draw.lines(self.screen, GOLD, False, points(outline), 2)
        pygame.draw.lines(self.screen, GOLD, True, points([(248.5, 140), (253, 153.5), (244, 153)]), 2)


async def main():
    await SoccerGame().run()


if __name__ == "__main__":
    asyncio.run(main())
