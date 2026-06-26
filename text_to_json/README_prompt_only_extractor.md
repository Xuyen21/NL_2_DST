# Prompt-Only DomainStory Extractor

This runner calls the LLM without `Instructor`, using one of the prompt-only strategies from `langgraph_module/prompts/domain_story_prompt_only_strategies.py`.

## What it does
1. loads a text story from a file
2. sends it to the model with a selected prompt strategy
3. saves the raw model response
4. tries to parse JSON from the response
5. validates the parsed payload against `DomainStory`
6. saves the validated JSON

## File
- `text_to_json/extract_domain_story_prompt_only.py`

## Example commands
```powershell
python .\text_to_json\extract_domain_story_prompt_only.py --strategy zero_shot
python .\text_to_json\extract_domain_story_prompt_only.py --strategy few_shot --input-path "C:\code\NL_2_DST\alphorn_text\alphorn-1-standardcase.txt"
python .\text_to_json\extract_domain_story_prompt_only.py --strategy chain_of_thought --output-path "C:\code\NL_2_DST\instructor\output\cot_prompt_only.json"
```

## Notes
- The script uses the plain OpenAI client from `model_init/openAI.py`.
- It does not use `Instructor` or `response_model`.
- If the model returns extra text around the JSON, the script attempts to extract the first balanced JSON object before validating it.
- If validation fails, the raw output file is still useful for error analysis.

