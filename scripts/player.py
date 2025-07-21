from ursina import *

heart_icons = []

death_text = Text("You Died!", origin=(0,0), scale=2, color=color.red, enabled=False)

class Player(Entity):
    def __init__(self, **kwargs):
        super().__init__()
        self.alive = True
        self.dead = False
        self.model = 'cube'
        self.color = color.azure
        self.collider = 'box'
        self.speed = 5
        self.scale_y = 2
        self.health = 100
        self.invincible = False
        self.invincibility_timer = 0
        self.knockback_force = Vec3(0, 0, 0)
        self.on_death_callback = None

        # Camera follow setup
        self.camera_target = Entity(parent=self, position=(0, 10, -20))
        camera.parent = scene
        camera.position = self.camera_target.world_position
        camera.look_at(self)

        for key, value in kwargs.items():
            setattr(self, key, value)

    def update(self):
        if not self.alive:
            return

        self.camera_target.world_position = self.world_position + Vec3(0, 10, -20)
        camera.position = lerp(camera.position, self.camera_target.world_position, time.dt * 5)
        camera.look_at(self)

        move = held_keys['w'] - held_keys['s']
        strafe = held_keys['d'] - held_keys['a']
        self.position += (self.forward * move + self.right * strafe) * time.dt * self.speed

        self.x = clamp(self.x, -25, 25)
        self.z = clamp(self.z, -25, 25)
        self.position += self.knockback_force * time.dt
        self.knockback_force *= 0.9

        if self.invincible and time.time() - self.invincibility_timer > 3:
            self.invincible = False
            print("Player is vulnerable again.")

    def setup_hearts(self):
        for i in range(7):
            heart = Entity(
                parent=camera.ui,
                model='quad',
                texture='assets/ui/heart_full.png',
                scale=0.07,
                position=Vec2(-0.75 + i * 0.1, 0.45)
            )
            heart_icons.append(heart)

    def update_hearts(self):
        full_hearts = round(self.health / 100 * 7)
        for i, heart in enumerate(heart_icons):
            heart.texture = (
                'assets/ui/heart_full.png' if i < full_hearts else 'assets/ui/heart_empty.png'
            )

    def take_damage(self, amount, source_position=None):
        if self.invincible:
            return

        self.health -= amount
        print(f"Player took {amount} damage! Health: {self.health}")

        if source_position:
            direction = (self.position - source_position).normalized()
            self.knockback_force += direction * 5

        self.invincible = True
        self.invincibility_timer = time.time()

        self.update_hearts()  # Update heart UI

        if self.health <= 0:
            self.health = 0
            self.die()
            if hasattr(self, 'on_death_callback'):
                self.on_death_callback()

    def die(self):
        self.alive = False
        self.visible = True
        self.collider = None
        self.dead = True
        self.rotation_x = 90
        for heart in heart_icons:
            heart.enabled = False
        if hasattr(self, 'on_death_callback'):
            self.on_death_callback()
        self.disable()

    def restart_game():
        application.quit()