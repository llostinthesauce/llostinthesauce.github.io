import os
import subprocess
import re

def get_image_dimensions(image_path):
    try:
        result = subprocess.run(['sips', '-g', 'pixelWidth', '-g', 'pixelHeight', image_path], 
                               capture_output=True, text=True)
        output = result.stdout
        width_match = re.search(r'pixelWidth: (\d+)', output)
        height_match = re.search(r'pixelHeight: (\d+)', output)
        if width_match and height_match:
            width = int(width_match.group(1))
            height = int(height_match.group(1))
            return width, height
        return 0, 0
    except Exception as e:
        print(f"Error getting dimensions for {image_path}: {e}")
        return 0, 0

def process_file(file_path):
    print(f"Processing {file_path}...")
    with open(file_path, 'r') as f:
        html = f.read()

    # Find the gallery-grid div content
    grid_pattern = re.compile(r'(<div class="gallery-grid">)(.*?)(</div>)', re.DOTALL)
    match = grid_pattern.search(html)
    if not match:
        print(f"No gallery-grid found in {file_path}")
        return

    grid_start, grid_content, grid_end = match.groups()
    
    # Extract each item
    item_pattern = re.compile(r'(<div class="gallery-grid-item[^"]*">.*?<img src="([^"]+)"[^>]*>.*?</div>)', re.DOTALL)
    items_raw = item_pattern.findall(grid_content)
    
    horizontals = []
    verticals = []

    file_dir = os.path.dirname(file_path)

    for full_item, src in items_raw:
        # Resolve absolute path
        abs_src = os.path.normpath(os.path.join(file_dir, src))
        
        width, height = get_image_dimensions(abs_src)
        
        # Strip existing new-row class
        cleaned_item = re.sub(r'gallery-grid-item\s+new-row', 'gallery-grid-item', full_item)
        
        # Horizontal if width >= height
        if width >= height:
            horizontals.append(cleaned_item)
        else:
            verticals.append(cleaned_item)

    # Rebuild the grid content
    new_items = []
    
    # Process Horizontals
    for i, item in enumerate(horizontals):
        if i % 3 == 0:
            item = item.replace('gallery-grid-item', 'gallery-grid-item new-row')
        new_items.append(item)

    # Process Verticals
    for i, item in enumerate(verticals):
        if i % 3 == 0:
            item = item.replace('gallery-grid-item', 'gallery-grid-item new-row')
        new_items.append(item)

    new_grid_content = "\n                " + "\n                ".join(new_items) + "\n        "
    
    # Replace the grid in the original HTML
    new_html = html[:match.start(2)] + new_grid_content + html[match.end(2):]
    
    with open(file_path, 'w') as f:
        f.write(new_html)

if __name__ == "__main__":
    files = [
        "galleries/cameras/canon-2022.html",
        "galleries/cameras/canon-2023.html",
        "galleries/cameras/canon-2024.html",
        "galleries/cameras/canon-2025.html",
        "galleries/cameras/canon-2026.html",
        "galleries/cameras/canon-sd400.html",
        "galleries/cameras/vivitar-pz3090.html",
        "galleries/cameras/vivitar-san-diego.html",
        "galleries/cameras/vivitar-utah.html",
        "galleries/misc/animals.html",
        "galleries/misc/long-form-root.html",
        "galleries/misc/plants-monthly-progress-feb.html",
        "galleries/misc/plants-monthly-progress-jan.html",
        "galleries/misc/plants-monthly-progress-mar.html",
        "galleries/misc/plants.html",
        "galleries/monthly/2025-01-jan.html",
        "galleries/monthly/2025-02-feb.html",
        "galleries/monthly/2025-03-mar.html",
        "galleries/monthly/2025-04-apr.html",
        "galleries/monthly/2025-05-may.html",
        "galleries/monthly/2025-06-jun.html",
        "galleries/monthly/2025-07-jul.html",
        "galleries/monthly/2025-08-aug.html",
        "galleries/monthly/2025-09-sep.html",
        "galleries/monthly/2025-10-oct.html",
        "galleries/monthly/2025-11-nov.html",
        "galleries/monthly/2025-12-dec.html",
        "galleries/monthly/2026-01-jan.html",
        "galleries/monthly/2026-02-feb.html",
        "galleries/monthly/2026-03-mar.html"
    ]
    
    base_dir = "/Users/wayne/Documents/gh/llostinthesauce.github.io"
    for f in files:
        process_file(os.path.join(base_dir, f))
