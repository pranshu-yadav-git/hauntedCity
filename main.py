from ursina import *
from math import sin, cos, radians
from random import uniform

app = Ursina()
# Ambrish Addition
# === CONFIG ===
normal_speed = 5
sprint_speed = 10
sensitivity = 100  # Mouse sensitivity; adjust if unintended drift occurs
jump_height = 6
gravity = 20
max_pitch = 89
pitch = -30  # Initial camera pitch to view ground on first frame
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


is_first_person = True
pitch, yaw = 0, 0
max_pitch = 89

Sky()

# === TERRAIN ===
ground = Entity(
    model='cube',
    scale=(9980, 1, 9981),
    texture='grass3',
    texture_scale=(1690, 2160),
    collider='box',
    position=(0, 0, 0),
    # color=color.green
)

DirectionalLight(y=3, z=3, shadows=True)

# === PLAYER ===
player = Entity(model='cube', scale_y=1.8, origin_y=-0.5, collider='box', position=(0, 10, 0))
player.visible = False
player.model = 'assets/models/player.glb'

# TEMP ENTITY
# Entity(model='cube', color=color.red, position=(0, 0.5, 0), scale=0.5)

# === POINTS TEXT ===
points_text = Text(
    text=f'Points: {player_points}',
    position=(0.75, 0.45),
    origin=(0, 0),
    scale=1.5,
    color=color.green
)

# "You Fell" Screen Removed

# === POINT PICKUPS ===
point_pickups = []

class PointPickup(Entity):
    def __init__(self, position=(0, 1, 0), value=10):
        super().__init__(
            model='cube',
            color=color.green,
            scale=0.5,
            position=position,
            collider='box'
        )
        self.value = value
        point_pickups.append(self)

def spawn_points(num_points=5, area_size=40):
    for _ in range(num_points):
        x = uniform(-area_size, area_size)
        z = uniform(-area_size, area_size)
        y = 0.5  # height above ground
        PointPickup(position=Vec3(x, y, z))

spawn_points(num_points=100, area_size=500)

# === DELAY FALL CHECK ===
def enable_fall_check():
    global fall_check_enabled
    # fall_check_enabled = True

# invoke(enable_fall_check, delay=1)  # Start checking for falling after 1 sec

# === CITY STRUCTURES ===
# def spawn_structures():
#     # Define structure type, position, color, and scale
#     structures = [
#         ('school', Vec3(-10, 0, 10), color.blue, Vec3(4, 2, 4)),
#         ('factory', Vec3(10, 0, 10), color.light_gray, Vec3(5, 3, 5)),
#         ('building', Vec3(10, 0, -10), color.gray, Vec3(3, 4, 3)),
#         ('hospital', Vec3(-10, 0, -10), color.red, Vec3(4, 3, 4)),
#         ('park', Vec3(0, 0, 15), color.lime, Vec3(6, 1, 6)),
#     ]
#     for name, pos, col, scl in structures:
#         Entity(
#             model='cube',
#             collider='box',
#             position=pos + Vec3(0, scl.y / 2, 0),
#             scale=scl,
#             color=col,
#             name=name
#         )

# spawn_structures()

apartment = Entity(
    model='assets/models/apartment.glb',
    collider='box',
    scale=0.05,
    position=(100, -0.9, 0)
)

def input(key):
    global is_first_person
    if key == 'c':
        is_first_person = not is_first_person
    if key == 'escape':
        mouse.locked = False
    if key == 'left mouse down':
        mouse.locked = True



# === UPDATE ===
def update():
    global pitch, yaw, velocity_y, is_grounded, player_points, game_over

    if game_over:
        return

    # === Mouse Look ===
    if mouse.locked and (abs(mouse.velocity[0]) > 1e-3 or abs(mouse.velocity[1]) > 1e-3):
        dx = mouse.velocity[0] * sensitivity
        dy = mouse.velocity[1] * sensitivity
        yaw += dx
        pitch -= dy
        pitch = clamp(pitch, -max_pitch, max_pitch)
        camera.rotation_x = pitch
        player.rotation_y = yaw
        camera.rotation_y = yaw

    if mouse.locked:
        yaw += mouse.velocity[0] * sensitivity
        pitch -= mouse.velocity[1] * sensitivity
        pitch = clamp(pitch, -max_pitch, max_pitch)

    # Reset roll and update camera position every frame
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
    # Calculate ground surface height
    surface_y = ground.position.y + ground.scale_y / 2

    # Handle jumping
    if is_grounded and held_keys['space']:
        velocity_y = jump_height
    else:
        velocity_y -= gravity * time.dt

    # Apply vertical movement
    player.y += velocity_y * time.dt

    # Simple ground collision
    if player.y < surface_y:
        player.y = surface_y
        velocity_y = 0
        is_grounded = True
    else:
        is_grounded = False

    # === PERSPECTIVE CHANGE LOGIC ===

    # === First-person view ===
    if is_first_person:
        player.visible = False
        if player.model != 'cube':
            player.model = 'cube'
            player.scale = Vec3(1, 10, 1)

        camera.position = player.position + Vec3(0, eye_height, 0)
        camera.rotation_x = pitch
        camera.rotation_y = yaw
        camera.rotation_z = 0

    # === Third-person view ===
    else:
        player.visible = True
        if player.model != 'assets/models/player.glb':
            player.model = 'assets/models/char.obj'
            player.scale = 0.005

        # Camera offset (behind and above player)
        behind = Vec3(sin(radians(yaw)), 0, cos(radians(yaw))) * -6
        height = Vec3(0, 3, 0)
        camera.position = player.position + behind + height
        # Third-person camera placement and rotation
        player.visible = True

        if player.model != 'assets/models/player.glb':
            player.model = 'assets/models/char.obj'
            player.scale = 0.005
        
        # Position camera behind and above the player
        behind = Vec3(sin(radians(yaw)), 0, cos(radians(yaw))) * -6
        height = Vec3(0, 2, 0)
        camera.position = player.position + behind + height

        # Set camera rotation using pitch and yaw (manual view control)
        camera.rotation_x = pitch
        camera.rotation_y = yaw
        camera.rotation_z = 0


    # === MODEL CHANGE LOGIC ===
    if is_first_person:
        camera.position = player.position + Vec3(0, eye_height, 0)
        camera.rotation_x = pitch
        camera.rotation_y = yaw
        player.visible = False
        if player.model != 'cube':
            player.model = 'cube'
            player.scale = Vec3(1, 1.8, 1)  # Default cube size
    else:
        offset = Vec3(sin(radians(yaw)), 0.5, cos(radians(yaw))) * -6
        camera.position = player.position + offset + Vec3(0, 2, 0)
        camera.look_at(player.position + Vec3(0, 1, 0))
        player.visible = True
        if player.model != 'assets/models/player.glb':
            player.model = 'assets/models/char.obj'
            player.scale = 0.005  # <-- Set this to scale the model down properly


    # === Point Pickup Collection ===
    for pickup in point_pickups[:]:
        if distance(player.position, pickup.position) < 1:
            player_points += pickup.value
            points_text.text = f'Points: {player_points}'
            pickup.disable()
            point_pickups.remove(pickup)

    # print("Terrain enabled:", ground.enabled, "visible:", ground.visible)

# REMOVED GAME OVER LOGIC

    # # === Game Over on Fall ===
    # if fall_check_enabled and player.y < -20:
    #     trigger_game_over()

# PRINT LOGS FOR POS CHANGE
# print("Player Y:", player.y, "Camera Y:", camera.y)

app.run()
