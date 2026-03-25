import json
import time
from model_init.openAI import openai_client

# ==========================================
# Configuration
# ==========================================
# Set your API key here or make sure it's in your environment variables
client = openai_client

INPUT_FILE = r"/material_icons/processed_icons.json"  #r"C:\code\NL_2_DST\material_icons\mdi_icons_reduced.json"
OUTPUT_FILE = "../semantics_added.json"
BATCH_SIZE = 50  # Process 50 icons at a time

# gpt-4o-mini is OpenAI's cheapest and highly effective model for this task
MODEL_NAME = "gpt-4o-mini"


def process_icons():
    print(f"Loading data from {INPUT_FILE}...")
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            icons = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find {INPUT_FILE}. Please check the file path.")
        return

    print(f"Total icons loaded: {len(icons)}")
    updated_icons = []
    total_batches = (len(icons) + BATCH_SIZE - 1) // BATCH_SIZE

    # Process in batches
    for i in range(0, len(icons), BATCH_SIZE):
        batch = icons[i: i + BATCH_SIZE]
        current_batch_num = (i // BATCH_SIZE) + 1
        print(f"Processing batch {current_batch_num} of {total_batches}...")

        # Strip heavy data (svgPath) to save tokens and speed up the LLM
        lightweight_batch = []
        for icon in batch:
            lightweight_batch.append({
                "name": icon.get("name"),
                "aliases": icon.get("aliases", []),
                "tags": icon.get("tags", [])
            })

        # Construct the prompt
        # Note: When using JSON mode with OpenAI, we must explicitly ask it to output a JSON object.
        prompt = f"""
                You are an expert metadata tagger preparing data for a semantic vector search engine. 
                I am providing a JSON array of UI icons with their names, aliases, and tags.

                You MUST return a JSON object containing a single key called "results". The value of "results" should be an array of objects.
                Each object in the array must have exactly two keys:
                1. "name": The exact name of the icon I provided.
                2. "semanticMeaning": A highly detailed, comma-separated string optimized for vector search. It must include three things:
                   - Visuals: What the icon literally looks like (e.g., "piece of paper with lines", "plastic card").
                   - Concepts: Abstract ideas it represents (e.g., "reports, statements, analytics, billing, finance").
                   - Actions: UI actions it triggers (e.g., "viewing a document, making a payment, generating a summary").

                Here are the icons:
                {json.dumps(lightweight_batch, indent=2)}
                """

        try:
            # Call the OpenAI API
            response = client.chat.completions.create(
                model=MODEL_NAME,
                response_format={"type": "json_object"},  # Forces strict JSON output
                messages=[
                    {"role": "system", "content": "You are a helpful data assistant designed to output JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3  # Low temperature keeps the descriptions factual and consistent
            )

            # Parse the LLM's JSON response
            response_content = response.choices[0].message.content
            semantic_data = json.loads(response_content)

            # Extract the array from the "results" key
            results_array = semantic_data.get("results", [])

            # Create a lookup dictionary for easy merging
            semantic_lookup = {
                item["name"]: item["semanticMeaning"]
                for item in results_array if "name" in item and "semanticMeaning" in item
            }

            # Merge the semantic meaning back into the original heavy objects
            for icon in batch:
                icon_name = icon["name"]
                # Add the new property, default to a fallback string if the LLM missed it
                icon["semanticMeaning"] = semantic_lookup.get(icon_name, "Represents a user interface element.")
                updated_icons.append(icon)

            # Small delay to respect rate limits (adjust based on your OpenAI tier)
            time.sleep(1)

        except Exception as e:
            print(f"Error processing batch {current_batch_num}: {e}")
            # If a batch fails, append the original batch without the new field so data isn't lost
            updated_icons.extend(batch)
            time.sleep(5)  # Wait longer if we hit an error (like a rate limit)

    # Save the final compiled list
    print(f"Saving updated data to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(updated_icons, f, indent=2)

    print("Done!")


if __name__ == "__main__":
    process_icons()