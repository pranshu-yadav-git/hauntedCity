from ursina import *
from math import sin, cos, radians

app = Ursina()
# Ambrish Addition
# === CONFIG ===
normal_speed = 5
sprint_speed = 10
sensitivity = 100
jump_height = 6
gravity = 20
max_pitch = 89
pitch = 0
yaw = 0
eye_height = 1.8
player_points = 0
velocity_y = 0
is_grounded = False
game_over = False
fall_check_enabled = False  # Delay fall detection
# ==============

window.title = "Haunted City - FPS"
mouse.locked = True
window.color = color.black
window.fps_counter.enabled = True
window.exit_button.visible = False

Sky()

# === TERRAIN ===
ground = Entity(
    model='plane',
    scale=100,
    texture='grass',
    texture_scale=(50, 50),
    collider='mesh',
    position=(0, 0, 0)
)

DirectionalLight(y=3, z=3, shadows=True)

# === PLAYER ===
player = Entity(model='cube', scale_y=1.8, origin_y=-0.5, collider='box', position=(0, 3, 0))
player.visible = False

# === POINTS TEXT ===
points_text = Text(
    text=f'Points: {player_points}',
    position=(0.75, 0.45),
    origin=(0, 0),
    scale=1.5,
    color=color.green
)

# === GAME OVER UI ===
fall_text = Text("You Fell!", origin=(0, 0), scale=2, color=color.red, enabled=False)
restart_button = Button(
    text='Restart',
    color=color.red,
    scale=(0.2, 0.1),
    position=(0, -0.1),
    enabled=False
)

def trigger_game_over():
    global game_over
    game_over = True
    fall_text.enabled = True
    restart_button.enabled = True
    restart_button.on_click = restart_game

def restart_game():
    import os
    os.execl(sys.executable, sys.executable, *sys.argv)  # clean restart

# === POINT PICKUPS ===
point_pickups = []

class PointPickup(Entity):
    def __init__(self, position=(0, 0, 0), value=10):
        super().__init__(
            model='cube',
            color=color.green,
            scale=0.5,
            position=position,
            collider='box'
        )
        self.value = value
        point_pickups.append(self)

def spawn_points():
    positions = [(-5, 0.25, -5), (5, 0.25, -5), (-5, 0.25, 5), (5, 0.25, 5), (0, 0.25, 0)]
    for pos in positions:
        PointPickup(position=Vec3(*pos))

spawn_points()

# === DELAY FALL CHECK ===
def enable_fall_check():
    global fall_check_enabled
    fall_check_enabled = True

invoke(enable_fall_check, delay=1)  # Start checking for falling after 1 sec

# === UPDATE ===
def update():
    global pitch, yaw, velocity_y, is_grounded, player_points, game_over

    if game_over:
        return

    # === Mouse Look ===
    if mouse.locked:
        yaw += mouse.velocity[0] * sensitivity
        pitch -= mouse.velocity[1] * sensitivity
        pitch = clamp(pitch, -max_pitch, max_pitch)

    camera.rotation_x = pitch
    player.rotation_y = yaw
    camera.rotation_y = yaw
    camera.rotation_z = 0
    camera.position = player.position + Vec3(0, eye_height, 0)

    # === Movement ===
    forward = Vec3(sin(radians(yaw)), 0, cos(radians(yaw))).normalized()
    right = Vec3(forward.z, 0, -forward.x).normalized()

    move = Vec3(0, 0, 0)
    if held_keys['w']: move += forward
    if held_keys['s']: move -= forward
    if held_keys['a']: move -= right
    if held_keys['d']: move += right

    if move != Vec3(0, 0, 0):
        move = move.normalized()

    move_speed = sprint_speed if held_keys['shift'] and held_keys['w'] else normal_speed
    player.position += move * time.dt * move_speed

    # === Gravity + Jump ===
    ray = raycast(player.world_position + Vec3(0, 0.25, 0), direction=Vec3(0, -1, 0), distance=0.3, ignore=(player,))
    is_grounded = ray.hit

    if is_grounded:
        if held_keys['space']:
            velocity_y = jump_height
        else:
            velocity_y = 0
    else:
        velocity_y -= gravity * time.dt

    player.y += velocity_y * time.dt

    # === Point Pickup Collection ===
    for pickup in point_pickups[:]:
        if distance(player.position, pickup.position) < 1:
            player_points += pickup.value
            points_text.text = f'Points: {player_points}'
            pickup.disable()
            point_pickups.remove(pickup)

    # === Game Over on Fall ===
    if fall_check_enabled and player.y < -20:
        trigger_game_over()

app.run()
