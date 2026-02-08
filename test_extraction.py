import langextract as lx
import textwrap

# 1. Define the prompt and extraction rules
prompt = textwrap.dedent("""\
    In the context of domain storytelling,
    Extract actors and work objects from the following car leasing process description.""")

# 2. Provide a high-quality example to guide the model
examples = [
    lx.data.ExampleData(
        text="1.The customer chooses a specific car from the catalog",
        extractions=[
            lx.data.Extraction(
                extraction_class="actor",
                extraction_text="customer",
            ),
            lx.data.Extraction(
                extraction_class="work object",
                extraction_text="car",
            ),
        ]
    )
]
# The input text to be processed
input_text = """
1.The customer chooses a specific car from the catalog.

2.The customer initiates a conversation to ask the salesperson for assistance.

3.The salesperson offers a contract to the customer, which specifies the offered car and the required monthly installments.

4.The customer signs the contract document in the presence of the salesperson.

5.The salesperson passes the signed contract document on to the risk manager.

6.The risk manager assesses the financial risk associated with the contract.

7.The risk manager votes whether to approve the contract.

8.The risk manager informs the salesperson of the voting result.

9.The salesperson hands over the car to the customer.

10.The customer makes regular payments for the duration of the agreement.

11.After the leasing period ends, the customer returns the car to the salesperson.
"""

# Run the extraction
result = lx.extract(
    text_or_documents=input_text,
    prompt_description=prompt,
    examples=examples,
    model_id="gemma2:2b",  # Automatically selects Ollama provider
    model_url="http://localhost:11434",
    fence_output=False,
    use_schema_constraints=False
)
# Save the results to a JSONL file
lx.io.save_annotated_documents([result], output_name="extraction_results.jsonl", output_dir=".")

# Generate the visualization from the file
html_content = lx.visualize("extraction_results.jsonl")
with open("visualization.html", "w", encoding="utf-8") as f:
    if hasattr(html_content, 'data'):
        f.write(html_content.data)  # For Jupyter/Colab
    else:
        f.write(html_content)
