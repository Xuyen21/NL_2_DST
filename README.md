# NL_2_DST

## About the Project

This project simplifies the creation of Domain Storytelling by converting a domain story written in plain text into a Domain Story representation.

## Installation

It is recommended to create and activate a virtual environment before installing the dependencies.

Install the Python dependencies:

```bash
pip install uv
uv pip install -r requirements.txt
```

If you want to run the evaluation flows, install the JavaScript dependencies as well:

```bash
npm install
```

## Configuration

### Evaluation Configuration

This project requires API keys for the configured AI models. There is an example file [.env.example](.env.example) provided. 

Copy it to a new `.env` file and fill in your API keys.

You can configure which models to run for evaluation in [promptfooconfig_pilot.yaml](evaluations/promptfoo_eval/promptfooconfig_pilot.yaml) and [promptfooconfig_final.yaml](evaluations/promptfoo_eval/promptfooconfig_final.yaml) respectively.

### Streamlit Configuration

The streamlit application is using _gpt-5.5_ by default and requires the `OPENAI_API_KEY` to be set in the `.env` file.

The model can be changed in [pipeline.py](pipeline.py).

## Run the Streamlit Application

Start the app with:

```bash
streamlit run .\main.py
```

By default, Streamlit hosts the application locally at:

```text
Local URL: http://localhost:8501
```

## Evaluation

### Screening Phase

Check whether the models meet the project criteria:

```bash
python llm_prescreen.py
```

### Pilot Phase Evaluation

Run the pilot evaluation with:

```bash
npm run eval-pilot
```

If you use a different evaluation output file, update `REPORT_PATH` in `evaluations/calc_final_metrics.py` so it points to the generated report.

### Final Phase Evaluation

Run the final evaluation with:

```bash
npm run eval-final
```

To rerun different prompt versions, you can checkout the prompt file with a specific Git tag. For example:
```bash
git checkout 0.1.2 -- prompt_strategy/prompts.py```
```

### Evaluation Metrics

After running an evaluation, you can calculate the metrics with:

```powershell
$env:PYTHONPATH = "."
python .\evaluations\calc_final_metrics.py
```

If needed, adjust `REPORT_PATH` in `evaluations/calc_final_metrics.py` to match the report file produced by the evaluation command.

