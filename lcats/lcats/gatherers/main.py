"""Runs the extractors we have."""

import lcats.gatherers.sherlock.gutenberg as sherlock

def run(dry_run=False):
    if not dry_run:
        print("Gathering data from the corpus.")
        print(sherlock.gather())
    return "Gathering complete.", 0


if __name__ == '__main__':
    run()
