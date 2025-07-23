from ursina import *
from math import sin, cos, radians
from random import uniform
from ursina import lerp
from panda3d.core import Fog

app = Ursina()

# === CONFIG ===
target_eye_height = 1.8
target_scale_y = 1.8
normal_speed = 5
camera.fov = 90  # Try values between 60 - 120
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


crouch_height = 0.9
stand_height = 1.8
is_crouching = False

held_left = None
held_right = None
pickup_distance = 4.0  # max distance to grab object

bobbing_time = 0
base_eye_height = 1.8

# Add fog effect
fog = Fog("SceneFog")  # This name string is required
fog.setMode(Fog.MExponential)  # You can also use Fog.MLinear
fog.setColor(0.3, 0.3, 0.3)  # spooky gray
fog.setExpDensity(0.05)
scene.setFog(fog)

crosshair = Entity(
    model='circle',
    scale=0.005,
    color=color.white,
    position=(0, 0, 0),
    parent=camera.ui
)

crosshair = Entity(parent=camera.ui, model='quad', scale=(0.002, 0.0002), color=color.white, position=(0, 0))
crosshair2 = Entity(parent=camera.ui, model='quad', scale=(0.0002, 0.002), color=color.white, position=(0, 0))
crosshair = Entity(parent=camera.ui, model='quad', texture='/assets/textures/crosshairg.png', scale=0.003)

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
player.collider = BoxCollider(player, center=Vec3(0,1,0), size=Vec3(1,2,1))
player.visible = False
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

apartment = Entity(
    model='assets/models/apartment.glb',
    collider='box',
    scale=0.05,
    position=(100, -0.9, 0)
)

def input(key):
    global held_left, held_right

    # Pick up object
    if key == 'e':
        ray = raycast(camera.world_position, camera.forward, distance=pickup_distance, ignore=(player,))

        if ray.hit and hasattr(ray.entity, 'is_holdable') and ray.entity.is_holdable:
            item = ray.entity
            if not held_right:
                held_right = item
                item.parent = camera
                item.world_position = player.world_position + Vec3(0.3, 0, 1)
                item.scale = 0.3
            elif not held_left:
                held_left = item
                item.parent = camera
                item.world_position = player.world_position + Vec3(-0.3, 0, 1)
                item.scale = 0.3

    # Drop / Throw object
    if key == 'q':
        thrown = None

        if held_right:
            thrown = held_right
            held_right = None
        elif held_left:
            thrown = held_left
            held_left = None

        if thrown:
            thrown.parent = scene
            thrown.collider = 'box'
            thrown.world_position = camera.world_position + camera.forward + Vec3(0, -0.2, 0)
            thrown.scale = 0.5
            thrown.velocity = camera.forward * 10 + Vec3(0, 3, 0)  # Add upward arc

            # Add the item to a global list to update its motion manually
            thrown.is_thrown = True

class HoldableItem(Entity):
    def __init__(self, position=(0, 1, 0), model='cube', color=color.azure):
        super().__init__(
            model=model,
            color=color,
            scale=0.5,
            position=position,
            collider='box'
        )
        self.is_holdable = True

holdable_items = []

holdable_items.append(HoldableItem(position=(2, 1, 2), color=color.orange))
holdable_items.append(HoldableItem(position=(-2, 1, -2), color=color.yellow))
holdable_items.append(HoldableItem(position=(0, 1, 4), color=color.cyan))

# === UPDATE ===
def update():
    global pitch, yaw, velocity_y, is_grounded, player_points, game_over, eye_height, target_eye_height, target_scale_y, bobbing_time, x_bob, y_bob

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

    global is_crouching

    # Smooth crouch control
    if held_keys['left control']:
        target_scale_y = crouch_height
        target_eye_height = 0.9
    else: 
        target_scale_y = stand_height
        target_eye_height = 1.8

    
    # Interpolate current values towards target values (smoothing)
    player.scale_y = lerp(player.scale_y, target_scale_y, 6 * time.dt)
    eye_height = lerp(eye_height, target_eye_height, 6 * time.dt)

    if held_right:
        base_pos = camera.world_position + camera.forward + camera.right * 0.4 + Vec3(0, -0.2, 0)
        bob = Vec3(x_bob * 0.5, y_bob * 0.7, 0)  # match camera bob gently
        held_right.world_position = lerp(held_right.world_position, base_pos + bob, 10 * time.dt)

    if held_left:
        base_pos = camera.world_position + camera.forward - camera.right * 0.4 + Vec3(0, -0.2, 0)
        bob = Vec3(x_bob * 0.5, y_bob * 0.7, 0)
        held_left.world_position = lerp(held_left.world_position, base_pos + bob, 10 * time.dt)


    # Highlight holdable under crosshair
    hovered_holdable = None
    ray = raycast(camera.world_position, camera.forward, distance=pickup_distance, ignore=(player,))

    if ray.hit and hasattr(ray.entity, 'is_holdable') and ray.entity.is_holdable:
        hovered_holdable = ray.entity

    # Add/remove outline effect
    for e in scene.entities:
        if hasattr(e, 'is_holdable'):
            e.highlight_color = color.lime if e == hovered_holdable else color.clear

    is_moving = held_keys['w'] or held_keys['a'] or held_keys['s'] or held_keys['d']

    if is_moving and is_grounded:
        bobbing_time += time.dt * 6  # slower for smoothness
        y_bob = math.sin(bobbing_time) * 0.035
        x_bob = math.sin(bobbing_time * 2) * 0.02
    else:
        bobbing_time = 0
        y_bob = 0
        x_bob = 0

    # Final camera position
    camera.position = player.position + Vec3(x_bob, eye_height + y_bob, 0)

    # === Update thrown item physics ===
    for item in holdable_items:
        if hasattr(item, 'is_thrown') and item.is_thrown:
            if not hasattr(item, 'velocity'):
                item.velocity = Vec3(0, 0, 0)
            item.velocity.y -= gravity * time.dt  # gravity
            item.position += item.velocity * time.dt

            # Check for ground collision
            if item.y <= ground.y + 0.75:  # adjust as needed
                item.y = ground.y + 0.75
                item.velocity = Vec3(0, 0, 0)
                item.is_thrown = False

app.run()
