"""
this will remove icon that has the design come with 'outline' in the name, which is not good for our use case.
We want to keep all icons and just add the semantic meaning to them.

this will also remove the field 'search_text' which was the concatenation of the name and the tags, which is not needed anymore since we will have the semantic meaning field that is optimized for vector search.

"""
import json

input_filename = r"/material_icons/mdi_icons_reduced.json"
output_filename = r"/material_icons/processed_icons.json"

try:
    with open(input_filename, 'r') as file:
        data = json.load(file)

    updated_data = []

    for item in data:
        if not item.get('name', '').endswith('-outline'):
            # .pop(key, default) removes the key if it exists,
            # otherwise it does nothing (prevents errors if the key is missing)
            item.pop('search_text', None)
            updated_data.append(item)

    with open(output_filename, 'w', encoding='utf-8') as file:
        json.dump(updated_data, file, indent=2)

    print(f"Success! {len(data) - len(updated_data)} outline icons removed.")
    print(f"Cleaned data saved to '{output_filename}'.")

except FileNotFoundError:
    print(f"Error: '{input_filename}' not found.")
except json.JSONDecodeError:
    print("Error: The file is not a valid JSON.")
