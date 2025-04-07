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
logger = get_logger()

# determine if application is running in bundled mode
if getattr(sys, "frozen", False):
    # running as bundled exe
    BASE_DIR = Path(sys._MEIPASS)
else:
    # running in normal Python environment
    BASE_DIR = Path(__file__).parent.parent


def load_directory_of_textures(relative_pattern: str) -> dict[str, pr.Texture2D]:
    textures = {}
    search_directory_str = (BASE_DIR / relative_pattern.rsplit("/*.")[0]).as_posix()
    search_directory = Path(search_directory_str)
    file_pattern = "*.png"
    # logger.info(f"Search Directory: {search_directory}")
    # logger.info(f"File Pattern: {file_pattern}")

    try:
        matches = list(search_directory.glob(file_pattern))
        for match in matches:
            name = match.name
            textures[name] = pr.load_texture(str(match))
            logger.info(f"Loaded Texture: {match}")
    except FileNotFoundError:
        logger.exception(f"Directory not found: {search_directory}")
    except Exception as e:
        logger.exception(f"Pathlib error: {e}")

    return textures


def unload_directory_of_textures(textures: dict[str, pr.Texture2D]):
    for path, tex in textures.items():
        pr.unload_texture(tex)
        logger.info(f"Unloaded Texture: {path}")
    textures.clear()


def draw_object(texture: pr.Texture2D, x: float, y: float) -> None:
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


def tile_to_screen_space(u: float, v: float) -> tuple[float, float]:
    x = (u + v) * 0.5
    y = (u - v) * 0.5
    x *= TILE_WIDTH
    y *= TILE_HEIGHT
    y -= TILE_FULL_HEIGHT - TILE_HEIGHT
    return x, y


def tile_to_screen_space_i32(u: float, v: float) -> tuple[int, int]:
    x, y = tile_to_screen_space(u, v)
    return int(x), int(y)


def tile_to_screen_space_vector(uv: pr.Vector2) -> pr.Vector2:
    x = (uv.x + uv.y) * 0.5
    y = (uv.x - uv.y) * 0.5
    x *= TILE_WIDTH
    y *= TILE_HEIGHT
    y -= TILE_FULL_HEIGHT - TILE_HEIGHT
    return pr.Vector2(x, y)


# N -> Top-Right    0
# NE ->             1
# E -> Bottom-Right 2
# SE ->             3
# S -> Bottom-Left  4
# SW ->             5
# W -> Top-Left     6
# NW ->             7


def main():
    pr.set_trace_log_level(pr.TraceLogLevel.LOG_ERROR)
    pr.set_config_flags(pr.ConfigFlags.FLAG_MSAA_4X_HINT | pr.ConfigFlags.FLAG_VSYNC_HINT)
    pr.init_window(1920, 1080, "Super Isometric Game")

    scene_textures = load_directory_of_textures("res/image/scene/*.png")
    character_textures = load_directory_of_textures("res/image/characters/*.png")

    camera = pr.Camera2D()
    camera.offset = pr.Vector2(0, 0)
    camera.target = pr.Vector2(0, 0)
    camera.rotation = 0.0
    camera.zoom = 1.0
    cam_trg = 0.5
    camera.target = pr.Vector2(TILE_WIDTH * cam_trg, TILE_HEIGHT * cam_trg)

    floor = [
        scene_textures["stone_N.png"],
        scene_textures["stone_E.png"],
        scene_textures["stone_S.png"],
        scene_textures["stone_W.png"],
        scene_textures["stoneUneven_N.png"],
        scene_textures["stoneUneven_E.png"],
        scene_textures["stoneUneven_S.png"],
        scene_textures["stoneUneven_W.png"],
    ]

    ground_covering = [
        scene_textures["planksBroken_N.png"],
        scene_textures["planksBroken_E.png"],
        scene_textures["planksBroken_S.png"],
        scene_textures["planksBroken_W.png"],
    ]

    HIT_BOX_SMALL = pr.Rectangle(4 - 0.125, -3 - 0.125, 0.25, 0.25)
    HIT_BOX_MEDIUM = pr.Rectangle(4 - 0.25, -3 - 0.25, 0.5, 0.5)
    HIT_BOX_CHEST_EW = pr.Rectangle(4 - 0.125, -3 - 0.15, 0.25, 0.3)
    HIT_BOX_CHEST_NS = pr.Rectangle(4 - 0.15, -3 - 0.1, 0.3, 0.25)
    HIT_BOX_SPIRAL_N = pr.Rectangle(4 - 0.375, -3 - 0.125, 0.5, 0.5)
    HIT_BOX_SPIRAL_E = pr.Rectangle(4 - 0.125, -3 - 0.125, 0.5, 0.5)
    HIT_BOX_SPIRAL_S = pr.Rectangle(4 - 0.375, -3 - 0.375, 0.5, 0.5)
    HIT_BOX_SPIRAL_W = pr.Rectangle(4 - 0.5, -3, 0.625, 0.5)

    @dataclass
    class Object:
        texture: pr.Texture2D
        hit_box: pr.Rectangle

    objects = [
        Object(scene_textures["barrel_N.png"], HIT_BOX_SMALL),
        Object(scene_textures["barrel_E.png"], HIT_BOX_SMALL),
        Object(scene_textures["barrel_S.png"], HIT_BOX_SMALL),
        Object(scene_textures["barrel_W.png"], HIT_BOX_SMALL),
        Object(scene_textures["barrels_N.png"], HIT_BOX_MEDIUM),
        Object(scene_textures["barrels_E.png"], HIT_BOX_MEDIUM),
        Object(scene_textures["barrels_S.png"], HIT_BOX_MEDIUM),
        Object(scene_textures["barrels_W.png"], HIT_BOX_MEDIUM),
        Object(scene_textures["woodenCrate_N.png"], HIT_BOX_SMALL),
        Object(scene_textures["woodenCrate_E.png"], HIT_BOX_SMALL),
        Object(scene_textures["woodenCrate_S.png"], HIT_BOX_SMALL),
        Object(scene_textures["woodenCrate_W.png"], HIT_BOX_SMALL),
        Object(scene_textures["woodenCrates_N.png"], HIT_BOX_MEDIUM),
        Object(scene_textures["woodenCrates_E.png"], HIT_BOX_MEDIUM),
        Object(scene_textures["woodenCrates_S.png"], HIT_BOX_MEDIUM),
        Object(scene_textures["woodenCrates_W.png"], HIT_BOX_MEDIUM),
        Object(scene_textures["chestClosed_E.png"], HIT_BOX_CHEST_EW),
        Object(scene_textures["chestClosed_S.png"], HIT_BOX_CHEST_NS),
        Object(scene_textures["chestClosed_W.png"], HIT_BOX_CHEST_EW),
        Object(scene_textures["chestClosed_N.png"], HIT_BOX_CHEST_NS),
        Object(scene_textures["chestOpen_E.png"], HIT_BOX_CHEST_EW),
        Object(scene_textures["chestOpen_S.png"], HIT_BOX_CHEST_NS),
        Object(scene_textures["chestOpen_W.png"], HIT_BOX_CHEST_EW),
        Object(scene_textures["chestOpen_N.png"], HIT_BOX_CHEST_NS),
        Object(scene_textures["stoneColumn_E.png"], HIT_BOX_SMALL),
        Object(scene_textures["stoneColumn_S.png"], HIT_BOX_SMALL),
        Object(scene_textures["stoneColumn_W.png"], HIT_BOX_SMALL),
        Object(scene_textures["stoneColumn_N.png"], HIT_BOX_SMALL),
        Object(scene_textures["stoneColumnWood_E.png"], HIT_BOX_SMALL),
        Object(scene_textures["stoneColumnWood_S.png"], HIT_BOX_SMALL),
        Object(scene_textures["stoneColumnWood_W.png"], HIT_BOX_SMALL),
        Object(scene_textures["stoneColumnWood_N.png"], HIT_BOX_SMALL),
        Object(scene_textures["stairsSpiral_E.png"], HIT_BOX_SPIRAL_E),
        Object(scene_textures["stairsSpiral_S.png"], HIT_BOX_SPIRAL_S),
        Object(scene_textures["stairsSpiral_W.png"], HIT_BOX_SPIRAL_W),
        Object(scene_textures["stairsSpiral_N.png"], HIT_BOX_SPIRAL_N),
    ]

    walls = [
        scene_textures["stoneWall_E.png"],
        scene_textures["stoneWallColumnIn_E.png"],
        scene_textures["stoneWall_S.png"],
        scene_textures["stoneWallColumnIn_S.png"],
        scene_textures["stoneWall_W.png"],
        scene_textures["stoneWallColumnIn_W.png"],
        scene_textures["stoneWall_N.png"],
        scene_textures["stoneWallColumnIn_N.png"],
        scene_textures["stoneWallCorner_E.png"],
        scene_textures["stoneWallCorner_S.png"],
        scene_textures["stoneWallCorner_W.png"],
        scene_textures["stoneWallCorner_N.png"],
        scene_textures["stoneWallGateClosed_E.png"],
        scene_textures["stoneWallGateClosed_S.png"],
        scene_textures["stoneWallGateClosed_W.png"],
        scene_textures["stoneWallGateClosed_N.png"],
    ]

    render_target = pr.load_render_texture(pr.get_screen_width(), pr.get_screen_height())
    shader = pr.load_shader(f"{BASE_DIR}/res/shader/tiles.vs", f"{BASE_DIR}/res/shader/tiles.fs")

    TILE_SIZE = pr.Vector2(TILE_WIDTH, TILE_HEIGHT)

    WORLD_WIDTH = 12
    WORLD_HEIGHT = 12

    character_position = pr.Vector2(WORLD_WIDTH / 2 - 1, WORLD_HEIGHT / 2 - 1)
    character_dir = 0
    character_animation_accumulator = 0.0

    collision_boxes: list[pr.Rectangle] = []

    global_rand = random.Random(100)

    was_moving = False
    pr.set_target_fps(144)
    while not pr.window_should_close():
        frame_rand = random.Random(476)

        dt = pr.get_frame_time()

        character_dp = pr.Vector2(0, 0)

        # keyboard
        if pr.is_key_down(pr.KeyboardKey.KEY_W):
            character_dp.x -= 1
            character_dp.y += 1
        if pr.is_key_down(pr.KeyboardKey.KEY_S):
            character_dp.x += 1
            character_dp.y -= 1
        if pr.is_key_down(pr.KeyboardKey.KEY_A):
            character_dp.x -= 1
            character_dp.y -= 1
        if pr.is_key_down(pr.KeyboardKey.KEY_D):
            character_dp.x += 1
            character_dp.y += 1

        # gamepad
        gamepad_angle = 0.0
        gamepad_magnitude = 0.0
        if pr.is_gamepad_available(0):
            right_x = pr.get_gamepad_axis_movement(0, pr.GamepadAxis.GAMEPAD_AXIS_RIGHT_X)
            right_y = pr.get_gamepad_axis_movement(0, pr.GamepadAxis.GAMEPAD_AXIS_RIGHT_Y)
            deadzone = 0.4

            magnitude = math.sqrt((right_x * right_x) + (right_y * right_y))
            gamepad_magnitude = magnitude  # debugging variable
            if magnitude > deadzone:
                angle = math.degrees(math.atan2(right_x, -right_y)) % 360
                gamepad_angle = angle  # debugging variable

                # even 45 degree zones
                if angle >= 337.5 or angle < 22.5:  # up. 0
                    character_dp.x -= 1
                    character_dp.y += 1
                elif 22.5 <= angle < 67.5:  # up right. 45
                    character_dp.x += 0
                    character_dp.y += 2
                elif 67.5 <= angle < 112.5:  # right. 90
                    character_dp.x += 1
                    character_dp.y += 1
                elif 112.5 <= angle < 157.5:  # down right. 135
                    character_dp.x += 2
                    character_dp.y += 0
                elif 157.5 <= angle < 202.5:  # down. 180
                    character_dp.x += 1
                    character_dp.y -= 1
                elif 202.5 <= angle < 247.5:  # downl left. 225
                    character_dp.x += 0
                    character_dp.y -= 2
                elif 247.5 <= angle < 292.5:  # left. 270
                    character_dp.x -= 1
                    character_dp.y -= 1
                elif 292.5 <= angle < 337.5:  # up left. 315
                    character_dp.x -= 2
                    character_dp.y += 0

        is_moving = False

        match (int(character_dp.x), int(character_dp.y)):
            case (0, 2):
                character_dir, is_moving = 0, True
            case (1, 1):
                character_dir, is_moving = 1, True
            case (2, 0):
                character_dir, is_moving = 2, True
            case (1, -1):
                character_dir, is_moving = 3, True
            case (0, -2):
                character_dir, is_moving = 4, True
            case (-1, -1):
                character_dir, is_moving = 5, True
            case (-2, 0):
                character_dir, is_moving = 6, True
            case (-1, 1):
                character_dir, is_moving = 7, True

        if character_dp.x != 0 or character_dp.y != 0:
            norm = pr.vector2_normalize(character_dp)
        else:
            norm = pr.Vector2(0, 0)

        char_speed = 3.0
        character_position.x += norm.x * char_speed * dt
        character_position.y += norm.y * char_speed * dt

        # clamp character movement to world size
        character_position.x = max(0, min(character_position.x, WORLD_WIDTH - 1))
        character_position.y = max(0, min(character_position.y, WORLD_HEIGHT - 1))

        was_collision = False

        character_hit_box = pr.Rectangle(
            HIT_BOX_SMALL.x + character_position.x,
            HIT_BOX_SMALL.y + character_position.y,
            HIT_BOX_SMALL.width,
            HIT_BOX_SMALL.height,
        )

        for box in collision_boxes:
            if pr.check_collision_recs(character_hit_box, box):
                is_moving = False
                was_collision = True  # debugging

                diff = pr.get_collision_rec(character_hit_box, box)
                if diff.width > diff.height:
                    if diff.y > box.y:
                        character_position.y += diff.height
                    else:
                        character_position.y -= diff.height
                elif diff.x > box.x:
                    character_position.x += diff.width
                else:
                    character_position.x -= diff.width

        collision_boxes.clear()

        cpx, cpy = tile_to_screen_space(character_position.x, character_position.y)
        camera.target = pr.Vector2(cpx, cpy)
        camera.zoom = 1
        w = float(render_target.texture.width) * 0.5
        h = float(render_target.texture.height) * 0.5
        camera.offset = pr.Vector2(w, h)
        offset_x = TILE_SIZE.x * 0.5 * camera.zoom
        offset_y = TILE_SIZE.y * 0.5 * camera.zoom
        camera.offset = pr.Vector2(camera.offset.x - offset_x, camera.offset.y - offset_y)
        camera.offset.y -= (TILE_FULL_HEIGHT + TILE_HEIGHT) * 0.5 * camera.zoom

        pr.begin_texture_mode(render_target)
        pr.clear_background(pr.Color(30, 30, 30, 255))  # darker background
        pr.begin_mode_2d(camera)
        pr.begin_shader_mode(shader)
        pr.rl_draw_render_batch_active()
        pr.rl_disable_depth_test()

        # ground floor
        for i in range(int(WORLD_WIDTH * WORLD_HEIGHT)):
            u = i // WORLD_WIDTH
            v = WORLD_HEIGHT - 1 - (i % WORLD_HEIGHT)
            pr.draw_texture(frame_rand.choice(floor), *tile_to_screen_space_i32(u, v), pr.WHITE)
        # ground covering
        for i in range(int(WORLD_WIDTH * WORLD_HEIGHT)):
            u = i // WORLD_WIDTH
            v = WORLD_HEIGHT - 1 - (i % WORLD_HEIGHT)
            if frame_rand.randint(0, 15) != 0:
                continue
            pr.draw_texture(
                frame_rand.choice(ground_covering),
                *tile_to_screen_space_i32(u, v),
                pr.WHITE,
            )

        # north corner wall
        pr.draw_texture(walls[9], *tile_to_screen_space_i32(0, WORLD_HEIGHT - 1), pr.WHITE)
        # north west wall
        for i in range(WORLD_HEIGHT - 2):
            wall_idx = 1 - (i & 1)  # alternating index
            if (i & 5) == 1:  # specific bit pattern check
                wall_idx = 12
            pr.draw_texture(
                walls[wall_idx],
                *tile_to_screen_space_i32(0, float(WORLD_HEIGHT - 2 - i)),
                pr.WHITE,
            )
        # north east wall
        for i in range(1, WORLD_HEIGHT - 1):
            pr.draw_texture(
                walls[(i & 1) + 2],
                *tile_to_screen_space_i32(float(i), float(WORLD_HEIGHT - 1)),
                pr.WHITE,
            )
        # west corner wall
        pr.draw_texture(walls[8], *tile_to_screen_space_i32(0, 0), pr.WHITE)
        # east corner wall
        pr.draw_texture(
            walls[10],
            *tile_to_screen_space_i32(WORLD_WIDTH - 1, WORLD_HEIGHT - 1),
            pr.WHITE,
        )

        pr.rl_draw_render_batch_active()
        pr.rl_enable_depth_test()

        character_texture: pr.Texture2D
        if is_moving:
            animation_index = int((character_animation_accumulator * 15.0) % 10.0)
            character_texture = character_textures[f"Male_{character_dir}_Run{animation_index}.png"]
        else:
            wait_time = float(2)
            if character_animation_accumulator > wait_time:
                animation_index = int(((character_animation_accumulator - wait_time) * 10.0) % 10.0)
                if (
                    animation_index == 0
                    and ((character_animation_accumulator - wait_time) * 10.0) > 9
                ):
                    character_texture = character_textures[f"Male_{character_dir}_Idle0.png"]
                    global_rand.seed()  # optional. reseed for less predictable behavior
                    character_animation_accumulator -= random.uniform(1, 6)
                else:
                    character_texture = character_textures[
                        f"Male_{character_dir}_Pickup{animation_index}.png"
                    ]
            else:
                character_texture = character_textures[f"Male_{character_dir}_Idle0.png"]

        u, v = character_position.x, character_position.y
        x, y = tile_to_screen_space(u, v)
        draw_object(character_texture, x, y)

        # place objects and collision boxes in world
        for i in range(int(WORLD_WIDTH * WORLD_HEIGHT)):
            if frame_rand.randint(0, 4) != 0:
                continue

            u = float(i // WORLD_WIDTH)
            v = float(WORLD_HEIGHT - 1 - (i % WORLD_HEIGHT))
            if u == WORLD_WIDTH - 1:
                u -= 1
            if v == 0:
                v += 1
            x, y = tile_to_screen_space(u, v)

            obj = frame_rand.choice(objects[:])
            draw_object(obj.texture, x, y)

            obj_box = pr.Rectangle(
                obj.hit_box.x,
                obj.hit_box.y,
                obj.hit_box.width,
                obj.hit_box.height,
            )
            obj_box.x += u
            obj_box.y += v
            collision_boxes.append(obj_box)

        pr.rl_draw_render_batch_active()
        pr.rl_disable_depth_test()

        # south east wall
        for i in range(1, WORLD_HEIGHT - 1):
            pr.draw_texture(
                walls[(i & 1) + 4],
                *tile_to_screen_space_i32(float(WORLD_WIDTH - 1), float(WORLD_HEIGHT - 1 - i)),
                pr.WHITE,
            )
        # south west wall
        for i in range(1, WORLD_HEIGHT - 1):
            pr.draw_texture(walls[7 - (i & 1)], *tile_to_screen_space_i32(float(i), 0), pr.WHITE)
        # south corner wall
        pr.draw_texture(walls[11], *tile_to_screen_space_i32(WORLD_WIDTH - 1, 0), pr.WHITE)

        # draw collision boxes
        if True:
            try:
                pr.rl_begin(pr.RL_LINES)
                pr.rl_color4f(1, 0, 1, 1)

                for box in collision_boxes:
                    pr.rl_vertex2f(*tile_to_screen_space(box.x, box.y))
                    pr.rl_vertex2f(*tile_to_screen_space(box.x + box.width, box.y))

                    pr.rl_vertex2f(*tile_to_screen_space(box.x + box.width, box.y))
                    pr.rl_vertex2f(*tile_to_screen_space(box.x + box.width, box.y + box.height))

                    pr.rl_vertex2f(*tile_to_screen_space(box.x + box.width, box.y + box.height))
                    pr.rl_vertex2f(*tile_to_screen_space(box.x, box.y + box.height))

                    pr.rl_vertex2f(*tile_to_screen_space(box.x, box.y + box.height))
                    pr.rl_vertex2f(*tile_to_screen_space(box.x, box.y))

                box = character_hit_box
                pr.rl_color4f(0, 1, 0, 1)
                pr.rl_vertex2f(*tile_to_screen_space(box.x, box.y))
                pr.rl_vertex2f(*tile_to_screen_space(box.x + box.width, box.y))

                pr.rl_vertex2f(*tile_to_screen_space(box.x + box.width, box.y))
                pr.rl_vertex2f(*tile_to_screen_space(box.x + box.width, box.y + box.height))

                pr.rl_vertex2f(*tile_to_screen_space(box.x + box.width, box.y + box.height))
                pr.rl_vertex2f(*tile_to_screen_space(box.x, box.y + box.height))

                pr.rl_vertex2f(*tile_to_screen_space(box.x, box.y + box.height))
                pr.rl_vertex2f(*tile_to_screen_space(box.x, box.y))
            finally:
                pr.rl_end()

        pr.end_shader_mode()
        pr.end_mode_2d()
        pr.end_texture_mode()

        pr.begin_drawing()
        pr.clear_background(pr.WHITE)
        pr.draw_texture_pro(
            render_target.texture,
            (0, 0, float(render_target.texture.width), -float(render_target.texture.height)),
            (0, 0, float(pr.get_screen_width()), float(pr.get_screen_height())),
            (0, 0),
            0,
            pr.WHITE,
        )
        pr.draw_fps(10, 10)

        if True:
            # character direction debugging
            pr.draw_text(f"x:{character_dp.x}, y:{character_dp.y}", 10, 35, 20, pr.DARKGREEN)
            # gamepad debugging
            pr.draw_text(f"{gamepad_angle:.1f}", 10, 60, 20, pr.DARKGREEN)
            pr.draw_text(f"{gamepad_magnitude:.1f}", 10, 85, 20, pr.DARKGREEN)
            # collision debugging
            if was_collision:
                pr.draw_text("COLLISION", 10, 110, 20, pr.DARKGREEN)

        pr.end_drawing()

        character_animation_accumulator += dt
        if (was_moving and not is_moving) or (not was_moving and is_moving):
            character_animation_accumulator = 0

        was_moving = is_moving

    pr.unload_shader(shader)
    pr.unload_render_texture(render_target)
    unload_directory_of_textures(scene_textures)
    unload_directory_of_textures(character_textures)
    pr.close_window()


def logging_test():
    logger.debug(
        "Detailed information, typically of interest only for diagnosing problems",
    )
    logger.info("Confirmation that things are working as expected")
    logger.warning("An indication that something unexpected happened")
    logger.error("The software has not been able to perform some function")
    logger.critical(
        "A serious error, indicating that the program itself may be unable to continue running",
    )


if __name__ == "__main__":
    main()
