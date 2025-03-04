import pandas as pd
import numpy as np
import torch
import time
import json
from transformers import AutoModelForCausalLM, AutoTokenizer

# # Load and preprocess your data
# df = pd.read_csv("/app/data/relevance_Qwen.csv", encoding='latin1')
# df = df[(df["relevance"] == "Yes") & (df["Document Body"].str.len() <= 5000)].reset_index(drop=True)

# def extract_documentation_from_dataframe(df):
#     documentation = ""
#     for _, row in df.iterrows():
#         title = row['Document Title']  # Adjust if necessary
#         content = row['Document Body']  # Adjust if necessary
#         documentation += f"### {title}\n\n{content}\n\n"
#     return documentation

# documentation_text = extract_documentation_from_dataframe(df)

# Open the .txt file and read its content
with open("/app/data/manual_new.txt", "r") as file:
    file_content = file.read()  # Read the entire content of the file

# Reading JSON from a file
with open('/app/data/content.json', 'r') as file:
    content = json.load(file)

documentation_text = file_content

# Load the tokenizer and model
Hermes_model = AutoModelForCausalLM.from_pretrained(
    "NousResearch/Hermes-3-Llama-3.1-8B",
    device_map="auto",
    torch_dtype=torch.float16,
    local_files_only=True,

)

Hermes_tokenizer = AutoTokenizer.from_pretrained("NousResearch/Hermes-3-Llama-3.1-8B")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

generation_kwargs = {
    "max_new_tokens": 1500,
    "do_sample": False,
    "eos_token_id": Hermes_tokenizer.eos_token_id,
}

Text = f"""
You are an experienced instructor specializing in {content["Topic"]}. Your goal is to **write** a short, {content["Level"]} course for {content["Audience"]} on how to {content["Task"]} using {content["Topic"]}.

**Course Requirements:**

- **Audience:** {content["Audience"]}.
- **Style:** Clear, concise, and engaging language. Use step-by-step instructions.
- **Formatting:** Provide detailed explanations, examples, and practical exercises where appropriate. Avoid creating just an outline.

**Course Content:**

1. **Introduction:**
   - Explain what {content["Topic"]} is.
   - Describe the purpose of the course.

2. **Step-by-Step Guide:**
   - Provide detailed instructions on how to {content["Task"]}.
   - Include screenshots or diagrams (describe them in text).
   - Offer tips or common pitfalls to avoid.

3. **Conclusion:**
   - Summarize the key takeaways.
   - Suggest next steps for learning.

**Length:** {content["Length"]}.

**Use the following documentation to ensure the information is accurate and comprehensive.

**Documentation:**

{documentation_text}

Please write the full course content, elaborating on each section with detailed explanations and instructions. Do not provide an outline. Begin now.
"""

Text_no_template = f"""
You are an experienced instructor specializing in {content["Topic"]}. Your goal is to **write** a short, {content["Level"]} course for {content["Audience"]} on how to {content["Task"]} using {content["Topic"]}.

**Course Requirements:**

- **Audience:** {content["Audience"]}.
- **Style:** Clear, concise, and engaging language. Use step-by-step instructions.
- **Formatting:** Provide detailed explanations, examples, and practical exercises where appropriate. Avoid creating just an outline.
- **Length:** {content["Length"]}.

**Use the following documentation to ensure the information is accurate and comprehensive.

**Documentation:**

{documentation_text}

Please write the full course content, elaborating on each section with detailed explanations and instructions. Do not provide an outline. Begin now.
"""

messages = [
    {
        "role": "system",
        "content": "You are an experienced instructor specializing in NX Manufacturing CAM software."
    },
    {
        "role": "user",
        "content": Text
    }
]
gen_input = Hermes_tokenizer.apply_chat_template(messages, return_tensors="pt").to(device)
input_length = gen_input.shape[1]

# Check the length of the prompt
print(f"Input token count: {input_length}")

print("Starting generation...")
start_time = time.time()

with torch.no_grad():
    outputs = Hermes_model.generate(gen_input, **generation_kwargs)

end_time = time.time()
time_taken = end_time - start_time

# Get the generated tokens (excluding the input tokens)
generated_tokens = outputs[0][input_length:]

# Decode the generated tokens
response = Hermes_tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()

# Save the response to a file
with open('/app/result/output.txt', 'w') as file:
    file.write(response)

print("Done, Time Taken:", time_taken)
print("Tokens Generated:", generated_tokens.shape[0])