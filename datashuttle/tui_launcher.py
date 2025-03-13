import argparse
from datashuttle.tui.app import main as tui_main

# -------------------------------------------------------------------------
# Entry Point to the CLI
# -------------------------------------------------------------------------

description = (
    "-----------------------------------------------------------------------\n"
    "Use `datashuttle launch` to start datashuttle.\n"
    "-----------------------------------------------------------------------\n"
)

def create_parser() -> argparse.ArgumentParser:
    """
    Creates and returns the argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="datashuttle",
        usage="%(prog)s launch",
        description=description,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    # We are only interested in the "launch" command
    parser.add_argument("command", choices=["launch"], help="Command to execute")
    return parser

# -------------------------------------------------------------------------
# Main Run Function
# -------------------------------------------------------------------------

def main() -> None:
    """
    Launch the datashuttle TUI based on the user's command.
    """
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "launch":
        tui_main()  # Call the TUI main function when 'launch' is provided
    else:
        # This block will never be executed due to the `choices` argument above
        parser.print_help()

if __name__ == "__main__":
    main()

