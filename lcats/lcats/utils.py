"""Utility functions for the LCATS package."""

import json
import re
import textwrap


def pprint(text, width=80):
    """Pretty-print text with a given line width."""
    print()
    paragraphs = text.split('\n\n')
    for paragraph in paragraphs:
        print(textwrap.fill(paragraph, width=width))
        print()


def sm(text, limit=80, spacer='...'):
    """Show prefix and suffix of text if it is longer than the limit."""
    if len(text) <= limit:
        return text
    prefix = (limit - len(spacer)) // 2
    if prefix <= 0:
        raise ValueError(
            f"Text limit {limit} not long enough for prefix/suffix spacer '{spacer}'.")
    suffix = limit - prefix - len(spacer)
    return text[:prefix] + spacer + text[-suffix:]


def extract_fenced_code_blocks(text):
    """
    Finds any ```something ... ``` blocks and returns a list of tuples:
      (language, code_string)
    The `language` might be 'json', 'python', etc. or '' if unspecified.
    """
    # Regex explanation:
    #   ```     matches three backticks
    #   (\w+)?  optionally captures a word (the language name)
    #   [^\n]*  then zero or more non-newline characters until a newline
    #   (.*?)   lazily captures all content (including newlines) up to...
    #   ```     the closing three backticks
    pattern = r'```(\w+)?[^\n]*\n(.*?)```'
    matches = re.findall(pattern, text, flags=re.DOTALL)
    return matches


def extract_json(json_string: str, allow_multiple: bool = False) -> dict:
    """
    Extract JSON from a string that may contain additional text.
    """
    try:
        # Attempt to parse the JSON
        return json.loads(json_string)
    except json.JSONDecodeError as exc:
        code_blocks = extract_fenced_code_blocks(json_string)
        if not code_blocks:
            raise ValueError("No JSON found in the string.") from exc
        if len(code_blocks) > 1 and not allow_multiple:
            raise ValueError(
                "Multiple JSON blocks found, but allow_multiple is False.") from exc
        fmt, content = code_blocks[0]
        if fmt != "json":
            raise ValueError(f"Expected JSON format, but got: {fmt}") from exc
        return json.loads(content)
