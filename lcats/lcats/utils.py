"""Utility functions for the LCATS package."""

import textwrap

def pprint(text, width=80):
    """Pretty-print text with a given line width."""
    print()
    paragraphs = text.split('\n\n')
    for paragraph in paragraphs:
        print(textwrap.fill(paragraph, width=width))
        print()
