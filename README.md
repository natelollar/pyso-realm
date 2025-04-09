# pyso-realm
 An isometric game prototype built with Python and Pyray (Raylib) featuring tile-based map, character animations, and collision detection. Includes game shader and gamepad support.

Made with:
- Python 3.13
- pyray (raylib)
- pyinstaller (for building executable)
- ruff (linter and formatter)
- Windows 11

Resource Image folder
- `res/image`
- Object and animation images currently not included.
    - User images needed.
- Planning to add custom images at a later date.
- Originally used images from here:
    - https://kenney.nl/assets/isometric-miniature-dungeon

Run via Python
- Add project folder path to PYTHONPATH environment variable.
- Run `__main__.py` or `rpg_game.py` via python.exe.

Build Exe
- Run `py_utils/py_build.cmd` to build the .exe with PyInstaller.  
- The .exe is portable. 
    - Will contain all images and data needed in the single .exe file.
- One can move the .exe to a new folder or computer and it'll still work.

Controls
- W/A/S/D : Moves the character on the isometric map. (keyboard)
- Gamepad : Left analog stick for movement. (Tested with Xbox Controller)
- Close Window : Press the window’s close button or Esc key to exit.

Pyray Documentation
- https://electronstudio.github.io/raylib-python-cffi/pyray.html

Inspired by this Odin programming language tutorial by Ginger Bill.
- https://youtu.be/B9kSV2TaKpw?si=bjLz4lXJsSj3GFn8

---

Features
- Isometric Tile Rendering: Renders tiles in an isometric projection, giving the game a distinctive 2.5D look.
- Character Movement: Supports diagonal movement via keyboard and analog gamepad input.
- Collision Detection: Demonstrates bounding-box collisions with in-game objects.
- Resizing: The game automatically letterboxes/pillarboxes when resized, preserving aspect ratio.
- Logging: Logs game events and errors to both the console and a log file (rpg_game.log).
