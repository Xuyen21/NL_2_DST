from dotenv import load_dotenv

from icons_module.icon_semantic_search_2 import search_icons
from utils.api_request import api_response

load_dotenv()



def pipeline(response_model, prompt, content):
    model = "gpt-5.4"  # 'gemini/gemini-2.5-flash'  # "gpt-4o-mini"   #
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": content}
    ]
    resp = api_response(model, messages, response_model)
    update_icons = search_icons(resp['output'])

    return update_icons.model_dump(mode="json")
