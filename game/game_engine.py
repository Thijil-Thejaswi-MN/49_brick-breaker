import pygame
from .paddle import Paddle
from .ball import Ball
from .brick import Brick

# Game Engine

WHITE = (255, 255, 255)
BG = (15, 15, 25)
BRICK_COLORS = [
    (200, 60, 60),
    (200, 140, 60),
    (200, 200, 60),
    (80, 180, 80),
    (80, 140, 200),
]


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.paddle = Paddle(width // 2 - 50, height - 30, 100, 14)

        self.ball = Ball(width // 2, height - 50, radius=8)
        self.ball.vx, self.ball.vy = 4, -4

        self.rows, self.cols = 5, 8
        self.bricks = self._build_bricks(self.rows, self.cols)

        self.lives = 3
        self.score = 0
        self.font = pygame.font.SysFont("Arial", 28)
        self.end_title_font = pygame.font.SysFont("Arial", 48, bold=True)
        self.end_score_font = pygame.font.SysFont("Arial", 32, bold=True)
        self.end_hint_font = pygame.font.SysFont("Arial", 22)
        self.menu_font = pygame.font.SysFont("Arial", 20)
        self.game_over = False
        self.result = None  # "win" or "lose"

        # Task 3: default to Medium for the first game.
        self.difficulty = "Medium"
        self.ball_speed = 4
        self.paddle_width = 100

    def _build_bricks(self, rows, cols):
        bricks = []
        margin, gap, top = 30, 6, 60
        brick_w = (self.width - margin * 2 - gap * (cols - 1)) // cols
        brick_h = 22
        for r in range(rows):
            for c in range(cols):
                x = margin + c * (brick_w + gap)
                y = top + r * (brick_h + gap)
                bricks.append(Brick(x, y, brick_w, brick_h))
        return bricks

    def handle_event(self, event):
        """Handle end-screen choices without changing normal paddle input."""
        if not self.game_over or event.type != pygame.KEYDOWN:
            return

        key = event.key
        if key in (pygame.K_1, pygame.K_e):
            self._start_new_game("Easy")
        elif key in (pygame.K_2, pygame.K_m):
            self._start_new_game("Medium")
        elif key in (pygame.K_3, pygame.K_h):
            self._start_new_game("Hard")
        elif key in (pygame.K_4, pygame.K_q, pygame.K_ESCAPE):
            # main.py already handles pygame.QUIT, so post that event to
            # close through the existing application event loop.
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def _start_new_game(self, difficulty):
        """Reset all gameplay state and apply the chosen difficulty."""
        settings = {
            "Easy": {"ball_speed": 3, "paddle_width": 120},
            "Medium": {"ball_speed": 4, "paddle_width": 100},
            "Hard": {"ball_speed": 6, "paddle_width": 80},
        }
        selected = settings[difficulty]
        self.difficulty = difficulty
        self.ball_speed = selected["ball_speed"]
        self.paddle_width = selected["paddle_width"]

        # Restore a centered paddle with the selected size.
        self.paddle.width = self.paddle_width
        self.paddle.x = (self.width - self.paddle.width) // 2
        self.paddle.y = self.height - 30

        # Recreate the ball and all bricks, and reset round counters.
        self.ball.x = self.width // 2
        self.ball.y = self.height - 50
        self.ball.vx = self.ball_speed
        self.ball.vy = -self.ball_speed
        self.bricks = self._build_bricks(self.rows, self.cols)
        self.lives = 3
        self.score = 0
        self.game_over = False
        self.result = None

    def handle_input(self):
        if self.game_over:
            return
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.paddle.move(-self.paddle.speed, self.width)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.paddle.move(self.paddle.speed, self.width)

    def _resolve_ball_collision(self, target_rect, previous_ball_rect):
        """Resolve a ball/rectangle collision using the side of entry.

        The ball is represented by an axis-aligned rectangle for collision
        detection. Its previous rectangle helps distinguish a side hit from
        a top/bottom hit. A minimum-penetration fallback handles corner or
        already-overlapping cases and moves the ball out of the target.
        """
        current_ball_rect = self.ball.rect()
        if not current_ball_rect.colliderect(target_rect):
            return False

        radius = self.ball.radius

        # The ball crossed the top or bottom edge of the target.
        if previous_ball_rect.bottom <= target_rect.top and self.ball.vy > 0:
            self.ball.y = target_rect.top - radius
            self.ball.vy = -abs(self.ball.vy)
        elif previous_ball_rect.top >= target_rect.bottom and self.ball.vy < 0:
            self.ball.y = target_rect.bottom + radius
            self.ball.vy = abs(self.ball.vy)

        # The ball crossed the left or right edge of the target.
        elif previous_ball_rect.right <= target_rect.left and self.ball.vx > 0:
            self.ball.x = target_rect.left - radius
            self.ball.vx = -abs(self.ball.vx)
        elif previous_ball_rect.left >= target_rect.right and self.ball.vx < 0:
            self.ball.x = target_rect.right + radius
            self.ball.vx = abs(self.ball.vx)

        else:
            # Fallback for corner impacts or an overlap that already existed.
            overlap_left = current_ball_rect.right - target_rect.left
            overlap_right = target_rect.right - current_ball_rect.left
            overlap_top = current_ball_rect.bottom - target_rect.top
            overlap_bottom = target_rect.bottom - current_ball_rect.top
            penetration_x = min(overlap_left, overlap_right)
            penetration_y = min(overlap_top, overlap_bottom)

            if penetration_x < penetration_y:
                if self.ball.x < target_rect.centerx:
                    self.ball.x = target_rect.left - radius
                    self.ball.vx = -abs(self.ball.vx)
                else:
                    self.ball.x = target_rect.right + radius
                    self.ball.vx = abs(self.ball.vx)
            else:
                if self.ball.y < target_rect.centery:
                    self.ball.y = target_rect.top - radius
                    self.ball.vy = -abs(self.ball.vy)
                else:
                    self.ball.y = target_rect.bottom + radius
                    self.ball.vy = abs(self.ball.vy)

        return True

    def update(self):
        if self.game_over:
            return

        # Keep the previous position to determine which side is struck.
        previous_ball_rect = self.ball.rect()
        self.ball.move()

        # Resolve side-wall collisions and clamp the ball inside the window
        # so it cannot repeatedly reverse while already beyond a wall.
        if self.ball.x - self.ball.radius <= 0:
            self.ball.x = self.ball.radius
            if self.ball.vx < 0:
                self.ball.vx = abs(self.ball.vx)
        elif self.ball.x + self.ball.radius >= self.width:
            self.ball.x = self.width - self.ball.radius
            if self.ball.vx > 0:
                self.ball.vx = -abs(self.ball.vx)

        if self.ball.y - self.ball.radius <= 0:
            self.ball.y = self.ball.radius
            if self.ball.vy < 0:
                self.ball.vy = abs(self.ball.vy)

        # Resolve the paddle collision from the actual side of impact.
        self._resolve_ball_collision(self.paddle.rect(), previous_ball_rect)

        # Destroy at most one brick per frame, and only score once per brick.
        for brick in self.bricks:
            if brick.alive and self._resolve_ball_collision(
                brick.rect(), previous_ball_rect
            ):
                brick.alive = False
                self.score += 1
                break

        if self.ball.y - self.ball.radius > self.height:
            self.lives -= 1
            if self.lives <= 0:
                self.game_over = True
                self.result = "lose"
            else:
                self._reset_ball()

        if all(not b.alive for b in self.bricks):
            self.game_over = True
            self.result = "win"

    def _reset_ball(self):
        self.ball.x, self.ball.y = self.width // 2, self.height - 50
        self.ball.vx, self.ball.vy = self.ball_speed, -self.ball_speed

    def render(self, screen):
        screen.fill(BG)

        pygame.draw.rect(screen, WHITE, self.paddle.rect())
        pygame.draw.circle(screen, WHITE, (int(self.ball.x), int(self.ball.y)), self.ball.radius)

        for i, brick in enumerate(self.bricks):
            if brick.alive:
                row = i // self.cols
                color = BRICK_COLORS[row % len(BRICK_COLORS)]
                pygame.draw.rect(screen, color, brick.rect())

        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        lives_text = self.font.render(f"Lives: {self.lives}", True, WHITE)
        screen.blit(lives_text, (self.width - 130, 10))

        # Task 2: display the result inside the game window rather than
        # printing it to the terminal. update() and handle_input() already
        # stop normal gameplay once game_over becomes True.
        if self.game_over:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((5, 8, 16, 220))
            screen.blit(overlay, (0, 0))

            if self.result == "win":
                title = "YOU WIN!"
                title_color = (100, 235, 130)
            else:
                title = "GAME OVER"
                title_color = (255, 105, 105)

            title_surface = self.end_title_font.render(title, True, title_color)
            score_surface = self.end_score_font.render(
                f"Final Score: {self.score}", True, WHITE
            )
            difficulty_surface = self.menu_font.render(
                "Replay: 1/E Easy    2/M Medium    3/H Hard",
                True,
                (210, 215, 225),
            )
            quit_surface = self.menu_font.render(
                "Quit: 4 / Q / Esc",
                True,
                (210, 215, 225),
            )

            screen.blit(
                title_surface,
                title_surface.get_rect(center=(self.width // 2, self.height // 2 - 100)),
            )
            screen.blit(
                score_surface,
                score_surface.get_rect(center=(self.width // 2, self.height // 2 - 40)),
            )
            screen.blit(
                difficulty_surface,
                difficulty_surface.get_rect(center=(self.width // 2, self.height // 2 + 20)),
            )
            screen.blit(
                quit_surface,
                quit_surface.get_rect(center=(self.width // 2, self.height // 2 + 55)),
            )
