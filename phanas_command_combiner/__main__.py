from pathlib import Path
import re
import sys

from . import CommandCombiner, Vector3

# This lookahead thing using tmp is an emulation of an atomic group
command_pattern = re.compile(
    r'^(?=(?P<tmp>\s*))(?P=tmp)(?!#)\s*(?P<command>\S.*)$'
)


def main():
    if len(sys.argv) != 3:
        return

    commands_file = Path(sys.argv[1])
    out_file = Path(sys.argv[2])
    if not commands_file.exists():
        return

    cmds = []
    with commands_file.open() as f:
        for line in f.readlines():
            match = command_pattern.match(line)
            if match:
                cmds.append(match['command'])

    combiner = CommandCombiner(cmds, Vector3(8, -1, 8))
    with out_file.open('wt') as f:
        for combined in combiner.combine():
            f.write(combined)
            f.write('\n')


if __name__ == '__main__':
    main()
