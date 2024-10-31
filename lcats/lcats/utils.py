"""Utility functions for the LCATS package."""

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
        raise ValueError(f"Text limit {limit} not long enough for prefix/suffix spacer '{spacer}'.")
    suffix = limit - prefix - len(spacer)
    return text[:prefix] + spacer + text[-suffix:]
