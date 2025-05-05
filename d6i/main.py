import socketserver
import threading
import keyboard
import subprocess
import os
from http.server import SimpleHTTPRequestHandler
import pymem
import csv
import json
import git

# ==== CONFIG ====

script_dir = os.path.dirname(os.path.realpath(__file__))
config_path = os.path.join(script_dir, "config.json")

def read_config():
    global INCLUDE_RAND_PATHS, RAND_CHANCE_CUTOFF, PORT
    global BROWSER_PATH, SERVER_URL, PRINT_DEBUG_INFO, PRINT_SERVER_LOGS, PRINT_KB_LOGS
    global tested_on_game_versions, process_name, spell_base_offset, spell_pointer_offsets, spell_value_type
    global recruit_base_offset, recruit_pointer_offsets, recruit_value_type
    global HOTKEY_ACTIONS
    global spell_paneH, spell_paneV, unit_paneH, unit_paneV
    global REPO_URL,GOT_INSPECTOR
    
    with open(config_path, "r") as f:
        cfg = json.load(f)
        
    spell_hk = cfg["spell_hotkey"]
    recruit_hk = cfg["recruit_hotkey"]
    castable_hk = cfg["castable_hotkey"]
    forgeable_hk = cfg["forgeable_hotkey"]
    quit_hk = cfg["quit_hotkey"]
    spell_paneH = cfg["spell_paneH"]
    spell_paneV = cfg["spell_paneV"]
    unit_paneH = cfg["unit_paneH"]
    unit_paneV = cfg["unit_paneV"]
    
    INCLUDE_RAND_PATHS = cfg["INCLUDE_RAND_PATHS"]
    RAND_CHANCE_CUTOFF = cfg["RAND_CHANCE_CUTOFF"]
    PORT = cfg["PORT"]
    BROWSER_PATH = cfg["BROWSER_PATH"]
    PRINT_DEBUG_INFO = cfg["PRINT_DEBUG_INFO"]
    PRINT_SERVER_LOGS = cfg["PRINT_SERVER_LOGS"]
    PRINT_KB_LOGS = cfg["PRINT_KB_LOGS"]
    GOT_INSPECTOR = cfg["GOT_INSPECTOR"]
    REPO_URL = cfg["REPO_URL"]

    SERVER_URL = f"http://localhost:{PORT}"

    process_name = cfg["process_name"]
    tested_on_game_versions = cfg["tested_on_game_versions"]

    spell_base_offset = int(cfg["spell_base_offset"], 16)
    spell_pointer_offsets = [int(x, 16) for x in cfg["spell_pointer_offsets"]]
    spell_value_type = cfg["spell_value_type"]

    recruit_base_offset = int(cfg["recruit_base_offset"], 16)
    recruit_pointer_offsets = [int(x, 16) for x in cfg["recruit_pointer_offsets"]]
    recruit_value_type = cfg["recruit_value_type"]
    
    # Define actions and their associated hotkeys
    HOTKEY_ACTIONS = {
        'spell': spell_hk,
        'recruit': recruit_hk,
        'castable': castable_hk,
        'forgeable': forgeable_hk,
        'close': quit_hk,
    }

# ==== /CONFIG ====

keys_to_keep = {
    'id',
    'rand1', 'link1', 'nbr1', 'mask1',
    'rand2', 'link2', 'nbr2', 'mask2',
    'rand3', 'link3', 'nbr3', 'mask3',
    'F' , 'A' , 'W', 'E', 'S', 'D', 'N', 'B', 'G', 'H'
}

# Mapping from bitmask values to path letters
BIT_TO_PATH = {
    128: 'F',
    256: 'A',
    512: 'W',
    1024: 'E',
    2048: 'S',
    4096: 'D',
    8192: 'N',
    16384: 'G',
    32768: 'B',
    65536: 'H'
}

# Reverse mapping: letter to bit
PATH_TO_BIT = {v: k for k, v in BIT_TO_PATH.items()}

# Fixed path order
PATH_ORDER = ['W', 'G', 'F', 'A', 'E', 'H', 'S', 'D', 'N', 'B']

# ================

browser_process = None  # Track the launched Firefox process
indexed_data = {}
        
def spellid_to_params(id):
    return f"?page=spell&panes=spell+{id}@{spell_paneH}@{spell_paneV}&nation=0&spellq={id}"

def recruitid_to_params(id):
    return f"?page=unit&panes=unit+{id}@{unit_paneH}@{unit_paneV}&nation=0&showids=1&unitq={id}"

def unitid_to_paths(unit_id, type):
    #type = 'spell' | 'item'
    row = indexed_data.get(str(unit_id))
    if not row:
        return ''  # or raise an error

    # Initialize levels with row value
    levels = {path: int(row[path.lower()]) if row[path.lower()] != '' else 0 for path in PATH_ORDER}

    if INCLUDE_RAND_PATHS:
        # Extract values from rand1, rand2, rand3
        for i in range(1, 4):
            rand_key = f"mask{i}"
            if rand_key in row:
                try:
                    bitmask = int(row[rand_key])
                except ValueError:
                    continue  # Skip if value is not an integer

                for bit, path in BIT_TO_PATH.items():
                    if bitmask & bit:
                        if int(row[f"rand{i}"])>= RAND_CHANCE_CUTOFF:
                            levels[path] += int(row[f"nbr{i}"])

    # Construct query string
    path_parts = [f"path{path}level={levels[path]}" for path in PATH_ORDER]
    query_string = f"?page={type}&nation=0&" + "&".join(path_parts) +"&spellgen=1"
    return query_string

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        if PRINT_SERVER_LOGS:
            super().log_message(format, *args)

    def handle(self):
        try:
            super().handle()
        except ConnectionAbortedError:
            pass  # Silently ignore
            
def start_http_server():
    os.chdir(server_dir)
    with socketserver.TCPServer(("", PORT), QuietHandler) as httpd:
        if PRINT_SERVER_LOGS:
            print(f"Serving at {SERVER_URL}")
        httpd.serve_forever()

def handle_input(action):
    global browser_process

    if action == 'spell':
        entity_id = get_entity_id(process_name, spell_base_offset, spell_pointer_offsets, spell_value_type, PRINT_DEBUG_INFO)
        formatter = spellid_to_params
    elif action == 'recruit':
        entity_id = get_entity_id(process_name, recruit_base_offset, recruit_pointer_offsets, recruit_value_type, PRINT_DEBUG_INFO)
        formatter = recruitid_to_params
    elif action == 'castable':
        entity_id = get_entity_id(process_name, recruit_base_offset, recruit_pointer_offsets, recruit_value_type, PRINT_DEBUG_INFO)
        formatter = lambda uid: unitid_to_paths(uid, 'spell')
    elif action == 'forgeable':
        entity_id = get_entity_id(process_name, recruit_base_offset, recruit_pointer_offsets, recruit_value_type, PRINT_DEBUG_INFO)
        formatter = lambda uid: unitid_to_paths(uid, 'item')
    elif action == 'close':
        if browser_process:
            if PRINT_KB_LOGS:
                print("[Alt+Q] Sending Alt+F4 to close the active window.")
            keyboard.send("alt+f4")
            browser_process = None
        return
    else:
        print(f"Unknown action: {action}")
        return

    if entity_id is not None:
        if PRINT_KB_LOGS:
            print(f"Entity ID extracted: {entity_id}")
        if(formatter(entity_id)==''):
            return
        url = SERVER_URL + formatter(entity_id)
        if PRINT_KB_LOGS:
            print(f"[{HOTKEY_ACTIONS[action].upper()}] Opening Firefox with URL: {url}")
        browser_process = subprocess.Popen([BROWSER_PATH, "--new-window", url])
    else:
        if PRINT_KB_LOGS:
            print("Failed to extract entity ID.")

def start_keyboard_listener():
    for action, hotkey in HOTKEY_ACTIONS.items():
        keyboard.add_hotkey(hotkey, lambda a=action: handle_input(a))

    print("Hotkeys active:")
    for action, hotkey in HOTKEY_ACTIONS.items():
        print(f"  {hotkey.upper()} = {action.capitalize()}")
    
    keyboard.wait()
    
def write_config(config):
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
    
def patch_file(file_path):
    # Line is -1 to actual because array 0 indexing?
    check_line = 607
    # Step 1: Load config
    with open(config_path, "r") as f:
        cfg = json.load(f)

    if cfg.get("SERVER_PATCH_APPLIED"):
        print("Patch already applied — skipping.")
        return

    # Step 2: Load file lines
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Step 3: Check target line
    expected_line = "var tag = $el.prop('tagName');"
    actual_line = lines[check_line].strip()

    if actual_line != expected_line:
        print(f"Expected line {check_line} to be:\n  {expected_line}\nBut found:\n  {actual_line}")
        print("Aborting patch.")
        return

    # Step 4: Insert patch
    insert_lines = [
        "\t\t\t\tif (k.includes('level') && pqs._parameters['page'].includes('item')){",
        "\t\t\t\t\tvar $container = $('.filters-pathlevels.panel.itemview');",
        "\t\t\t\t\t$el = $container.find('#' + k); // only find the ID within this container",
        "\t\t\t\t}"
    ]

    lines[check_line:check_line] = [line + '\n' for line in insert_lines]  # insert at line 608 (index 607)

    # Step 5: Save patched file
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print("Patch applied successfully.")

    # Step 6: Update config
    cfg["SERVER_PATCH_APPLIED"] = True
    with open(config_path, "w") as f:
        json.dump(cfg, f, indent=2)
        
def get_inspector():  
    # Check if GOT_INSPECTOR is False
    if (not GOT_INSPECTOR):
        print("Flag GOT_INSPECTOR is set to False. Cloning the repository...")
        
        # Clone the GitHub repository if it's not cloned yet
        if not os.path.exists(server_dir):
            print(f"Cloning repository from {REPO_URL} into {server_dir}...")
            try:
                git.Repo.clone_from(REPO_URL, server_dir)  # Clone using gitpython
                # Or if you want to use subprocess:
                # subprocess.run(["git", "clone", REPO_URL, CLONE_DIR], check=True)
                print("Repository cloned successfully.")
                with open(config_path, "r") as f:
                    cfg = json.load(f)
                # Step 6: Update config
                cfg["GOT_INSPECTOR"] = True
                cfg["SERVER_PATCH_APPLIED"] = False
                with open(config_path, "w") as f:
                    json.dump(cfg, f, indent=2)
                    
            except Exception as e:
                print(f"Error while cloning repository: {e}")
        else:
            print(f"Repository already exists at {server_dir}")
    else:
        print("Flag GOT_INSPECTOR is set to True, no need to clone the repository.")

def get_entity_id(process_name: str, base_offset: int, pointer_offsets: list, value_type: str, PRINT_DEBUG_INFO : bool) -> int:
    """
    Extracts the spell id from the target process.

    Args:
        process_name (str): The name of the target process.
        base_offset (int): The base offset for pointer calculation.
        pointer_offsets (list): List of offsets to traverse the pointer chain.

    Returns:
        int: The extracted value (spell id) or None if failed.
    """

    def print_dbg_info(message):
        if PRINT_DEBUG_INFO:
            print(message)
        
    try:
         # Open the process
        pm = pymem.Pymem(process_name)
    except:
         print_dbg_info(f"Error: The process '{process_name}' could not be opened.")
         return None
    
    # Get the base address of the module where the pointer is located
    module_base = None
    for module in pm.list_modules():
        if module.name.lower() == process_name.lower():
            module_base = module.lpBaseOfDll
            break

    if module_base is None:
        print_dbg_info(f"Module {process_name} not found!")
        return None

    print_dbg_info(f"Base module address: {hex(module_base)}".upper())

    # Calculate the initial address
    current_address = module_base + base_offset
    print_dbg_info(f"Initial address: {hex(current_address)}".upper())

    try:
        # Traverse the pointer chain
        for i, offset in enumerate(pointer_offsets):
            # Read the pointer value at the current address
            current_address = pm.read_ulonglong(current_address)
            if current_address is None:
                print_dbg_info(f"Failed to read memory at step {i} with offset {hex(offset)}")
                return None
            print_dbg_info(f"Address after reading pointer at step {i}: {hex(current_address)}")
            
            # Add the offset to get the next address in the chain
            current_address += offset
            print_dbg_info(f"Address after adding offset at step {i}: {hex(current_address)}")

        # Read the final value
        if current_address is not None:
            value = None
            if value_type == "ulonglong":
                value = pm.read_ulonglong(current_address)
            if value_type == "ulong":
                value = pm.read_ulong(current_address)
            if value is not None:
                print_dbg_info(f"Final value at pointer address: {hex(value)}")
                return value
            else:
                print_dbg_info("Failed to read the final value.")
                return None
        else:
            print_dbg_info("Pointer chain traversal failed.")
            return None
    except:
        print_dbg_info("Pointer chain traversal failed.")
        return None



def main():
    read_config()
    print(f"\nTested on game versions {tested_on_game_versions}, pointer offsets might not apply to other versions.")
    global server_dir
    server_dir = os.path.join(script_dir, '../', 'dom6inspector-main')
    # Download Dominions 6 Mod Inspector if needed
    get_inspector()
    # Aplly server patch if needed
    patch_file(os.path.join(server_dir, 'scripts', 'DMI', 'Utils.js' ))
    # Start HTTP server in background thread
    threading.Thread(target=start_http_server, daemon=True).start()
    csv_path = os.path.join(server_dir, 'gamedata', 'BaseU.csv')
    with open(csv_path, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        
        # Normalize headers: strip and lowercase
        reader.fieldnames = [h.strip().lower() for h in reader.fieldnames]

        # Normalize keys_to_keep too
        normalized_keys = {key.lower() for key in keys_to_keep}
        existing_keys = normalized_keys & set(reader.fieldnames)

        for row in reader:
            # Normalize each row key
            row = {k.strip().lower(): v.strip() for k, v in row.items()}
            
            row_id = row['id']
            filtered_row = {key: row[key] for key in existing_keys if key != 'id'}
            # Check if at least one value in filtered_row is not an empty string before assignment
            if any(value != '' for value in filtered_row.values()):
                indexed_data[row_id] = filtered_row

    
    print(f"Parsed {csv_path} and loaded {len(indexed_data)} relevant entries")
    
    # Start keyboard listener in main thread
    start_keyboard_listener()
    

if __name__ == "__main__":
    main()
