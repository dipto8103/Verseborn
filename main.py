import socket
import json
import sys
import google.generativeai as genai
from instructions import first_agent, describer_agent, coding_agent
from utils import convert_text_to_dict, parse_enhancements_to_dict
from dotenv import load_dotenv
import os
import re

# Load environment variables (e.g., GEMINI_API_KEY)
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure the Generative AI model with the API key
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("Error: GEMINI_API_KEY not found. Please set it in your .env file.")
    sys.exit(1)

# Initialize the Generative AI agents
agent = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=first_agent,
)

describer = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=describer_agent
)

coder = genai.GenerativeModel(
    model_name="gemini-2.5-pro", # Using the specified model for coder
    system_instruction=coding_agent
)

# def send_to_blender(script_code):
#     """
#     Connects to the Blender MCP server, sends a script, and returns the response.
#     """
#     HOST = 'localhost'
#     PORT = 8000
#     command = {
#         "type": "execute_code",
#         "params": {"code": script_code}
#     }
#     message = json.dumps(command)

#     print(f"Connecting to Blender on {HOST}:{PORT}...")
#     try:
#         with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#             s.connect((HOST, PORT))
#             print("Connection successful. Sending command...")
#             s.sendall(message.encode('utf-8'))
            
#             response = s.recv(8192)
#             response_data = json.loads(response.decode('utf-8'))
#             print("\n--- Response from Blender ---")
#             print(json.dumps(response_data, indent=2))
#             print("---------------------------\n")
#             return response_data

#     except ConnectionRefusedError:
#         print("\nError: Connection refused. Please ensure the Blender MCP server is running.")
#         sys.exit(1)
#     except Exception as e:
#         print(f"\nAn unexpected error occurred: {e}")
#         return {"status": "error", "message": str(e)}

def send_to_blender(script_code):
    """
    Connects to the Blender MCP server, sends a script, and returns the response.
    """
    HOST = 'localhost'
    PORT = 8000
    command = {
        "type": "execute_code",
        "params": {"code": script_code}
    }
    message = json.dumps(command)

    print(f"Connecting to Blender on {HOST}:{PORT}...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            print("Connection successful. Sending command...")
            s.sendall(message.encode('utf-8'))
            
            # --- START OF FIX ---
            # Buffer the response until the transmission is complete
            response_buffer = b''
            while True:
                # Read data in chunks
                chunk = s.recv(8192)
                if not chunk:
                    # If no more data is received, the transmission is over
                    break
                response_buffer += chunk
            
            response_data = json.loads(response_buffer.decode('utf-8'))
            # --- END OF FIX ---

            print("\n--- Response from Blender ---")
            print(json.dumps(response_data, indent=2))
            print("---------------------------\n")
            return response_data

    except ConnectionRefusedError:
        print("\nError: Connection refused. Please ensure the Blender MCP server is running.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"\nError: Could not decode JSON response from Blender: {e}")
        print(f"Received data: {response_buffer.decode('utf-8', errors='ignore')}")
        return {"status": "error", "message": "Failed to decode JSON response."}
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    prompt = input("What do you want to generate?")
    
    # Generate initial response from the first agent
    response = agent.generate_content(prompt)
    
    # Save the prompt and response to a file
    with open('details.txt', 'a') as f:
        f.write(f"\n## Prompt: {prompt}\n")
        f.write(f"\n## Response: \n {response.text}")
        f.write("\n##End of this response\n")
        f.write("-" * 50)
    
    # Extract theme, details, and enhancements from the response
    theme = re.search(r"- Overall impression:\s*(.+?)(?=\n- |\Z)", response.text, re.DOTALL)
    details = convert_text_to_dict(response.text) # Assuming convert_text_to_dict is defined in utils
    enhancements = parse_enhancements_to_dict(response.text) # Assuming parse_enhancements_to_dict is defined in utils
    final_touch = re.search(r"- Any other information in this final section:\s*(.+?)(?=\n- |\Z)", response.text, re.DOTALL)
    
    if not theme:
        print("Error: Could not extract theme from agent response.")
        sys.exit(1)

    print("extracted the componenets")

    # Prepare prompt for the describer agent
    settings_prompt = f"""
    This is the description for the overall theme, this will be the base -> not objects, rather the background. You can take this as as the setting i.e. the ground, sky, ambience etc. This background space will set the mood for the entire scene. 

    The description of the setting/theme based on which you need to generate the base: {theme.group(1).strip()}

    # Give all the details, do not give anything other than the details, make sure you include numbers whenever necessary, so that it is easier to forward it to the coding agent.
    """

    # Generate setting description
    setting = describer.generate_content(settings_prompt)
    
    # Save the setting description to a file
    with open("setting.txt", "w") as f:
        f.write(f"{setting.text}")

    print("got the setting description")

#     # Prepare prompt for the coder agent
#     coding_prompt = f"""
#     You need to generate the following scene as described: {setting.text}. 
#     Please provide a Python script that can be executed in Blender to create this scene.
#     Ensure the script is self-contained and uses Blender's `bpy` module.
#     """

#     # Generate the Blender script
#     script = coder.generate_content(coding_prompt)
#     blender_script_to_run = script.text
    
#     print("\n--- Generated Blender Script ---")
#     print(blender_script_to_run)
#     print("------------------------------\n")
#     blender_script_to_run = re.sub(r'^```.*\n|\n```$', '', blender_script_to_run)
    
#     # Save the generated script to a file
#     with open("scripts.txt", "w") as f:
#         f.write(f"{blender_script_to_run}")

#     # Send the generated Blender script to Blender for execution
#     send_to_blender(blender_script_to_run)
#     print("Ran the entire code")

# ________________________________________________________________________________________________
    max_retries = 3
    blender_script_to_run = "" # Initialize to prevent reference before assignment error

    for attempt in range(max_retries):
        print(f"\n--- Code Generation Attempt {attempt + 1}/{max_retries} ---")
        
        # Prepare the prompt for the coder
        if attempt == 0:
            coding_prompt = f"Generate a Blender Python script for the following scene: {setting.text}"
        else:
            # Get the error message from the response, default to a generic message if not found
            error_message = blender_response.get('message', 'An unknown error occurred. The script did not complete as expected.')
            coding_prompt = (
                f"The previous script failed or did not complete. Please analyze the error and the code, then provide a corrected version.\n\n"
                f"ERROR/ISSUE:\n---\n{error_message}\n---\n\n"
                f"FAILED SCRIPT:\n---\n{blender_script_to_run}\n---"
            )

        print("Generating Blender script...")
        script_response = coder.generate_content(coding_prompt)
        blender_script_to_run = re.sub(r'^```(python)?\n|\n```$', '', script_response.text, flags=re.MULTILINE)

        print("\n--- Generated Blender Script ---")
        print(blender_script_to_run)
        print("------------------------------\n")

        # Send the script to Blender
        blender_response = send_to_blender(blender_script_to_run)

        # --- ENHANCED SUCCESS CHECK ---
        # A script is only successful if the status is 'success' AND it prints our success keyword.
        is_successful = False
        if blender_response and blender_response.get("status") == "success":
            # Check the 'result' from the 'result' object (stdout from the script)
            script_output = blender_response.get('result', {}).get('result', '')
            if "Scene generation complete." in script_output:
                is_successful = True
            else:
                # The script ran without crashing but didn't finish.
                # We add a custom message to inform the retry loop.
                blender_response['message'] = "The script ran without error but did not print the final 'Scene generation complete.' message, indicating an incomplete execution."

        if is_successful:
            print("✅ Script executed successfully and completely in Blender!")
            break
        else:
            print(f"❌ Script failed or was incomplete. Retrying...")
            if attempt == max_retries - 1:
                print("\n💥 Max retries reached. Could not generate a working script.")
                sys.exit(1)