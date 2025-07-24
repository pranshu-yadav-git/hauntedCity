from ursina import *
from math import sin, cos, radians
from random import uniform
from ursina import lerp
from panda3d.core import Fog
from ursina import Audio

ghost_sound = Audio('assets/sounds/ghost.wav', loop=True, autoplay=True)

app = Ursina()

road = Entity(
    model='plane',
    texture='assets/textures/asphalt.jpg',
    scale=(10, 1, 50),
    position=(0, 0.76, 5),
    color=color.white,
    collider='box'
)

for i in range(-25, 26, 5):
    Entity(
        model='cube',
        scale=(0.2, 0.01, 1.5),
        color=color.white,
        position=(0, 0.01, i)
    )

# === CONFIG ===
target_eye_height = 1.8
target_scale_y = 1.8
normal_speed = 5
camera.fov = 90  
sprint_speed = 10
sensitivity = 100
jump_height = 6
gravity = 20
max_pitch = 89
pitch = -30
yaw = 0
eye_height = 1.8
player_points = 0
velocity_y = 0
is_grounded = False
game_over = False
fall_check_enabled = False
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
pickup_distance = 4.0

bobbing_time = 0.1
base_eye_height = 1.8

# Add fog effect
fog = Fog("SceneFog")
fog.setMode(Fog.MExponential)
fog.setColor(0.3, 0.3, 0.3)
fog.setExpDensity(0.05)
scene.setFog(fog)

crosshair = Entity(parent=camera.ui, model='circle', scale=(0.0125, 0.0125), color=color.white, position=(0, 0))


hand_right = Entity(
    parent=camera,
    model='cube',
    color=color.rgb(255, 224, 189),

    scale=(0.15, 0.25, 0.15),
    position=(0.25, -0.4, 0.5),
    rotation=(20, -15, 10),
    enabled=True
)

hand_left = Entity(
    parent=camera,
    model='cube',
    color=color.rgb(255, 224, 189),

    scale=(0.15, 0.25, 0.15),
    position=(-0.25, -0.4, 0.5),
    rotation=(20, 15, -10),
    enabled=True
)

Sky()

ground = Entity(
    model='plane',
    texture='assets/textures/grass2.png',
    scale=(100, 1, 100),
    position=(0, 0, 0),
    color=color.white,
    collider='box'
)

DirectionalLight(y=3, z=3, shadows=True)

player = Entity(model='cube', scale_y=1.8, origin_y=-0.5, collider='box', position=(0, 10, 0))
player.collider = BoxCollider(player, center=Vec3(0, 1, 0), size=Vec3(1, 2, 1))
player.visible = False

points_text = Text(
    text=f'Points: {player_points}',
    position=(0.75, 0.45),
    origin=(0, 0),
    scale=1.5,
    color=color.red
)

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
        y = 0.5
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

    if key == 'e':
        ray = raycast(camera.world_position, camera.forward, distance=pickup_distance, ignore=(player,))
        if ray.hit and hasattr(ray.entity, 'is_holdable') and ray.entity.is_holdable:
            item = ray.entity
            if not held_right:
                held_right = item
                item.parent = camera
                item.position = Vec3(0.675, -0.2, 1)  # local to camera
                item.scale = 0.3


                item.rotation = Vec3(0, 0, 0)  # Reset rotation
                item.is_thrown = False

    
    # Offhand grabbing
    if key == 'f':
        ray = raycast(camera.world_position, camera.forward, distance=pickup_distance, ignore=(player,))
        if ray.hit and hasattr(ray.entity, 'is_holdable') and ray.entity.is_holdable:
            item = ray.entity
            if not held_left:
                held_left = item
                item.parent = camera
                item.position = Vec3(-0.675, -0.2, 1)
                item.scale = 0.3

                item.rotation = Vec3(0, 0, 0)
                item.is_thrown = False


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
            thrown.velocity = camera.forward * 10 + Vec3(0, 4, 0)
            thrown.angular_velocity = Vec3(uniform(-180, 180), uniform(-180, 180), uniform(-180, 180))
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

holdable_items.append(HoldableItem(position=(2, 0.75, 2), color=color.orange))
holdable_items.append(HoldableItem(position=(-2, 0.75, -2), color=color.yellow))
holdable_items.append(HoldableItem(position=(0, 0.75, 4), color=color.cyan))

...

# === Input Handling ===
def input(key):
    global held_left, held_right

    if key == 'e':
        ray = raycast(camera.world_position, camera.forward, distance=pickup_distance, ignore=(player,))
        if ray.hit and hasattr(ray.entity, 'is_holdable') and ray.entity.is_holdable:
            item = ray.entity
            if not held_right:
                held_right = item
                item.parent = camera
                item.world_position = player.world_position + Vec3(0.3, -0.2, 1)
                item.scale = 0.3

    if key == 'f':
        ray = raycast(camera.world_position, camera.forward, distance=pickup_distance, ignore=(player,))
        if ray.hit and hasattr(ray.entity, 'is_holdable') and ray.entity.is_holdable:
            item = ray.entity
            if not held_left:
                held_left = item
                item.parent = camera
                item.world_position = player.world_position + Vec3(-0.3, -0.2, 1)
                item.scale = 0.3

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
            thrown.velocity = camera.forward * 10 + Vec3(0, 4, 0)
            thrown.angular_velocity = Vec3(uniform(-180, 180), uniform(-180, 180), uniform(-180, 180))
            thrown.is_thrown = True

# === Main Game Loop ===
def update():
    global pitch, yaw, velocity_y, is_grounded, player_points, game_over, eye_height, target_eye_height, target_scale_y, bobbing_time, x_bob, y_bob, is_crouching

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

    # === Gravity and Jumping ===
    surface_y = ground.position.y + ground.scale_y / 2
    if is_grounded and held_keys['space']:
        velocity_y = jump_height
    else:
        velocity_y -= gravity * time.dt
    player.y += velocity_y * time.dt

    if player.y < surface_y:
        player.y = surface_y
        velocity_y = 0
        is_grounded = True
    else:
        is_grounded = False

    # === Third-Person Camera Position ===
    behind = Vec3(sin(radians(yaw)), 0, cos(radians(yaw))) * -6
    height = Vec3(0, 2, 0)
    camera.position = player.position + behind + height
    camera.rotation_x = pitch
    camera.rotation_y = yaw


    # === First vs Third Person ===
    if is_first_person:
        camera.position = player.position + Vec3(0, eye_height, 0)
        camera.rotation_x = pitch
        camera.rotation_y = yaw
        player.visible = False
        if player.model != 'cube':
            player.model = 'cube'
            player.scale = Vec3(1, 1.8, 1)
    else:
        offset = Vec3(sin(radians(yaw)), 0.5, cos(radians(yaw))) * -6
        camera.position = player.position + offset + Vec3(0, 2, 0)
        camera.look_at(player.position + Vec3(0, 1, 0))
        player.visible = True
        if player.model != 'assets/models/player.glb':
            player.model = 'assets/models/char.obj'
            player.scale = 0.005

    # === Point Pickup Logic ===

    for pickup in point_pickups[:]:
        if distance(player.position, pickup.position) < 1:
            player_points += pickup.value
            points_text.text = f'Points: {player_points}'
            pickup.disable()
            point_pickups.remove(pickup)

    # === Crouching ===
    if held_keys['left control']:
        target_scale_y = crouch_height
        target_eye_height = 0.9
    else:
        target_scale_y = stand_height
        target_eye_height = 1.8


    player.scale_y = lerp(player.scale_y, target_scale_y, 6 * time.dt)
    eye_height = lerp(eye_height, target_eye_height, 6 * time.dt)

    # === Held Item Bobbing ===
    if held_right:
        base_pos = camera.world_position + camera.forward + camera.right * 0.4 + Vec3(0, -0.2, 0)
        bob = Vec3(x_bob * 0.5, y_bob * 0.7, 0)
        held_right.world_position = lerp(held_right.world_position, base_pos + bob, 10 * time.dt)

    if held_left:
        base_pos = camera.world_position + camera.forward - camera.right * 0.4 + Vec3(0, -0.2, 0)
        bob = Vec3(x_bob * 0.5, y_bob * 0.7, 0)
        held_left.world_position = lerp(held_left.world_position, base_pos + bob, 10 * time.dt)

    # === Highlight Holdables ===
    hovered_holdable = None
    ray = raycast(camera.world_position, camera.forward, distance=pickup_distance, ignore=(player,))
    if ray.hit and hasattr(ray.entity, 'is_holdable') and ray.entity.is_holdable:
        hovered_holdable = ray.entity

    for e in scene.entities:
        if hasattr(e, 'is_holdable'):
            e.highlight_color = color.lime if e == hovered_holdable else color.clear

    # === Camera and Hand Bobbing ===
    is_moving = held_keys['w'] or held_keys['a'] or held_keys['s'] or held_keys['d']

    if is_moving and is_grounded:
        bobbing_time += time.dt * 6
        y_bob = sin(bobbing_time) * 0.035
        x_bob = sin(bobbing_time * 2) * 0.02
    else:
        bobbing_time = 0
        y_bob = 0
        x_bob = 0

    camera.position = player.position + Vec3(x_bob, eye_height + y_bob, 0)

    bob_speed = 6
    x_bob = sin(time.time() * bob_speed) * 0.01
    y_bob = cos(time.time() * bob_speed * 2) * 0.01
    hand_right.position = Vec3(0.25 + x_bob, -0.4 + y_bob, 0.5)
    hand_left.position = Vec3(-0.25 - x_bob, -0.4 + y_bob, 0.5)

    # === Thrown Items Physics ===
    for item in holdable_items:
        if hasattr(item, 'is_thrown') and item.is_thrown:
            if not hasattr(item, 'velocity'):
                item.velocity = Vec3(0, 0, 0)
            if not hasattr(item, 'angular_velocity'):
                item.angular_velocity = Vec3(0, 0, 0)

            item.velocity.y -= gravity * time.dt
            item.position += item.velocity * time.dt
            item.rotation_x += item.angular_velocity.x * time.dt
            item.rotation_y += item.angular_velocity.y * time.dt
            item.rotation_z += item.angular_velocity.z * time.dt

            ground_y = ground.y + 0.75
            if item.y <= ground_y:
                item.y = ground_y
                item.velocity = Vec3(0, 0, 0)
                item.angular_velocity *= 0.8
                if item.angular_velocity.length() < 1:
                    if not hasattr(item, 'upright_timer'):
                        item.upright_timer = 0
                    item.upright_timer += time.dt
                    target_rot = Vec3(0, item.rotation.y, 0)
                    item.rotation = lerp(item.rotation, target_rot, 6 * time.dt)
                    if item.upright_timer > 0.5:
                        item.rotation = target_rot
                        item.angular_velocity = Vec3(0, 0, 0)
                        item.is_thrown = False
                        del item.upright_timer

# === Run App ===
app.run()
