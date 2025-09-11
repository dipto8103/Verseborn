import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urlparse
import os
from datetime import datetime

def scrape_headings_and_definitions(url):
    """Scrape headings and definition terms from a single URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return {'error': str(e), 'url': url}

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find all heading tags and definition terms
    elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'dt'])
    
    result = {}
    stack = [{'level': 0, 'type': 'root', 'children': result}]

    for element in elements:
        if element.name.startswith('h'):
            # Handle heading tags
            level = int(element.name[1])
            text = element.get_text(strip=True)
            element_type = 'heading'
        elif element.name == 'dt':
            # Handle definition terms
            level = 7  # Give dt a higher level than h6 to make it a child of the last heading
            text = element.get_text(strip=True)
            element_type = 'definition'
        else:
            continue

        # Find the correct parent in the stack
        while stack and stack[-1]['level'] >= level:
            stack.pop()

        # Ensure the parent exists in the stack
        if not stack:
            break

        parent = stack[-1]['children']
        
        if element_type == 'heading':
            # For headings, create a new nested dictionary
            new_node = {}
            parent[text] = new_node
            stack.append({'level': level, 'type': element_type, 'children': new_node})
        else:
            # For definition terms, add as a string value (not nested)
            if '_definitions' not in parent:
                parent['_definitions'] = []
            parent['_definitions'].append(text)

    return result

def get_domain_name(url):
    """Extract domain name from URL for filename"""
    parsed_url = urlparse(url)
    return parsed_url.netloc.replace('www.', '').replace('.', '_')

def save_to_json(data, filename):
    """Save data to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_to_txt(data, filename):
    """Save data to readable text file"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"Scraping Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")
        
        for url, content in data.items():
            f.write(f"URL: {url}\n")
            f.write("-" * 40 + "\n")
            
            if 'error' in content:
                f.write(f"Error: {content['error']}\n\n")
            else:
                write_nested_structure(f, content, 0)
                f.write("\n")
            f.write("=" * 50 + "\n\n")

def write_nested_structure(file_obj, data, indent):
    """Helper function to write nested structure to file"""
    for key, value in data.items():
        if key == '_definitions':
            file_obj.write(' ' * indent + f"Definitions: {value}\n")
        elif isinstance(value, dict):
            file_obj.write(' ' * indent + f"{key}:\n")
            write_nested_structure(file_obj, value, indent + 2)
        else:
            file_obj.write(' ' * indent + f"{key}: {value}\n")

def scrape_multiple_urls(url_list):
    """Scrape multiple URLs and return combined results"""
    results = {}
    
    print(f"Starting to scrape {len(url_list)} URLs...\n")
    
    for i, url in enumerate(url_list, 1):
        print(f"Scraping URL {i}/{len(url_list)}: {url}")
        results[url] = scrape_headings_and_definitions(url)
    
    return results

def main():
    # List of URLs to scrape
    urls = [
        "https://docs.blender.org/manual/en/latest/scene_layout/scene/properties.html",
        "https://docs.blender.org/manual/en/latest/scene_layout/object/types.html",
        "https://docs.blender.org/manual/en/latest/scene_layout/object/origin.html",
        "https://docs.blender.org/manual/en/latest/scene_layout/object/selecting.html",
        "https://docs.blender.org/manual/en/latest/scene_layout/object/editing/transform/control/numeric_input.html",
        "https://docs.blender.org/manual/en/latest/scene_layout/object/editing/shading.html",
        "https://docs.blender.org/manual/en/latest/sculpt_paint/selection_visibility.html",
        "https://docs.blender.org/manual/en/latest/sculpt_paint/brush/texture.html",
        "https://docs.blender.org/manual/en/latest/grease_pencil/materials/properties.html",
        "https://docs.blender.org/manual/en/latest/render/cycles/material_settings.html",
        "https://docs.blender.org/manual/en/latest/render/cycles/optimizations/reducing_noise.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/input/ao.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/input/attribute.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/input/bevel.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/input/camera_data.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/input/fresnel.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/input/geometry.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/input/layer_weight.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/output/aov.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/output/material.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/output/light.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/output/world.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/background.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/diffuse.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/emission.html",
        'https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/glass.html',
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/glossy.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/hair.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/holdout.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/mix.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/metallic.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/principled.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/hair_principled.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/volume_principled.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/ray_portal.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/refraction.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/specular_bsdf.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/sss.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/toon.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/translucent.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/transparent.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/sheen.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/volume_absorption.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/volume_scatter.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/volume_coefficients.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/brick.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/checker.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/environment.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/gabor.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/gradient.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/ies.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/image.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/magic.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/noise.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/point_density.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/sky.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/voronoi.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/wave.html",
        "https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/white_noise.html",
        # Add more URLs here
    ]
    
    # Or read URLs from a file
    # with open('urls.txt', 'r') as f:
    #     urls = [line.strip() for line in f if line.strip()]
    
    # Scrape all URLs
    all_results = scrape_multiple_urls(urls)
    
    # Create output directory if it doesn't exist
    os.makedirs('scraping_results', exist_ok=True)
    
    # Generate timestamp for filenames
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save results
    json_filename = f'scraping_results/results_{timestamp}.json'
    txt_filename = f'scraping_results/results_{timestamp}.txt'
    
    save_to_json(all_results, json_filename)
    save_to_txt(all_results, txt_filename)
    
    print(f"\nResults saved to:")
    print(f"JSON: {json_filename}")
    print(f"Text: {txt_filename}")
    
    # Print summary
    successful = sum(1 for result in all_results.values() if 'error' not in result)
    print(f"\nScraping completed: {successful} successful, {len(urls) - successful} failed")

if __name__ == "__main__":
    main()