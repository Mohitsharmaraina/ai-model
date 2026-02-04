import csv
import json
import io

def process_mixed_data(input_stream, system_prompt: str):
    """
    Parses CSV and generates JSONL. 
    Adapts format based on presence of 'image_url'.
    """
    output = io.StringIO()
    
    # Use DictReader so we can access columns by name
    # Expected CSV Headers: user_input, assistant_output, image_url
    reader = csv.DictReader(input_stream)

    for row in reader:
        # basic validation to ensure we have content
        if not row.get("user_input") or not row.get("assistant_output"):
            continue

        user_input = row["user_input"].strip()
        assistant_output = row["assistant_output"].strip()
        image_url = row.get("image_url", "").strip()

        # 1. Start with System Message
        messages = [
            {"role": "system", "content": system_prompt}
        ]

        # 2. Add Text User Message (Always present)
        messages.append({
            "role": "user", 
            "content": user_input
        })

        # 3. Add Image User Message (ONLY if image_url exists)
        if image_url:
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url}
                    }
                ]
            })

        # 4. Add Assistant Response
        messages.append({
            "role": "assistant",
            "content": assistant_output
        })

        training_example = {"messages": messages}
        output.write(json.dumps(training_example) + '\n')

    output.seek(0)
    return output.getvalue()

# import pandas as pd
# import json
# import io

# # --- 1. The Normalizer ---
# # This function converts your complex DB structure into standard OpenAI messages
# def parse_db_turn_content(content_array):
#     """
#     Adapts your DB's content array [{'type': 'text', ...}] 
#     to OpenAI's expected format.
#     """
#     # OpenAI expects Assistant content to be a String, not an array of objects
#     # So we extract the text for assistant, but keep array for User if multimodal.
    
#     # If it's simple text, just join it
#     text_parts = [item['text'] for item in content_array if item['type'] == 'text']
#     full_text = " ".join(text_parts)
    
#     # If there are images, we need the complex array format
#     images = [item for item in content_array if item['type'] == 'image_url']
    
#     if not images:
#         return full_text  # Return simple string if no images
    
#     # If images exist, return OpenAI multimodal array structure
#     openai_content = [{"type": "text", "text": full_text}]
#     for img in images:
#         openai_content.append({
#             "type": "image_url",
#             "image_url": {"url": img['image_url']} 
#         })
#     return openai_content

# def convert_db_session_to_messages(db_record, system_prompt):
#     """Converts a full DB session (multi-turn) into one training example."""
#     messages = [{"role": "system", "content": system_prompt}]
    
#     for turn in db_record.get('turns', []):
#         # 1. Process User
#         user_content = parse_db_turn_content(turn['user']['content'])
#         messages.append({"role": "user", "content": user_content})
        
#         # 2. Process Assistant
#         # Assistant messages in fine-tuning generally require a string, not an array
#         asst_content_raw = turn['assistant']['content']
#         asst_text = " ".join([item['text'] for item in asst_content_raw if item.get('text')])
#         messages.append({"role": "assistant", "content": asst_text})
        
#     return {"messages": messages}

# def convert_excel_row_to_messages(row, system_prompt):
#     """Converts a flat Excel row (single-turn) into one training example."""
#     user_input = str(row.get("user_input", "")).strip()
#     assistant_output = str(row.get("assistant_output", "")).strip()
#     image_url = str(row.get("image_url", "")).strip()

#     if not user_input or not assistant_output:
#         return None

#     # Construct content
#     if image_url:
#         user_content = [
#             {"type": "text", "text": user_input},
#             {"type": "image_url", "image_url": {"url": image_url}}
#         ]
#     else:
#         user_content = user_input

#     messages = [
#         {"role": "system", "content": system_prompt},
#         {"role": "user", "content": user_content},
#         {"role": "assistant", "content": assistant_output}
#     ]
#     return {"messages": messages}

# # --- 2. The Main Processor ---
# def generate_finetuning_file(data_source, source_type="excel", system_prompt="You are a helpful assistant."):
#     output = io.StringIO()
    
#     # CASE A: Processing Admin Excel File
#     if source_type == "excel":
#         df = pd.read_excel(data_source).fillna("")
#         df.columns = [c.strip().lower() for c in df.columns] # normalize headers
        
#         for _, row in df.iterrows():
#             example = convert_excel_row_to_messages(row, system_prompt)
#             if example:
#                 output.write(json.dumps(example) + '\n')

#     # CASE B: Processing Database Dump (List of Dicts)
#     elif source_type == "db":
#         # data_source is expected to be a list of session objects
#         for session in data_source:
#             if not session.get('turns'): continue
#             example = convert_db_session_to_messages(session, system_prompt)
#             output.write(json.dumps(example) + '\n')

#     output.seek(0)
#     return output.getvalue()