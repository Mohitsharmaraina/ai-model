import pandas as pd
import json
import io

def process_mixed_data_v2(input_stream, system_prompt: str, filename: str):
    """
    Correctly processes BytesIO stream and returns a full JSONL string.
    """
    try:
        # 1. Load Data
        if filename.endswith('.csv'):
            df = pd.read_csv(input_stream)
        else:
         
            df = pd.read_excel(input_stream, engine='openpyxl')
    except Exception as e:
        raise ValueError(f"File parsing failed: {e}")

    # 2. Admin-Proofing: Normalize headers
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    # Check if required columns actually exist before dropping NaNs
    required = ['user_input', 'assistant_output']
    if not all(col in df.columns for col in required):
        missing = [col for col in required if col not in df.columns]
        raise ValueError(f"Missing required columns: {missing}")

    # 3. Cleanup
    df = df.dropna(subset=['user_input', 'assistant_output'])
    df = df.fillna("")

    output = io.StringIO()

    # 4. Conversion Loop
    for _, row in df.iterrows():
        user_text = str(row['user_input']).strip()
        assistant_text = str(row['assistant_output']).strip()
        image_url = str(row.get('image_url', "")).strip()

        
        # 1. Start with System Message
        messages = [
            {"role": "system", "content": system_prompt}
        ]

        user_content = [{"type":"text", "text": user_text}]

        # 3. Add Image User Message (ONLY if image_url exists)
        if image_url:
            user_content.append({
              
                        "type": "image_url",
                        "image_url": {"url": image_url}
                
            })

        messages.append({
            "role":"user",
            "content":user_content
        })

        # 4. Add Assistant Response
        messages.append({
            "role": "assistant",
            "content": assistant_text
        })

        training_example = {"messages": messages}
        output.write(json.dumps(training_example) + '\n')

    output.seek(0)
    return output.getvalue()
