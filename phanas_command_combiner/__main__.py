import argparse
from pathlib import Path
import re

from . import CommandCombiner, Vector3

# This lookahead thing using tmp is an emulation of an atomic group
command_pattern = re.compile(
    r'^(?=(?P<tmp>\s*))(?P=tmp)(?!#)\s*(?P<command>\S.*)$'
)


def main():
    parser = argparse.ArgumentParser(
        prog="python -m phanas_command_combiner",
        description="Generate commands for an armor stand clock with rotating "
                    "hands."
    )
    parser.add_argument(
        'commands_file', type=Path,
        help="File to read commands from"
    )
    parser.add_argument(
        'output_file', type=Path,
        help="File to write generated combined commands to"
    )
    parser.add_argument(
        '--run-once', required=False, action='store_true',
        help=(
            "Run the commands immediately from the command block minecarts, "
            "rather than writing the commands to command blocks"
        )
    )
    parser.add_argument(
        '--no-support-blocks', required=False, action='store_true',
        help=(
            "Don't generate support blocks for the minecarts (stone, redstone "
            "block, activator rail). Use this if you already will have these "
            "blocks set up above the command block."
        )
    )

    args = parser.parse_args()
    commands_file: Path = args.commands_file
    output_file: Path = args.output_file
    run_once: bool = args.run_once
    support_blocks: bool = not args.no_support_blocks

    if not commands_file.exists():
        return

    cmds = []
    with commands_file.open() as f:
        for line in f.readlines():
            match = command_pattern.match(line)
            if match:
                cmds.append(match['command'])

    combiner = CommandCombiner(
        cmds, Vector3(8, -1, 8), run_once=run_once,
        support_blocks=support_blocks
    )
    with output_file.open('wt') as f:
        for combined in combiner.combine():
            f.write(combined)
            f.write('\n')


if __name__ == '__main__':
    main()
