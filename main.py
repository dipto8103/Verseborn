import google.generativeai as genai
from instructions import first_agent, describer_agent, coding_agent
from utils import convert_text_to_dict, parse_enhancements_to_dict
from dotenv import load_dotenv
import json
import os
import re

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

agent = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=first_agent,
)

describer = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=describer_agent
)

coder = genai.GenerativeModel(
    model_name="gemini-2.5-flash-preview-05-20",
    system_instruction=coding_agent
)

if __name__ == "__main__":
    prompt = input("What do you want to generate?")
    response = agent.generate_content(prompt)
    with open('details.txt', '+a') as f:
        f.write(f"\n## Prompt: {prompt}\n")
        f.write(f"\n## Response: \n {response.text}")
        f.write("\n##End of this response\n")
        f.write("-"*50)
    
    theme = re.search(r"- Overall impression:\s*(.+?)(?=\n- |\Z)", response.text, re.DOTALL)
    # print(theme.group(1).strip())
    details = convert_text_to_dict(response.text)
    enhancments = parse_enhancements_to_dict(response.text)
    final_touch = re.search(r"- Any other information in this final section:\s*(.+?)(?=\n- |\Z)", response.text, re.DOTALL)
    # print(final_touch.group(1).strip())
    
    settings_prompt = f"""
    This is the description for the overall theme, this will be the base -> not objects, rather the background. You can take this as as the setting i.e. the ground, sky, ambience etc. This background space will set the mood for the entire scene. 

    The description of the setting/theme based on which you need to generate the base: {theme.group(1).strip()}

    # Give all the details, do not give anything other than the details, make sure you include numbers whenever necessary, so that it is easier to forward it to the coding agent.
    """

    setting = describer.generate_content(settings_prompt)
    # print(setting.text)
    with open("setting.txt", "w+") as f:
        f.write(f"{setting.text}")

    coding_prompt = f"""
    You need to generate the following scene as described: {setting.text}. 
    """

    script = coder.generate_content(coding_prompt)
    print(script.text)
    with open("scripts.txt", "w+") as f:
        f.write(f"{script.text}") 