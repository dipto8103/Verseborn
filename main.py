import google.generativeai as genai
from instructions import first_agent, describer_agent
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

    setting = describer.generate_content(theme.group(1).strip())
    print(setting.text)
    with open("setting.txt", "w+") as f:
        f.write(f"{setting.text}")