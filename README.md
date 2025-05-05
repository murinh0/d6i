# Dominions 6 Inspector Integration Tool

## Description

This is a Python utility that integrates with [larzm42's Dominions Mod Inspector](https://github.com/larzm42/dom6inspector) to quickly open unit and spell descriptions directly from *Dominions 6*.

It can also filter castable spells or forgeable items based on the paths of a commander.

## Installation

### Requirements

- [Python 3.8](https://www.python.org/downloads/) or later (includes `pip` by default)

### Steps

1. Create a new folder (e.g. `my_folder`, on Desktop)
2. Extract the contents of the archive to it
3. Open a terminal or command prompt:
   ```bash
   cd path\to\my_folder
   pip install .
    ```

4. Alternatively, clone the repo and install:
    ```bash
    git clone https://github.com/murinh0/d6i.git
    cd d6i
    pip install -e .
    ```

5. Launch it by opening a cmd and writing d6i, or using python:
    ```bash
    python C:/Users/YOURNAME/Desktop/my_folder/d6i/main.py
    ```

## Features

- 🔍 **Spell Search**  
  **Default Hotkey:** `Alt+S`  
  Opens the mod inspector at the spell currently selected in-game.

- 👥 **Unit Search**  
  **Default Hotkey:** `Alt+R`  
  Opens the inspector at the unit currently selected in-game.

- 🧙 **Castable Search**  
  **Default Hotkey:** `Alt+E`  
  Opens the inspector with a search filtered by the magic paths of the selected unit type  
  *(based on potential path rolls, not exact unit stats)*  
  - Supports disabling random path inclusion  
  - Supports customizing the minimum chance threshold for a path to be included in the search

- 🔨 **Forgeable Search**  
  **Default Hotkey:** `Alt+F`  
  Opens the inspector filtered by items forgeable with the selected unit type’s paths  
  - Also configurable for random path handling and thresholds

- ❌ **Close Current Window**  
  **Default Hotkey:** `Alt+Q`  
  Closes the currently focused window (can be *any* window, not just the browser)

## Config

The `config.json` file controls hotkeys, behavior, and integration settings. Below are explanations for each key:

### 🔑 Hotkeys and Browser 

`spell_hotkey`, `recruit_hotkey`, `forgeable_hotkey`, `castable_hotkey`, `quit_hotkey`:  
These define the keyboard shortcuts.  
Use strings like `"ctrl+alt+s"`, `"shift+k"`, or just `"j"` for single-key bindings.

`BROWSER_PATH`:  
Path to the browser executable used to open the inspector.  
**DO** set this to your chrome path or whatever you use.

---

### 🔮 Magic Path Filters

`INCLUDE_RAND_PATHS`:  
Set to `true` to include **random paths** (paths that might be rolled by the unit) in filter searches.  
Set to `false` to only use guaranteed (non-random) paths.

`RAND_CHANCE_CUTOFF`:  
Specifies the **minimum chance (%)** for a random path to be considered.  
For example, a path with a 10% roll chance will be ignored if this is set to `25`,  
but a 25% chance will be included in the filter.

---

### 🖼️ Inspector Pane Positioning

`unit_paneH` / `unit_paneV`  
`spell_paneH` / `spell_paneV`  
Control the **horizontal (H)** and **vertical (V)** positioning of the pane in the mod inspector  when opened.  
Useful for centering the window or offsetting based on screen layout.

---

### 🌐 Integration & Server

`GOT_INSPECTOR`:  
If set to `false`, the tool will attempt to automatically **clone** the dominions mod inspector repo defined in `REPO_URL`.  
If you've manually downloaded it, place the folder next to your d6i folder and set this to `true`.

`REPO_URL`:  
The GitHub URL of the Dominions Mod Inspector.  
You can change this if using a fork or mirror.

`PORT`:  
The local port used to serve the inspector.  
Change this if port `6945` is already in use on your system.

`SERVER_PATCH_APPLIED`:
Currently the mod inspector has a bug that doesn't allow deserialization of filters set on the item panel from permalink, this is a scuffed fix.

`PRINT_DEBUG_INFO`, `PRINT_SERVER_LOGS`, `PRINT_KB_LOGS`:
Print various logs 

`tested_on_game_versions`:
Game versions the provided pointer chains work on (currently `6.29` only)

`spell_base_offset`, `spell_pointer_offsets`, `spell_value_type`:
Offsets for the pointer chains used to extract the unit id and spell id from the game process, obtained using Cheat Engine.
Do not change these unless you know what you are doing


## Known Issues

- **Mouse Position Affects Detection**  
  The mouse cursor must **not** be hovering over a tag or property that shows a tooltip at the bottom of the screen.  
  This tooltip changes memory state and will interfere with extracting the correct ID.  
  **Workaround:** Move the mouse to a different area and press the hotkey again.

## Credits

- **Illwinter** – for developing [Dominions 6](https://www.illwinter.com/dom6/)
- **larzm42** – for the [Dominions Mod Inspector](https://github.com/larzm42/dom6inspector)
