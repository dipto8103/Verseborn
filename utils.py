import re
import json

description = """"""

def convert_text_to_dict(text_block: str) -> dict:
    lines = text_block.split('\n')
    
    output_dict = {} 
    current_category_name = None 
    
    in_key_elements_section = False 
    
    item_regex = re.compile(r"^\s{8}-\s\((.*?)\):\s(.*)$")

    for line in lines:
        stripped_line_content = line.strip() 

        if stripped_line_content == "- Key Elements and Details":
            in_key_elements_section = True
            continue 
        
        if not in_key_elements_section:
            continue

        if line.startswith("- ") and not line.startswith("  -"):
            in_key_elements_section = False
            break 

        if line.startswith("    - ") and not line.startswith("        "):
            category_name_candidate = line[len("    - "):].strip()
            if not category_name_candidate.startswith("("):
                current_category_name = category_name_candidate
                output_dict[current_category_name] = {}  
                continue

        if current_category_name and line.startswith("        - ("):
            item_match = item_regex.match(line)
            if item_match:
                item_name = item_match.group(1).strip()
                item_description = item_match.group(2).strip()  
                
                if current_category_name in output_dict: 
                    output_dict[current_category_name][item_name] = item_description
                continue  
                
    return output_dict

def parse_enhancements_to_dict(text_block: str) -> dict:
    lines = text_block.split('\n')
    output_dict = {}
    in_enhancements_section = False

    item_regex = re.compile(r"^\s{4}-\s(.*?):\s(.*)$")

    for line in lines:
        stripped_line_content = line.strip()

        if stripped_line_content == "- Final specific enhancements and details to enrich the scene":
            in_enhancements_section = True
            continue

        if not in_enhancements_section:
            continue

        if line.startswith("- ") and not line.startswith("  -"):
            in_enhancements_section = False
            break

        if line.startswith("    - "):
            item_match = item_regex.match(line)
            if item_match:
                item_name = item_match.group(1).strip()
                item_description = item_match.group(2).strip()
                output_dict[item_name] = item_description
                continue
    return output_dict
