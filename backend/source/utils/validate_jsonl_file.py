import json
from urllib.parse import urlparse
from typing import List, Dict, Any


ALLOWED_ROLES = {"system", "user", "assistant"}
ALLOWED_CONTENT_TYPES = {"text", "image_url"}

MAX_MESSAGES_PER_SAMPLE = 10
MAX_CHARS_PER_MESSAGE = 10000  # conservative safety
MAX_TOTAL_CHARS_PER_SAMPLE = 20000


class DatasetValidationError(Exception):
    pass


def is_valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False

def validate_finetuning_jsonl(
    jsonl_str: str,
    strict: bool = True
):
    """
    Validates a JSONL dataset for OpenAI fine-tuning.
    Raises DatasetValidationError on failure.
    """

    lines = [l for l in jsonl_str.splitlines() if l.strip()]

    if not lines:
        raise DatasetValidationError("Dataset is empty")

    for i, line in enumerate(lines, start=1):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            raise DatasetValidationError(
                f"Line {i}: Invalid JSON ({e})"
            )

        if "messages" not in obj:
            raise DatasetValidationError(
                f"Line {i}: Missing 'messages' field"
            )

        if not isinstance(obj["messages"], list):
            raise DatasetValidationError(
                f"Line {i}: 'messages' must be an array"
            )

        validate_messages(obj["messages"], i)

    return {
        "status": "ok",
        "samples": len(lines)
    }

def validate_messages(messages: List[Dict[str, Any]], line_no: int):
    if not messages:
        raise DatasetValidationError(
            f"Line {line_no}: Messages array cannot be empty"
        )

    if len(messages) > MAX_MESSAGES_PER_SAMPLE:
        raise DatasetValidationError(
            f"Line {line_no}: Too many messages in one sample"
        )

    total_chars = 0
    has_assistant = False
    has_user = False

    for idx, msg in enumerate(messages):
        if not isinstance(msg, dict):
            raise DatasetValidationError(
                f"Line {line_no}: Each message must be an object"
            )

        role = msg.get("role")
        content = msg.get("content")
        image_count = 0

   
        if msg["role"] == "user" and isinstance(msg["content"], list):
            for block in msg["content"]:
                if block["type"] == "image_url":
                    image_count += 1
    
        if image_count > 10:
            raise DatasetValidationError(
                f"Line {line_no}: Too many images ({image_count}), max is 10"
            )


        if role not in ALLOWED_ROLES:
            raise DatasetValidationError(
                f"Line {line_no}: Invalid role '{role}'"
            )

        if role == "assistant":
            has_assistant = True
        if role == "user":
            has_user = True

        validate_message_content(content, line_no)

        if isinstance(content, str):
            total_chars += len(content)
        elif isinstance(content, list):
            for block in content:
                if block["type"] == "text":
                    total_chars += len(block["text"])

    if not has_user:
        raise DatasetValidationError(
            f"Line {line_no}: At least one user message is required"
        )

    if not has_assistant:
        raise DatasetValidationError(
            f"Line {line_no}: At least one assistant message is required"
        )

    if total_chars > MAX_TOTAL_CHARS_PER_SAMPLE:
        raise DatasetValidationError(
            f"Line {line_no}: Sample is too large overall"
        )



def validate_message_content(content: Any, line_no: int):
    """
    Validates a single message's content field.
    """
    if isinstance(content, str):
        if not content.strip():
            raise DatasetValidationError(
                f"Line {line_no}: Empty string content is not allowed"
            )
        if len(content) > MAX_CHARS_PER_MESSAGE:
            raise DatasetValidationError(
                f"Line {line_no}: Message content too long"
            )
        return
    

    if isinstance(content, list):
        if not content:
            raise DatasetValidationError(
                f"Line {line_no}: Content list cannot be empty"
            )

        for block in content:
            if not isinstance(block, dict):
                raise DatasetValidationError(
                    f"Line {line_no}: Content blocks must be objects"
                )

            block_type = block.get("type")
            if block_type not in ALLOWED_CONTENT_TYPES:
                raise DatasetValidationError(
                    f"Line {line_no}: Invalid content type '{block_type}'"
                )

            if block_type == "text":
                text = block.get("text", "")
                if not isinstance(text, str) or not text.strip():
                    raise DatasetValidationError(
                        f"Line {line_no}: Text block must contain non-empty text"
                    )

            if block_type == "image_url":
                url = block.get("image_url", {}).get("url")
                if not url or not is_valid_url(url):
                    raise DatasetValidationError(
                        f"Line {line_no}: Invalid image_url"
                    )

        return

    raise DatasetValidationError(
        f"Line {line_no}: Content must be string or list"
    )

