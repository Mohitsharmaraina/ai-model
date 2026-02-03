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

