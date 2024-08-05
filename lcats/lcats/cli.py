"""Command-line interface for the Literary Captain's Advisory Tool System (LCATS)."""

import sys

import lcats.gatherers.main

USAGE_MESSAGE = """Usage: lcats <command> [<args>]
Commands:   
    info      Describes LCATS, the literary captain's advisory tool system.
    gather    Gathers corpus data to a local database.
    index     Preprocesses a corpus to answer questions.
    advise    LCATS command-line advising tool.
    eval      Evaluate LCATS on a benchmark suite.
"""

def usage():
    """Prints the usage message for the LCATS command-line interface.""" 
    return USAGE_MESSAGE


def dispatch(command, args):
    """Dispatches the command to the appropriate function.
    
    Args:
        command: The command to execute.
        args: A list of additional arguments to the command.
    Returns:
        A tuple containing the output of the command and an exit status.
    """
    del args  # Unused currently
    if command == 'info':
        return "LCATS is a literary case based reasoning system.", 0

    elif command == 'gather':
        return lcats.gatherers.main.main()

    elif command == 'index':
        return "Indexing data files is not yet implemented.", 1

    elif command == 'advise':
        return "Getting advice from LCATS is not yet implemented.", 1

    elif command == 'eval':
        return "Evaluating LCATS is not yet implemented.", 1

    else:
        return f"Unknown command: {command}", 1


def main():
    """Main entry point for the LCATS command-line interface."""
    if len(sys.argv) < 2:
        print(usage())
        sys.exit(1)
    result, status = dispatch(sys.argv[1], sys.argv[2:])
    print(result)
    sys.exit(status)


if __name__ == "__main__":
    main()
