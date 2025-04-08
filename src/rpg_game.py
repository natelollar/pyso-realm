"""PysoRealm - Isometric Game Prototype

This module runs an isometric tile-based game world using pyray.
It handles rendering, player input (keyboard and gamepad), and asset loading/cleanup.
The window is also resizable.

Constants:
    TILE_WIDTH (int): Width of a single isometric tile in pixels.
    TILE_HEIGHT (int): Height of a single isometric tile in pixels. (floor surface)
    TILE_FULL_HEIGHT (int): Full pixel height of texture.

Direction Index:
    0: North (Top-Right)
    1: North-East
    2: East (Bottom-Right)
    3: South-East
    4: South (Bottom-Left)
    5: South-West
    6: West (Top-Left)
    7: North-West
"""

import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path

import pyray as pr

from src.rpg_logger import get_logger

TILE_WIDTH = 256
TILE_HEIGHT = 128
TILE_FULL_HEIGHT = 512


class PysoRealm:
    """Main class for running the Pyso Realm isometric game prototype.

    Handles game window setup, resource loading, rendering, camera logic,
    and core game loop control. Supports context manager usage for automatic
    initialization and cleanup.
    """

    def __init__(self) -> None:
        """Initialize base configuration, constants, and placeholders."""
        self.TILE_SIZE = pr.Vector2(TILE_WIDTH, TILE_HEIGHT)

        self.WORLD_WIDTH = 12
        self.WORLD_HEIGHT = 12
        self.base_dir = self._determine_base_dir()
        self.logger = get_logger()
        self.textures = {}

        self.GAME_WIDTH = 1920
        self.GAME_HEIGHT = 1080

    def __enter__(self) -> "PysoRealm":
        """Initialize the game window and rendering context.

        Configures trace logging, sets window flags (ex. anti-aliasing, VSync, high DPI),
        and initializes the game window with the specified resolution.

        Returns:
            PysoRealm: This instance of the PysoRealm class. (self)

        """
        self.logger.info("# ---------- Start... ---------- #")
        pr.set_trace_log_level(pr.TraceLogLevel.LOG_WARNING)
        pr.set_config_flags(
            pr.ConfigFlags.FLAG_MSAA_4X_HINT
            | pr.ConfigFlags.FLAG_VSYNC_HINT
            | pr.ConfigFlags.FLAG_WINDOW_RESIZABLE
            | pr.ConfigFlags.FLAG_WINDOW_HIGHDPI,
        )
        pr.init_window(self.GAME_WIDTH, self.GAME_HEIGHT, "Pyso Realm")

        self.scene_textures = self.load_directory_of_textures("res/image/scene/*.png")
        self.character_textures = self.load_directory_of_textures("res/image/characters/*.png")

        self.cam = pr.Camera2D()
        self.cam.offset = pr.Vector2(0, 0)
        self.cam.target = pr.Vector2(0, 0)
        self.cam.rotation = 0.0
        self.cam.zoom = 1.0
        cam_trg = 0.5
        self.cam.target = pr.Vector2(TILE_WIDTH * cam_trg, TILE_HEIGHT * cam_trg)

        self.floor = [
            self.scene_textures["stone_N.png"],
            self.scene_textures["stone_E.png"],
            self.scene_textures["stone_S.png"],
            self.scene_textures["stone_W.png"],
            self.scene_textures["stoneUneven_N.png"],
            self.scene_textures["stoneUneven_E.png"],
            self.scene_textures["stoneUneven_S.png"],
            self.scene_textures["stoneUneven_W.png"],
        ]

        self.ground_covering = [
            self.scene_textures["planksBroken_N.png"],
            self.scene_textures["planksBroken_E.png"],
            self.scene_textures["planksBroken_S.png"],
            self.scene_textures["planksBroken_W.png"],
        ]

        self.HIT_BOX_SMALL = pr.Rectangle(4 - 0.125, -3 - 0.125, 0.25, 0.25)
        self.HIT_BOX_MEDIUM = pr.Rectangle(4 - 0.25, -3 - 0.25, 0.5, 0.5)
        self.HIT_BOX_CHEST_EW = pr.Rectangle(4 - 0.125, -3 - 0.15, 0.25, 0.3)
        self.HIT_BOX_CHEST_NS = pr.Rectangle(4 - 0.15, -3 - 0.1, 0.3, 0.25)
        self.HIT_BOX_SPIRAL_N = pr.Rectangle(4 - 0.375, -3 - 0.125, 0.5, 0.5)
        self.HIT_BOX_SPIRAL_E = pr.Rectangle(4 - 0.125, -3 - 0.125, 0.5, 0.5)
        self.HIT_BOX_SPIRAL_S = pr.Rectangle(4 - 0.375, -3 - 0.375, 0.5, 0.5)
        self.HIT_BOX_SPIRAL_W = pr.Rectangle(4 - 0.5, -3, 0.625, 0.5)

        @dataclass
        class Object:
            texture: pr.Texture2D
            hit_box: pr.Rectangle

        self.objects = [
            Object(self.scene_textures["barrel_N.png"], self.HIT_BOX_SMALL),
            Object(self.scene_textures["barrel_E.png"], self.HIT_BOX_SMALL),
            Object(self.scene_textures["barrel_S.png"], self.HIT_BOX_SMALL),
            Object(self.scene_textures["barrel_W.png"], self.HIT_BOX_SMALL),
            Object(self.scene_textures["barrels_N.png"], self.HIT_BOX_MEDIUM),
            Object(self.scene_textures["barrels_E.png"], self.HIT_BOX_MEDIUM),
            Object(self.scene_textures["barrels_S.png"], self.HIT_BOX_MEDIUM),
            Object(self.scene_textures["barrels_W.png"], self.HIT_BOX_MEDIUM),
            Object(self.scene_textures["woodenCrate_N.png"], self.HIT_BOX_SMALL),
            Object(self.scene_textures["woodenCrate_E.png"], self.HIT_BOX_SMALL),
            Object(self.scene_textures["woodenCrate_S.png"], self.HIT_BOX_SMALL),
            Object(self.scene_textures["woodenCrate_W.png"], self.HIT_BOX_SMALL),
            Object(self.scene_textures["woodenCrates_N.png"], self.HIT_BOX_MEDIUM),
            Object(self.scene_textures["woodenCrates_E.png"], self.HIT_BOX_MEDIUM),
            Object(self.scene_textures["woodenCrates_S.png"], self.HIT_BOX_MEDIUM),
            Object(self.scene_textures["woodenCrates_W.png"], self.HIT_BOX_MEDIUM),
            Object(self.scene_textures["chestClosed_E.png"], self.HIT_BOX_CHEST_EW),
            Object(self.scene_textures["chestClosed_S.png"], self.HIT_BOX_CHEST_NS),
            Object(self.scene_textures["chestClosed_W.png"], self.HIT_BOX_CHEST_EW),
            Object(self.scene_textures["chestClosed_N.png"], self.HIT_BOX_CHEST_NS),
            Object(self.scene_textures["chestOpen_E.png"], self.HIT_BOX_CHEST_EW),
            Object(self.scene_textures["chestOpen_S.png"], self.HIT_BOX_CHEST_NS),
            Object(self.scene_textures["chestOpen_W.png"], self.HIT_BOX_CHEST_EW),
            Object(self.scene_textures["chestOpen_N.png"], self.HIT_BOX_CHEST_NS),
            Object(self.scene_textures["stoneColumn_E.png"], self.HIT_BOX_SMALL),
            Object(self.scene_textures["stoneColumn_S.png"], self.HIT_BOX_SMALL),
            Object(self.scene_textures["stoneColumn_W.png"], self.HIT_BOX_SMALL),
            Object(self.scene_textures["stoneColumn_N.png"], self.HIT_BOX_SMALL),
            Object(self.scene_textures["stoneColumnWood_E.png"], self.HIT_BOX_SMALL),
            Object(self.scene_textures["stoneColumnWood_S.png"], self.HIT_BOX_SMALL),
            Object(self.scene_textures["stoneColumnWood_W.png"], self.HIT_BOX_SMALL),
            Object(self.scene_textures["stoneColumnWood_N.png"], self.HIT_BOX_SMALL),
            Object(self.scene_textures["stairsSpiral_E.png"], self.HIT_BOX_SPIRAL_E),
            Object(self.scene_textures["stairsSpiral_S.png"], self.HIT_BOX_SPIRAL_S),
            Object(self.scene_textures["stairsSpiral_W.png"], self.HIT_BOX_SPIRAL_W),
            Object(self.scene_textures["stairsSpiral_N.png"], self.HIT_BOX_SPIRAL_N),
        ]

        self.walls = [
            self.scene_textures["stoneWall_E.png"],
            self.scene_textures["stoneWallColumnIn_E.png"],
            self.scene_textures["stoneWall_S.png"],
            self.scene_textures["stoneWallColumnIn_S.png"],
            self.scene_textures["stoneWall_W.png"],
            self.scene_textures["stoneWallColumnIn_W.png"],
            self.scene_textures["stoneWall_N.png"],
            self.scene_textures["stoneWallColumnIn_N.png"],
            self.scene_textures["stoneWallCorner_E.png"],
            self.scene_textures["stoneWallCorner_S.png"],
            self.scene_textures["stoneWallCorner_W.png"],
            self.scene_textures["stoneWallCorner_N.png"],
            self.scene_textures["stoneWallGateClosed_E.png"],
            self.scene_textures["stoneWallGateClosed_S.png"],
            self.scene_textures["stoneWallGateClosed_W.png"],
            self.scene_textures["stoneWallGateClosed_N.png"],
        ]

        self.render_target = pr.load_render_texture(pr.get_screen_width(), pr.get_screen_height())
        # set texture filter for smoother scaling when resizing the window
        pr.set_texture_filter(self.render_target.texture, pr.TextureFilter.TEXTURE_FILTER_BILINEAR)

        self.shader = pr.load_shader(
            f"{self.base_dir}/res/shader/tiles.vs",
            f"{self.base_dir}/res/shader/tiles.fs",
        )

        self.char_pos = pr.Vector2(self.WORLD_WIDTH / 2 - 1, self.WORLD_HEIGHT / 2 - 1)
        # character direction
        self.char_dir = 0
        # character animation accumulator
        self.char_anim_accumulator = 0.0

        # collision boxes
        self.coll_boxes: list[pr.Rectangle] = []

        self.global_rand = random.Random(100)

        self.was_moving = False

        pr.set_target_fps(144)

        # important. return self for context manager (__enter__, __exit__)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> bool | None:
        """Handle cleanup and exception logging when exiting the context.

        If an exception occurs within the context, it is logged. Then the method
        performs cleanup by unloading shaders, textures, and closing the window.

        Args:
            exc_type: The exception type.
            exc_val: The exception value.
            exc_tb: The traceback object.

        """
        # log any exception from the context
        if exc_type is not None:
            self.logger.error(f"Exception occurred in context: {exc_type.__name__}: {exc_val}")
            self.logger.debug("Traceback:", exc_info=(exc_type, exc_val, exc_tb))

        # cleanup
        try:
            pr.unload_shader(self.shader)
            pr.unload_render_texture(self.render_target)
            self.unload_directory_of_textures(self.scene_textures)
            self.unload_directory_of_textures(self.character_textures)
            pr.close_window()
        except Exception as e:
            self.logger.error(f"{e}")

        self.logger.info("# ---------- Exit... ---------- #")

    def run_game_loop(self) -> None:
        """Continuously runs the main game loop until the window is closed.
            In each frame, this loop:

        - Initializes a new random number generator (`self.frame_rand`) with a fixed seed.
        - Calculates the time elapsed since the previous frame (`self.dt`).
        - Resets the character's movement delta (`self.char_dp`) to zero.
        - Reads keyboard and gamepad inputs to determine the character's intended movement.
        - Resolves the characters direction, updates the characters animation state,
            and checks for collisions.
        - Updates the camera's position and renders the scene
            (ground, walls, objects, and the character).
        - Scales the final rendered texture to match the current window size and displays it.

        The loop ends when `pr.window_should_close()` returns True.
        """
        while not pr.window_should_close():
            self.frame_rand = random.Random(476)

            # delta time
            self.dt = pr.get_frame_time()

            # character delta position
            self.char_dp = pr.Vector2(0, 0)

            # keyboard
            if pr.is_key_down(pr.KeyboardKey.KEY_W):
                self.char_dp.x -= 1
                self.char_dp.y += 1
            if pr.is_key_down(pr.KeyboardKey.KEY_S):
                self.char_dp.x += 1
                self.char_dp.y -= 1
            if pr.is_key_down(pr.KeyboardKey.KEY_A):
                self.char_dp.x -= 1
                self.char_dp.y -= 1
            if pr.is_key_down(pr.KeyboardKey.KEY_D):
                self.char_dp.x += 1
                self.char_dp.y += 1

            # gamepad
            self.gamepad_angle = 0.0
            self.gamepad_magnitude = 0.0
            if pr.is_gamepad_available(0):
                right_x = pr.get_gamepad_axis_movement(0, pr.GamepadAxis.GAMEPAD_AXIS_LEFT_X)
                right_y = pr.get_gamepad_axis_movement(0, pr.GamepadAxis.GAMEPAD_AXIS_LEFT_Y)
                deadzone = 0.4

                magnitude = math.sqrt((right_x * right_x) + (right_y * right_y))
                self.gamepad_magnitude = magnitude  # debugging variable
                if magnitude > deadzone:
                    angle = math.degrees(math.atan2(right_x, -right_y)) % 360
                    self.gamepad_angle = angle  # debugging variable

                    # even 45 degree zones
                    if angle >= 337.5 or angle < 22.5:  # up. 0
                        self.char_dp.x -= 1
                        self.char_dp.y += 1
                    elif 22.5 <= angle < 67.5:  # up right. 45
                        self.char_dp.x += 0
                        self.char_dp.y += 2
                    elif 67.5 <= angle < 112.5:  # right. 90
                        self.char_dp.x += 1
                        self.char_dp.y += 1
                    elif 112.5 <= angle < 157.5:  # down right. 135
                        self.char_dp.x += 2
                        self.char_dp.y += 0
                    elif 157.5 <= angle < 202.5:  # down. 180
                        self.char_dp.x += 1
                        self.char_dp.y -= 1
                    elif 202.5 <= angle < 247.5:  # downl left. 225
                        self.char_dp.x += 0
                        self.char_dp.y -= 2
                    elif 247.5 <= angle < 292.5:  # left. 270
                        self.char_dp.x -= 1
                        self.char_dp.y -= 1
                    elif 292.5 <= angle < 337.5:  # up left. 315
                        self.char_dp.x -= 2
                        self.char_dp.y += 0

            self.is_moving = False

            match (int(self.char_dp.x), int(self.char_dp.y)):
                case (0, 2):
                    self.char_dir, self.is_moving = 0, True
                case (1, 1):
                    self.char_dir, self.is_moving = 1, True
                case (2, 0):
                    self.char_dir, self.is_moving = 2, True
                case (1, -1):
                    self.char_dir, self.is_moving = 3, True
                case (0, -2):
                    self.char_dir, self.is_moving = 4, True
                case (-1, -1):
                    self.char_dir, self.is_moving = 5, True
                case (-2, 0):
                    self.char_dir, self.is_moving = 6, True
                case (-1, 1):
                    self.char_dir, self.is_moving = 7, True

            if self.char_dp.x != 0 or self.char_dp.y != 0:
                norm = pr.vector2_normalize(self.char_dp)
            else:
                norm = pr.Vector2(0, 0)

            # character position
            char_speed = 3.0
            self.char_pos.x += norm.x * char_speed * self.dt
            self.char_pos.y += norm.y * char_speed * self.dt

            # clamp character movement to world size
            self.char_pos.x = max(0, min(self.char_pos.x, self.WORLD_WIDTH - 1))
            self.char_pos.y = max(0, min(self.char_pos.y, self.WORLD_HEIGHT - 1))

            self.was_collision = False

            character_hit_box = pr.Rectangle(
                self.HIT_BOX_SMALL.x + self.char_pos.x,
                self.HIT_BOX_SMALL.y + self.char_pos.y,
                self.HIT_BOX_SMALL.width,
                self.HIT_BOX_SMALL.height,
            )

            for box in self.coll_boxes:
                if pr.check_collision_recs(character_hit_box, box):
                    self.is_moving = False
                    self.was_collision = True  # debugging

                    diff = pr.get_collision_rec(character_hit_box, box)
                    if diff.width > diff.height:
                        if diff.y > box.y:
                            self.char_pos.y += diff.height
                        else:
                            self.char_pos.y -= diff.height
                    elif diff.x > box.x:
                        self.char_pos.x += diff.width
                    else:
                        self.char_pos.x -= diff.width

            self.coll_boxes.clear()

            cpx, cpy = self.tile_to_screen_space(self.char_pos.x, self.char_pos.y)
            self.cam.target = pr.Vector2(cpx, cpy)
            self.cam.zoom = 1
            w = float(self.render_target.texture.width) * 0.5
            h = float(self.render_target.texture.height) * 0.5
            self.cam.offset = pr.Vector2(w, h)
            offset_x = self.TILE_SIZE.x * 0.5 * self.cam.zoom
            offset_y = self.TILE_SIZE.y * 0.5 * self.cam.zoom
            self.cam.offset = pr.Vector2(self.cam.offset.x - offset_x, self.cam.offset.y - offset_y)
            self.cam.offset.y -= (TILE_FULL_HEIGHT + TILE_HEIGHT) * 0.5 * self.cam.zoom

            pr.begin_texture_mode(self.render_target)
            pr.clear_background(pr.Color(30, 30, 30, 255))  # darker background
            pr.begin_mode_2d(self.cam)
            pr.begin_shader_mode(self.shader)
            pr.rl_draw_render_batch_active()
            pr.rl_disable_depth_test()

            # ground floor
            for i in range(int(self.WORLD_WIDTH * self.WORLD_HEIGHT)):
                u = i // self.WORLD_WIDTH
                v = self.WORLD_HEIGHT - 1 - (i % self.WORLD_HEIGHT)
                pr.draw_texture(
                    self.frame_rand.choice(self.floor),
                    *self.tile_to_screen_space_i32(u, v),
                    pr.WHITE,
                )
            # ground covering
            for i in range(int(self.WORLD_WIDTH * self.WORLD_HEIGHT)):
                u = i // self.WORLD_WIDTH
                v = self.WORLD_HEIGHT - 1 - (i % self.WORLD_HEIGHT)
                if self.frame_rand.randint(0, 15) != 0:
                    continue
                pr.draw_texture(
                    self.frame_rand.choice(self.ground_covering),
                    *self.tile_to_screen_space_i32(u, v),
                    pr.WHITE,
                )

            # north corner wall
            pr.draw_texture(
                self.walls[9],
                *self.tile_to_screen_space_i32(0, self.WORLD_HEIGHT - 1),
                pr.WHITE,
            )
            # north west wall
            for i in range(self.WORLD_HEIGHT - 2):
                wall_idx = 1 - (i & 1)  # alternating index
                if (i & 5) == 1:  # specific bit pattern check
                    wall_idx = 12
                pr.draw_texture(
                    self.walls[wall_idx],
                    *self.tile_to_screen_space_i32(0, float(self.WORLD_HEIGHT - 2 - i)),
                    pr.WHITE,
                )
            # north east wall
            for i in range(1, self.WORLD_HEIGHT - 1):
                pr.draw_texture(
                    self.walls[(i & 1) + 2],
                    *self.tile_to_screen_space_i32(float(i), float(self.WORLD_HEIGHT - 1)),
                    pr.WHITE,
                )
            # west corner wall
            pr.draw_texture(self.walls[8], *self.tile_to_screen_space_i32(0, 0), pr.WHITE)
            # east corner wall
            pr.draw_texture(
                self.walls[10],
                *self.tile_to_screen_space_i32(self.WORLD_WIDTH - 1, self.WORLD_HEIGHT - 1),
                pr.WHITE,
            )

            pr.rl_draw_render_batch_active()
            pr.rl_enable_depth_test()

            character_texture: pr.Texture2D
            if self.is_moving:
                animation_index = int((self.char_anim_accumulator * 15.0) % 10.0)
                character_texture = self.character_textures[
                    f"Male_{self.char_dir}_Run{animation_index}.png"
                ]
            else:
                wait_time = float(2)
                if self.char_anim_accumulator > wait_time:
                    animation_index = int(((self.char_anim_accumulator - wait_time) * 10.0) % 10.0)
                    if (
                        animation_index == 0
                        and ((self.char_anim_accumulator - wait_time) * 10.0) > 9
                    ):
                        character_texture = self.character_textures[
                            f"Male_{self.char_dir}_Idle0.png"
                        ]
                        self.global_rand.seed()  # optional. reseed for less predictable behavior
                        self.char_anim_accumulator -= random.uniform(1, 6)
                    else:
                        character_texture = self.character_textures[
                            f"Male_{self.char_dir}_Pickup{animation_index}.png"
                        ]
                else:
                    character_texture = self.character_textures[f"Male_{self.char_dir}_Idle0.png"]

            u, v = self.char_pos.x, self.char_pos.y
            x, y = self.tile_to_screen_space(u, v)
            self.draw_object(character_texture, x, y)

            # place objects and collision boxes in world
            for i in range(int(self.WORLD_WIDTH * self.WORLD_HEIGHT)):
                if self.frame_rand.randint(0, 4) != 0:
                    continue

                u = float(i // self.WORLD_WIDTH)
                v = float(self.WORLD_HEIGHT - 1 - (i % self.WORLD_HEIGHT))
                if u == self.WORLD_WIDTH - 1:
                    u -= 1
                if v == 0:
                    v += 1
                x, y = self.tile_to_screen_space(u, v)

                obj = self.frame_rand.choice(self.objects[:])
                self.draw_object(obj.texture, x, y)

                obj_box = pr.Rectangle(
                    obj.hit_box.x,
                    obj.hit_box.y,
                    obj.hit_box.width,
                    obj.hit_box.height,
                )
                obj_box.x += u
                obj_box.y += v
                self.coll_boxes.append(obj_box)

            pr.rl_draw_render_batch_active()
            pr.rl_disable_depth_test()

            # south east wall
            for i in range(1, self.WORLD_HEIGHT - 1):
                pr.draw_texture(
                    self.walls[(i & 1) + 4],
                    *self.tile_to_screen_space_i32(
                        float(self.WORLD_WIDTH - 1),
                        float(self.WORLD_HEIGHT - 1 - i),
                    ),
                    pr.WHITE,
                )
            # south west wall
            for i in range(1, self.WORLD_HEIGHT - 1):
                pr.draw_texture(
                    self.walls[7 - (i & 1)],
                    *self.tile_to_screen_space_i32(float(i), 0),
                    pr.WHITE,
                )
            # south corner wall
            pr.draw_texture(
                self.walls[11],
                *self.tile_to_screen_space_i32(self.WORLD_WIDTH - 1, 0),
                pr.WHITE,
            )

            # draw collision boxes. debugging
            if True:
                try:
                    pr.rl_begin(pr.RL_LINES)
                    pr.rl_color4f(1, 0, 1, 1)

                    for box in self.coll_boxes:
                        pr.rl_vertex2f(*self.tile_to_screen_space(box.x, box.y))
                        pr.rl_vertex2f(*self.tile_to_screen_space(box.x + box.width, box.y))

                        pr.rl_vertex2f(*self.tile_to_screen_space(box.x + box.width, box.y))
                        pr.rl_vertex2f(
                            *self.tile_to_screen_space(box.x + box.width, box.y + box.height),
                        )

                        pr.rl_vertex2f(
                            *self.tile_to_screen_space(box.x + box.width, box.y + box.height),
                        )
                        pr.rl_vertex2f(*self.tile_to_screen_space(box.x, box.y + box.height))

                        pr.rl_vertex2f(*self.tile_to_screen_space(box.x, box.y + box.height))
                        pr.rl_vertex2f(*self.tile_to_screen_space(box.x, box.y))

                    box = character_hit_box
                    pr.rl_color4f(0, 1, 0, 1)
                    pr.rl_vertex2f(*self.tile_to_screen_space(box.x, box.y))
                    pr.rl_vertex2f(*self.tile_to_screen_space(box.x + box.width, box.y))

                    pr.rl_vertex2f(*self.tile_to_screen_space(box.x + box.width, box.y))
                    pr.rl_vertex2f(
                        *self.tile_to_screen_space(box.x + box.width, box.y + box.height),
                    )

                    pr.rl_vertex2f(
                        *self.tile_to_screen_space(box.x + box.width, box.y + box.height),
                    )
                    pr.rl_vertex2f(*self.tile_to_screen_space(box.x, box.y + box.height))

                    pr.rl_vertex2f(*self.tile_to_screen_space(box.x, box.y + box.height))
                    pr.rl_vertex2f(*self.tile_to_screen_space(box.x, box.y))
                finally:
                    pr.rl_end()

            pr.end_shader_mode()
            pr.end_mode_2d()
            pr.end_texture_mode()

            pr.begin_drawing()
            pr.clear_background(pr.BLACK)

            # -------------------- #
            # Resizable Window Data. Added to draw_texture_pro
            # window dimensions
            win_width = pr.get_screen_width()
            win_height = pr.get_screen_height()
            # scale that best fits the game dimensions in the current window:
            scale = min(
                win_width / self.GAME_WIDTH,
                win_height / self.GAME_HEIGHT,
            )
            scaled_width = int(self.GAME_WIDTH * scale)
            scaled_height = int(self.GAME_HEIGHT * scale)
            # Center it in the window (letterbox or pillarbox):
            offset_x = (win_width - scaled_width) // 2
            offset_y = (win_height - scaled_height) // 2
            # -------------------- #

            # draw part of a texture defined by a rectangle with 'pro' parameters
            # allows specifying source rectangle, destination rectangle, rotation, and tinting
            pr.draw_texture_pro(
                self.render_target.texture,
                (
                    0,
                    0,  # source rectangle position
                    float(self.render_target.texture.width),  # source rectangle width
                    -float(self.render_target.texture.height),  # source rectangle height
                ),
                (
                    offset_x,
                    offset_y,  # dest x, y (letterboxed)
                    scaled_width,
                    scaled_height,  # dest width, height
                ),  # destination rectangle
                (0, 0),  # origin point for rotation
                0,  # rotation angle in degrees
                pr.WHITE,  # tint color
            )

            # draw debugging info on screen
            if True:
                # show fps
                pr.draw_text(f"{pr.get_fps()}", 10, 10, 20, pr.DARKGREEN)
                # character direction debugging
                pr.draw_text(f"x:{self.char_dp.x}, y:{self.char_dp.y}", 10, 35, 20, pr.DARKGREEN)
                # gamepad debugging
                pr.draw_text(f"{self.gamepad_angle:.1f}", 10, 60, 20, pr.DARKGREEN)
                pr.draw_text(f"{self.gamepad_magnitude:.1f}", 10, 85, 20, pr.DARKGREEN)
                # collision debugging
                if self.was_collision:
                    pr.draw_text("COLLISION", 10, 110, 20, pr.DARKGREEN)

            pr.end_drawing()

            self.char_anim_accumulator += self.dt
            # reset anim accumulator when character transitions between moving and not moving states
            if (self.was_moving and not self.is_moving) or (not self.was_moving and self.is_moving):
                self.char_anim_accumulator = 0

            # store current move state for next frame comparison
            self.was_moving = self.is_moving

    def _determine_base_dir(self) -> Path:
        """Determine if application is running in bundled mode
        and return appropriate base directory.
        """
        # determine if application is running in bundled mode
        if getattr(sys, "frozen", False):
            # running as bundled exe
            return Path(sys._MEIPASS)
        # running in normal Python environment
        return Path(__file__).parent.parent

    def load_directory_of_textures(self, relative_pattern: str) -> dict[str, pr.Texture2D]:
        """Load textures from directory matching pattern into textures dict."""
        search_directory_str = (self.base_dir / relative_pattern.rsplit("/*.")[0]).as_posix()
        search_directory = Path(search_directory_str)
        file_pattern = "*.png"

        try:
            matches = list(search_directory.glob(file_pattern))
            for match in matches:
                name = match.name
                self.textures[name] = pr.load_texture(str(match))
                # self.logger.info(f"Loaded Texture: {match}")
        except FileNotFoundError:
            self.logger.exception(f"Directory not found: {search_directory}")
        except Exception as e:
            self.logger.exception(f"Pathlib error: {e}")

        return self.textures

    def unload_directory_of_textures(self, textures: dict[str, pr.Texture2D]) -> None:
        """Unload all textures and clear the textures dict."""
        for path, tex in textures.items():
            pr.unload_texture(tex)
            # self.logger.info(f"Unloaded Texture: {path}")
        textures.clear()

    def draw_object(self, texture: pr.Texture2D, x: float, y: float) -> None:
        """Draw texture at the specified coordinates."""
        if texture.id <= 0:
            return

        w, h = float(texture.width), float(texture.height)

        # begin
        pr.rl_set_texture(texture.id)
        pr.rl_begin(pr.RL_QUADS)

        pr.rl_color4f(1, 1, 1, 1)
        pr.rl_normal3f(0.0, 0.0, 1.0)

        # Top-left
        pr.rl_tex_coord2f(0, 0)
        pr.rl_vertex3f(x, y, 0)
        # Bottom-left
        pr.rl_tex_coord2f(0, 1)
        pr.rl_vertex3f(x, y + h, -1)
        # Bottom-right
        pr.rl_tex_coord2f(1, 1)
        pr.rl_vertex3f(x + w, y + h, -1)
        # Top-right
        pr.rl_tex_coord2f(1, 0)
        pr.rl_vertex3f(x + w, y, 0)

        # end
        pr.rl_end()
        pr.rl_set_texture(0)

    def tile_to_screen_space(self, u: float, v: float) -> tuple[float, float]:
        """Convert isometric coordinates to screen coordinates."""
        x = (u + v) * 0.5
        y = (u - v) * 0.5
        x *= TILE_WIDTH
        y *= TILE_HEIGHT
        y -= TILE_FULL_HEIGHT - TILE_HEIGHT
        return x, y

    def tile_to_screen_space_i32(self, u: float, v: float) -> tuple[int, int]:
        """Convert isometric coordinates to integer screen coordinates."""
        x, y = self.tile_to_screen_space(u, v)
        return int(x), int(y)

    def tile_to_screen_space_vector(self, uv: pr.Vector2) -> pr.Vector2:
        """Convert isometric Vector2 coordinates to screen Vector2 coordinates."""
        x = (uv.x + uv.y) * 0.5
        y = (uv.x - uv.y) * 0.5
        x *= TILE_WIDTH
        y *= TILE_HEIGHT
        y -= TILE_FULL_HEIGHT - TILE_HEIGHT
        return pr.Vector2(x, y)


if __name__ == "__main__":
    # using context manager
    # implements __enter__ and __exit__ methods to handle initialization and cleanup
    with PysoRealm() as realm:
        realm.run_game_loop()
