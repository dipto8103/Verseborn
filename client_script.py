import socket
import json
import sys

def send_to_blender(script_code):
    """
    Connects to the Blender MCP server and sends a script to be executed.

    Args:
        script_code (str): A string containing the Python code for Blender to run.
    """
    # Server configuration
    HOST = 'localhost'
    PORT = 8000  # This must match the port in the Blender addon

    # The command structure that the Blender addon expects
    # It needs a 'type' of 'execute_code' and the 'code' in the 'params'
    command = {
        "type": "execute_code",
        "params": {
            "code": script_code
        }
    }

    # Convert the command dictionary to a JSON string
    message = json.dumps(command)

    print(f"Connecting to Blender on {HOST}:{PORT}...")

    try:
        # Create a socket client
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Connect to the Blender server
            s.connect((HOST, PORT))
            print("Connection successful.")

            # Send the JSON message
            # It needs to be encoded into bytes
            s.sendall(message.encode('utf-8'))
            print("Sent command to Blender.")

            # Wait for a response from Blender
            response = s.recv(8192)
            response_data = json.loads(response.decode('utf-8'))

            # Print the response
            print("\n--- Response from Blender ---")
            print(json.dumps(response_data, indent=2))
            print("---------------------------\n")

    except ConnectionRefusedError:
        print("\nError: Connection refused.")
        print("Please ensure the Blender MCP server is running in Blender.")
        print("In Blender > 3D Viewport > Sidebar (N) > BlenderMCP, click 'Connect to MCP server'.")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # --- This is the script that will be executed inside Blender ---
    # You can replace this string with any script you generate from your API calls.
    blender_script_to_run = """
import bpy
import bmesh

# --- Customization Parameters ---
MANSION_SETTINGS = {
    # Overall Dimensions
    "main_width": 20.0,
    "main_depth": 14.0,
    "wing_width": 10.0,
    "wing_depth": 16.0,
    "wing_offset_z": 1.0,
    
    # Structural Details
    "floor_height": 4.0,
    "num_floors": 2,
    
    # Roof Details
    "roof_height": 4.0,
    "roof_overhang": 0.75,
    
    # Window Details
    "window_width": 1.5,
    "window_height": 2.0,
    "window_inset": 0.1,
    "window_sill_height": 1.0,
}


def clear_scene():
    
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')
    
    bpy.ops.object.select_all(action='DESELECT')
    
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
            
    bpy.ops.object.delete()
    print("Cleared existing mesh objects.")

def create_or_get_material(name, color):
    
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    else:
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = False
        mat.diffuse_color = color
        return mat

def create_building_block(name, location, dimensions, material):
    
    width, depth, height = dimensions
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.active_object
    obj.name = name
    
    obj.dimensions = (width, depth, height)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    
    obj.data.materials.append(material)
    return obj

def create_roof(name, location, dimensions, roof_height, overhang, material):
    
    width, depth, height = dimensions
    
    bpy.ops.mesh.primitive_cube_add(
        location=(location.x, location.y, location.z + height / 2)
    )
    roof_obj = bpy.context.active_object
    roof_obj.name = name
    
    roof_obj.dimensions = (width + overhang * 2, depth + overhang * 2, 0.5)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(roof_obj.data)

    top_edges = [
        e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) < 0.01
        and abs(e.verts[0].co.x - e.verts[1].co.x) > width / 2
    ]
    
    for edge in top_edges:
        edge.select = True

    bpy.ops.mesh.edge_split()
    bpy.ops.transform.translate(value=(0, 0, roof_height))
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.fill_holes()

    bpy.ops.object.mode_set(mode='OBJECT')
    
    roof_obj.data.materials.append(material)
    return roof_obj
    
def add_windows(target_obj, floor_num, settings):
    
    window_mat = create_or_get_material("Window Material", (0.6, 0.8, 1.0, 1))

    base_z = (floor_num * settings["floor_height"]) + settings["window_sill_height"]
    
    front_y = target_obj.location.y + target_obj.dimensions.y / 2
    num_windows_front = int((target_obj.dimensions.x - 2) / (settings["window_width"] * 2))
    spacing_x = target_obj.dimensions.x / (num_windows_front + 1)
    
    for i in range(num_windows_front):
        win_x = target_obj.location.x - target_obj.dimensions.x / 2 + (i + 1) * spacing_x
        win_loc = (win_x, front_y - settings["window_inset"], base_z + settings["window_height"] / 2)
        create_building_block(
            "Window", win_loc,
            (settings["window_width"], 0.2, settings["window_height"]),
            window_mat
        )

def create_mansion(settings):
   
    print("Starting mansion construction...")
    
    wall_mat = create_or_get_material("Wall Material", (0.8, 0.7, 0.6, 1))
    roof_mat = create_or_get_material("Roof Material", (0.3, 0.1, 0.1, 1))
    door_mat = create_or_get_material("Door Material", (0.4, 0.2, 0.1, 1))

    total_height = settings["floor_height"] * settings["num_floors"]

    main_dims = (settings["main_width"], settings["main_depth"], total_height)
    main_loc = (0, 0, total_height / 2)
    main_block = create_building_block("MainBlock", main_loc, main_dims, wall_mat)

    wing_dims = (settings["wing_width"], settings["wing_depth"], total_height)
    wing_x_pos = settings["main_width"] / 2 + settings["wing_width"] / 2
    wing_y_pos = (settings["wing_depth"] - settings["main_depth"]) / 2 - settings["wing_offset_z"]

    left_wing_loc = (-wing_x_pos, wing_y_pos, total_height / 2)
    right_wing_loc = (wing_x_pos, wing_y_pos, total_height / 2)

    left_wing = create_building_block("LeftWing", left_wing_loc, wing_dims, wall_mat)
    right_wing = create_building_block("RightWing", right_wing_loc, wing_dims, wall_mat)
    
    roof_base_z = total_height
    roof_dims_main = (main_block.dimensions.x, main_block.dimensions.y, 0)
    create_roof("MainRoof", main_block.location, roof_dims_main, settings["roof_height"], settings["roof_overhang"], roof_mat)

    roof_dims_wing = (left_wing.dimensions.x, left_wing.dimensions.y, 0)
    create_roof("LeftRoof", left_wing.location, roof_dims_wing, settings["roof_height"], settings["roof_overhang"], roof_mat)
    create_roof("RightRoof", right_wing.location, roof_dims_wing, settings["roof_height"], settings["roof_overhang"], roof_mat)

    for i in range(settings["num_floors"]):
        add_windows(main_block, i, settings)
        add_windows(left_wing, i, settings)
        add_windows(right_wing, i, settings)
        
    door_height = 3.0
    door_width = 2.5
    door_loc = (
        0,
        main_block.dimensions.y / 2 - settings["window_inset"],
        door_height / 2
    )
    create_building_block("MainDoor", door_loc, (door_width, 0.2, door_height), door_mat)

    print("Mansion construction complete.")

# --- Main Execution ---
# These functions are called directly when the script is executed in Blender.
clear_scene()
create_mansion(MANSION_SETTINGS)
"""

    # Send the script to Blender for execution
    send_to_blender(blender_script_to_run)