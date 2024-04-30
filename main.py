import pygame
import random
import asyncio
from sys import exit

# Constants
DISPLAY_WIDTH = 576
DISPLAY_HEIGHT = 1024
FPS = 120
FONT_SIZE = 50
FONT_ANTIALIAS = False
SOUND_FREQ = 44100
SOUND_SIZE = -16
SOUND_CHANNELS = 2
SOUND_BUFFER = 512
COLOR_RGB = [255, 255, 255]
SCORE_X = DISPLAY_WIDTH / 2
SCORE_Y = 100
HIGHSCORE_Y = 850
FLOOR_HEIGHT = 900
FLOOR_SPEED = 1
GRAVITY_COEFF = 0.25
BIRD_START_X = 100
BIRD_START_Y = DISPLAY_HEIGHT / 2
BIRD_START_SPEED = -10
BIRD_ROTATION_COEFF = 3
BIRD_FLAP_POWER = 7
BIRD_FLAP_FREQ = 300
PIPE_START_X = DISPLAY_WIDTH + 200
PIPE_HEIGHTS = [400, 600, 800]
PIPE_MARGIN = 300
PIPE_SPEED = 5
PIPE_FREQ = 1200
POWER_UP_FREQ = 3000
POWER_UPS = ['double_score']
power_up_active = None
power_up_timer = 0
power_up_rect = None

# Events
SPAWNPIPE_EVT = pygame.USEREVENT
BIRD_FLAP_EVT = pygame.USEREVENT + 1
SPAWNPOWERUP_EVT = pygame.USEREVENT + 2

pygame.mixer.pre_init(SOUND_FREQ, SOUND_SIZE, SOUND_CHANNELS, SOUND_BUFFER)
pygame.init()
pygame.font.init()
screen = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
clock = pygame.time.Clock()
game_font = pygame.font.Font('assets/04B_19.TTF', FONT_SIZE)

# Game Variables
gravity = GRAVITY_COEFF
bird_speed = BIRD_START_SPEED
game_active = False
game_score = 0
high_score = 0
bird_flap_index = 0
floor_x = 0
pipe_rect_list = []
power_up_rect = None
power_up_type = None

# Load assets
bg_surface = pygame.transform.scale2x(pygame.image.load('assets/background-day.png').convert())
floor_surface = pygame.transform.scale2x(pygame.image.load('assets/base.png').convert())
bird_flaps = [
    pygame.transform.scale2x(pygame.image.load('assets/bluebird-downflap.png').convert_alpha()),
    pygame.transform.scale2x(pygame.image.load('assets/bluebird-midflap.png').convert_alpha()),
    pygame.transform.scale2x(pygame.image.load('assets/bluebird-upflap.png').convert_alpha())
]
bird_surface = bird_flaps[bird_flap_index]
bird_rect = bird_surface.get_rect(center=(BIRD_START_X, BIRD_START_Y))
pipe_surfaces = [
    pygame.transform.scale2x(pygame.image.load('assets/pipe-red.png').convert()),
    pygame.transform.scale2x(pygame.image.load('assets/pipe-green.png').convert())
]
greeting_surface = pygame.transform.scale2x(pygame.image.load('assets/message.png').convert_alpha())
greeting_rect = greeting_surface.get_rect(center=(DISPLAY_WIDTH / 2, DISPLAY_HEIGHT / 2))

# Sounds
flap_sound = pygame.mixer.Sound('sound/sfx_wing.wav')
game_score_sound = pygame.mixer.Sound('sound/sfx_point.wav')
die_sound = pygame.mixer.Sound('sound/sfx_die.wav')
collision_sound = pygame.mixer.Sound('sound/sfx_hit.wav')
swooshing_sound = pygame.mixer.Sound('sound/sfx_swooshing.wav')

# Timer setups
pygame.time.set_timer(SPAWNPIPE_EVT, PIPE_FREQ)
pygame.time.set_timer(BIRD_FLAP_EVT, BIRD_FLAP_FREQ)
#pygame.time.set_timer(SPAWNPOWERUP_EVT, POWER_UP_FREQ)

pipe_count = 0  # Initialize a counter for pipes at the start of your program


# Game functions
def draw_floor():
    screen.blit(floor_surface, (floor_x, FLOOR_HEIGHT))
    screen.blit(floor_surface, (floor_x + DISPLAY_WIDTH, FLOOR_HEIGHT))

def bird_animation():
    global bird_flap_index, bird_surface, bird_rect  # Include bird_surface and bird_rect
    bird_flap_index = (bird_flap_index + 1) % 3
    bird_surface = bird_flaps[bird_flap_index]  # This updates the global variable
    bird_rect = bird_surface.get_rect(center=(BIRD_START_X, bird_rect.centery))
    return bird_surface, bird_rect


def rotate_bird(bird):
    new_surface = pygame.transform.rotozoom(bird, -bird_speed * BIRD_ROTATION_COEFF, 1)
    return new_surface

def draw_bird(bird):
    global bird_rect  # This ensures you are modifying the global bird_rect if needed
    screen.blit(bird, bird_rect)



def move_pipes(pipes):
    for pipe_rect in pipes:
        pipe_rect.centerx -= PIPE_SPEED
    return pipes

def draw_pipes(pipes):
    for pipe_rect in pipes:
        if pipe_rect.top < 0:
            flipped_pipe = pygame.transform.flip(pipe_surfaces[0], False, True)
            screen.blit(flipped_pipe, pipe_rect)
        else:
            screen.blit(pipe_surfaces[0], pipe_rect)

def create_pipe():
    global pipe_count, power_up_rect  # Use global to modify the pipe_count
    pipe_height = random.choice(PIPE_HEIGHTS)
    bottom_pipe = pipe_surfaces[0].get_rect(midtop=(PIPE_START_X, pipe_height))
    upper_pipe = pipe_surfaces[0].get_rect(midbottom=(PIPE_START_X, pipe_height - PIPE_MARGIN))
    pipe_count += 1  # Increment the pipe counter

    # Check if it's time to spawn a power-up
    if pipe_count % 7 == 0:  # Every 7 pipes, spawn a power-up
        create_power_up()

    return bottom_pipe, upper_pipe


def check_collisions(pipes):
    for pipe in pipes:
        if bird_rect.colliderect(pipe):
            collision_sound.play()
            return False
    if bird_rect.top <= -100 or bird_rect.bottom >= FLOOR_HEIGHT:
        die_sound.play()
        return False
    return True

def draw_score():
    score_surface = game_font.render(str(game_score), True, COLOR_RGB)
    score_rect = score_surface.get_rect(center=(SCORE_X, SCORE_Y))
    screen.blit(score_surface, score_rect)

def draw_highscore():
    highscore_surface = game_font.render(f'High Score: {int(high_score)}', True, COLOR_RGB)
    highscore_rect = highscore_surface.get_rect(center=(SCORE_X, HIGHSCORE_Y))
    screen.blit(highscore_surface, highscore_rect)

def reset_game():
    global bird_speed, game_score, game_active, pipe_rect_list, power_up_active, power_up_timer, power_up_rect, pipe_count, PIPE_SPEED, gravity
    bird_speed = BIRD_START_SPEED
    game_score = 0
    bird_rect.center = (BIRD_START_X, BIRD_START_Y)
    pipe_rect_list.clear()
    power_up_active = None
    power_up_timer = 0
    power_up_rect = None
    pipe_count = 0  # Reset the pipe counter
    PIPE_SPEED = 5  # Reset the pipe speed to the initial value
    gravity = GRAVITY_COEFF  # Reset gravity to its initial value, if it was ever changed
    game_active = True


def update_highscore():
    global high_score
    if game_score > high_score:
        high_score = game_score

def exit_app():
    pygame.quit()
    exit()

def create_power_up():
    global power_up_rect, power_up_type
    if power_up_rect is None:  # Only create a new power-up if there isn't already one
        power_up_type = random.choice(POWER_UPS)
        bird_width, bird_height = bird_surface.get_size()
        # Spawn at the right side of the screen
        power_up_rect = pygame.Rect(DISPLAY_WIDTH, (DISPLAY_HEIGHT - bird_height) // 2, bird_width, bird_height)


def move_power_up():
    if power_up_rect:
        power_up_rect.x -= PIPE_SPEED  # Move the power-up at the same speed as pipes
        if power_up_rect.right < 0:  # If the power-up has moved past the screen, reset it
            reset_power_up()  # Optionally reset or remove the power-up

def check_power_up_collision():
    global power_up_active
    if power_up_rect and bird_rect.colliderect(power_up_rect):
        activate_power_up()
        reset_power_up()  # Optionally remove the power-up after activation or move it off-screen



def activate_power_up():
    global power_up_active, power_up_timer, PIPE_SPEED, gravity, game_score
    power_up_active = power_up_type
    power_up_timer = pygame.time.get_ticks()  # Start the timer for the power-up effect

    # Apply immediate effects based on power-up type
    if power_up_active == 'speed_boost':
        PIPE_SPEED = 3  # Example: Increase speed temporarily
    elif power_up_active == 'double_score':
        game_score *= 2  # Example: Immediate score boost


def reset_power_up():
    global power_up_rect, power_up_active, power_up_timer, PIPE_SPEED, gravity
    power_up_rect = None
    power_up_active = None
    power_up_timer = 0
    PIPE_SPEED = 5  # Reset the pipe speed here as well, to ensure consistency
    gravity = GRAVITY_COEFF  # Reset gravity if modified by any power-up

def update_power_up_effects():
    global PIPE_SPEED, game_score, gravity, power_up_active, power_up_timer
    if power_up_active:
        current_time = pygame.time.get_ticks()
        if current_time - power_up_timer > 5000:  # 5 seconds duration for power-ups
            if power_up_active == 'speed_boost':
                PIPE_SPEED = 5  # Reset to original speed
            elif power_up_active == 'double_score':
                # Assuming you want to revert any score doubling effect here
                # Implement logic as needed if scores are adjusted dynamically
                pass
            power_up_active = None



def draw_power_ups():
    if power_up_rect and power_up_type:
        power_up_image = pygame.image.load(f'assets/{power_up_type}.png').convert_alpha()
        power_up_image = pygame.transform.scale(power_up_image, (power_up_rect.width, power_up_rect.height))  # Scale the image to bird size
        screen.blit(power_up_image, power_up_rect)


async def main():
    global game_active, pipe_rect_list, floor_x, bird_speed, game_score, gravity, bird_rect, bird_surface, power_up_rect

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_app()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if not game_active:
                        reset_game()
                    else:
                        bird_speed = 0
                        bird_speed -= BIRD_FLAP_POWER
                        flap_sound.play()
                if event.key == pygame.K_ESCAPE:
                    exit_app()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if not game_active:
                    reset_game()
                else:
                    bird_speed = 0
                    bird_speed -= BIRD_FLAP_POWER
                    flap_sound.play()
            if event.type == SPAWNPIPE_EVT:
                if game_active:
                    pipe_rect_list.extend(create_pipe())
            if event.type == BIRD_FLAP_EVT:
                if game_active:
                    bird_surface, bird_rect = bird_animation()
            if event.type == SPAWNPOWERUP_EVT:
                if game_active and power_up_rect is None:  # Check to avoid overlapping power-ups
                    create_power_up()

        screen.blit(bg_surface, (0, 0))

        if game_active:
            update_power_up_effects()
            bird_speed += gravity
            bird_rect.centery += bird_speed
            bird_rotated = rotate_bird(bird_surface)
            draw_bird(bird_rotated)

            game_active = check_collisions(pipe_rect_list)

            pipe_rect_list = move_pipes(pipe_rect_list)
            draw_pipes(pipe_rect_list)

            if power_up_rect:
                check_power_up_collision()
                move_power_up()
                draw_power_ups()

            game_score += 1
        else:
            draw_highscore()
            screen.blit(greeting_surface, greeting_rect)

        draw_score()

        floor_x -= FLOOR_SPEED
        if floor_x <= -DISPLAY_WIDTH:
            floor_x = 0
        draw_floor()

        pygame.display.update()
        clock.tick(FPS)
        await asyncio.sleep(0)

asyncio.run(main())
