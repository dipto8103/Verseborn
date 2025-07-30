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
    model_name="gemini-2.5-pro",
    system_instruction=coding_agent
)

def send_to_blender(script_code):
    """
    Connects to the Blender MCP server, sends a script, and returns the response,
    capturing all of stdout and stderr/log output.
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
            return response_data

    except ConnectionRefusedError:
        print("\nError: Connection refused. Please ensure the Blender MCP server is running.")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    prompt = input("What do you want to generate?")
    response = agent.generate_content(prompt)
    with open('details.txt', 'a') as f:
        f.write(f"\n## Prompt: {prompt}\n")
        f.write(f"\n## Response: \n {response.text}")
        f.write("\n##End of this response\n")
        f.write("-" * 50)
    theme = re.search(r"- Overall impression:\s*(.+?)(?=\n- |\Z)", response.text, re.DOTALL)
    details = convert_text_to_dict(response.text)
    enhancements = parse_enhancements_to_dict(response.text)
    final_touch = re.search(r"- Any other information in this final section:\s*(.+?)(?=\n- |\Z)", response.text, re.DOTALL)
    if not theme:
        print("Error: Could not extract theme from agent response.")
        sys.exit(1)
    print("extracted the componenets")
    settings_prompt = f"""
    This is the description for the overall theme, this will be the base -> not objects, rather the background. You can take this as as the setting i.e. the ground, sky, ambience etc. This background space will set the mood for the entire scene. 
    The description of the setting/theme based on which you need to generate the base: {theme.group(1).strip()}
    # Give all the details, do not give anything other than the details, make sure you include numbers whenever necessary, so that it is easier to forward it to the coding agent.
    """
    setting = describer.generate_content(settings_prompt)
    with open("setting.txt", "w") as f:
        f.write(f"{setting.text}")
    print("got the setting description")

    # --- Main codegen & retry loop ---
    max_retries = 3
    blender_script_to_run = "" # to avoid reference before assignment

    for attempt in range(max_retries):
        print(f"\n--- Code Generation Attempt {attempt + 1}/{max_retries} ---")
        if attempt == 0:
            coding_prompt = f"Generate a Blender Python script for the following scene: {setting.text}"
        else:
            # Now include stderr/blender traceback (if present) in the prompt!
            # fallback to .get('message') only if both error fields missing.
            error_message = ""
            if blender_response:
                # Try to extract Blender's detailed error log if available
                if isinstance(blender_response.get('result'), dict):
                    # For legacy layout, get stdout/stderr from .result dict
                    stdout = blender_response['result'].get('stdout', '') or blender_response['result'].get('result', '')
                    stderr = blender_response['result'].get('stderr', '')
                else:
                    # For newer layout, get top-level stdout/stderr
                    stdout = blender_response.get('stdout', '') or blender_response.get('result', '')
                    stderr = blender_response.get('stderr', '')
                # Combine for best diagnostics
                if stderr:
                    error_message += stderr
                if stdout and (not stderr or "Traceback" not in stderr):
                    # Only include stdout if not superseded by detailed traceback
                    error_message += f"\n[Stdout Output]\n{stdout}"
                if not error_message:
                    error_message = blender_response.get('message', 'An unknown error occurred. The script did not complete as expected.')
            else:
                error_message = 'No response object received from Blender.'

            coding_prompt = (
                f"The previous script failed or did not complete. Please analyze the error and the code, then provide a corrected version.\n\n"
                f"ERROR/ISSUE (traceback or log):\n---\n{error_message}\n---\n\n"
                f"FAILED SCRIPT:\n---\n{blender_script_to_run}\n---"
            )
        print("Generating Blender script...")
        script_response = coder.generate_content(coding_prompt)
        blender_script_to_run = re.sub(r'^``````$', '', script_response.text, flags=re.MULTILINE)

        print("\n--- Generated Blender Script ---")
        # print(blender_script_to_run)
        print("------------------------------\n")

        # Send the script to Blender
        blender_response = send_to_blender(blender_script_to_run)

        # --- Check for Success: look for both status and explicit completion message in stdout
        is_successful = False
        stdout = ""
        # Support both legacy and updated MCP formats
        if blender_response and blender_response.get("status") == "success":
            if isinstance(blender_response.get('result'), dict):
                # Newer MCP: stdout/stderr separated
                stdout = blender_response['result'].get('stdout', '') or blender_response['result'].get('result', '')
            else:
                stdout = blender_response.get('stdout', '') or blender_response.get('result', '')
            if "Scene generation complete." in (stdout or ""):
                is_successful = True
            else:
                blender_response['message'] = "The script ran without error but did not print the final 'Scene generation complete.' message, indicating an incomplete execution."

        if is_successful:
            print("✅ Script executed successfully and completely in Blender!")
            break
        else:
            if blender_response:
                # Print detailed log for immediate debugging.
                if isinstance(blender_response.get('result'), dict):
                    print(f"❌ Script failed or was incomplete.\nSTDOUT:\n{blender_response['result'].get('stdout','')}\nSTDERR:\n{blender_response['result'].get('stderr','')}\nMESSAGE:\n{blender_response.get('message','')}")
                else:
                    print(f"❌ Script failed or was incomplete.\nSTDOUT:\n{blender_response.get('stdout','')}\nSTDERR:\n{blender_response.get('stderr','')}\nMESSAGE:\n{blender_response.get('message','')}")
            else:
                print(f"❌ Script failed or was incomplete. No response received. Retrying...")
            if attempt == max_retries - 1:
                print("\n💥 Max retries reached. Could not generate a working script.")
                sys.exit(1)
