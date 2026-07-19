import os
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

from text_to_json.schema_design import DomainStory, Icon, WorkObject

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
ICON_FILE = BASE_DIR / "material_icons" / "semantics_added.json"
CHROMA_DIR = BASE_DIR / "material_icons" / "chroma_mdi_icons"
COLLECTION_NAME = "mdi_icons"

# 2. Native OpenAI embedding setup
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.environ.get("OPENAI_API_KEY"),
    model_name="text-embedding-3-small"
)


def get_icon_store():
    # 3. Connect directly to the existing directory
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # We grab the existing collection.
    # (Assuming it's already built. If you still need the build logic,
    # you can use client.get_or_create_collection here)
    collection = client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=openai_ef
    )
    return collection


def build_icon_query(work_object: WorkObject) -> str:
    return (
        # f"{work_object.type}. "
        f"{work_object.description}. "
        f"{work_object.name}"
    )


# -------------------------
# 2. Icon search node
# -------------------------
def search_icons(extracted_story: DomainStory) -> DomainStory:
    try:
        updated_work_objects = []
        collection = get_icon_store()

        for work_object in extracted_story.work_objects:
            query = build_icon_query(work_object)

            # 4. Native Chroma query syntax
            results = collection.query(
                query_texts=[query],
                n_results=1
            )

            # 5. Parse the native results structure
            # Chroma returns lists of lists. index [0] refers to the first (and only) query text.
            if results and results["ids"] and len(results["ids"][0]) > 0:
                metadata = results["metadatas"][0][0]
                # distance_score = results["distances"][0][0] # the least the better, the best is 0
                # confidence = 1 / (1 + distance_score)

                mdi_name = metadata.get("jsExportName")
                svg_path = metadata.get("svgPath")

                if mdi_name and svg_path:
                    updated_work_object = work_object.model_copy(
                        update={
                            "icon": Icon(
                                mdi_name=mdi_name,
                                svg=svg_path,
                            )
                        }
                    )
                else:
                    updated_work_object = work_object.model_copy(update={"icon": None})
            else:
                updated_work_object = work_object.model_copy(update={"icon": None})

            updated_work_objects.append(updated_work_object)

        updated_entities = extracted_story.model_copy(
            update={"work_objects": updated_work_objects}
        )

        return updated_entities

    except Exception as e:
        raise RuntimeError(f"Icon search failed: {e}") from e

# if __name__ == "__main__":
#     output_path = Path(r"C:\code\NL_2_DST\alphorn_json\alphorn-5.json")
#     raw = load_json(str(output_path))
#     extracted_story = DomainStory.model_validate(raw)
#
#     print("add icons ... ")
#     new = search_icons(extracted_story)
#     ...