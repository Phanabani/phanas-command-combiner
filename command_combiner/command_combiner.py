from collections.abc import Generator
import re

from typing import NoReturn, Optional

from .nbt_encoder import NBTEncoder
from .snakey import Snakey
from .vector import Vector3

COMMAND_BLOCK_TEXT_LIMIT = 32500
# This lookahead thing using tmp is an emulation of an atomic group
command_pattern = re.compile(
    r'^(?=(?P<tmp>\s*))(?P=tmp)(?!#)\s*(?P<command>\S.*)$'
)


class NBTUtils:

    @staticmethod
    def falling_block(
            block: Optional[str] = None, time: Optional[int] = 1,
            with_id=True
    ) -> dict:
        tag = {
            'id': 'falling_block', 'Time': time, 'BlockState': {'Name': block}
        }
        if not with_id:
            del tag['id']
        if block is None:
            del tag['BlockState']
        if time is None:
            del tag['Time']
        return tag

    @staticmethod
    def cmd_minecart(command: str) -> dict:
        return {'id': 'command_block_minecart', 'Command': command}

    @staticmethod
    def stack(entities: list[dict]) -> NoReturn:
        for i in range(len(entities) - 1):
            entities[i]['Passengers'] = [entities[i + 1]]

    @staticmethod
    def slice_by_length(
            tags: list, encoder: NBTEncoder, init_len: int = 0
    ) -> Generator[int]:
        tags = list(tags)  # make copy
        while tags:
            window_addend = len(tags)
            window = window_addend
            slice_ = slice(window)
            while window_addend > 0 and window <= len(tags):
                # This algorithm is inspired by binary search
                # It basically finds the largest window over tags which
                # starts at 0 and contains the longest encoded NBT string
                # which is less than the command block character limit
                slice_ = slice(window)
                encoded_len = len(encoder.encode(tags[slice_]))

                window_addend //= 2
                if encoded_len + init_len <= COMMAND_BLOCK_TEXT_LIMIT:
                    window += window_addend
                else:
                    window -= window_addend

            yield tags[slice_]
            # Remove this slice and continue slicing if anything is left
            del tags[slice_]


class CommandCombiner:

    origin = Vector3(1, -3, 1)

    def __init__(
            self, commands: list[str], dimensions: Optional[Vector3] = None
    ):
        self.commands = commands
        self.nbt_encoder = NBTEncoder(quote_strings=False)
        if dimensions is None:
            dimensions = Vector3(8, -1, 8)
        self.dimensions = dimensions

    def combine(self) -> Generator[str]:
        summon_cmd = 'summon falling_block ~ ~1 ~ '

        falling_blocks = [
            NBTUtils.falling_block('stone', with_id=False),
            NBTUtils.falling_block('fire'),
            NBTUtils.falling_block('fire'),
            NBTUtils.falling_block('redstone_block'),
            NBTUtils.falling_block('fire'),
            NBTUtils.falling_block('nether_portal'),
            NBTUtils.falling_block('fire'),
            NBTUtils.falling_block('fire'),
            NBTUtils.falling_block('activator_rail'),
        ]
        NBTUtils.stack(falling_blocks)

        falling_blocks[-1]['Passengers'] = []
        init_len = (
                # Skip length of the empty brackets
                len(summon_cmd) + len(self.nbt_encoder.encode(falling_blocks[0])) - 2
        )

        commands = self.place_command_blocks()
        commands.extend(self.format_commands())
        commands.append('setblock ~ ~-2 ~ command_block{auto:1b,Command:"fill ~ ~ ~ ~ ~2 ~ air"}')
        commands.append('kill @e[type=falling_block,distance=..1]')
        commands.append('kill @e[type=command_block_minecart,distance=..1]')
        minecarts = [NBTUtils.cmd_minecart(repr(cmd)) for cmd in commands]

        for minecarts_slice in (
                NBTUtils.slice_by_length(minecarts, self.nbt_encoder, init_len)
        ):
            falling_blocks[-1]['Passengers'] = minecarts_slice
            tag = self.nbt_encoder.encode(falling_blocks[0])
            yield f"{summon_cmd}{tag}"

    def place_command_blocks(self) -> list[str]:
        commands = []
        snakey = Snakey(self.dimensions, len(self.commands))
        # We leave the y axis unbounded and Snakey calculates it
        dims = snakey.dimensions
        offset_dims = self.origin + dims
        block = "chain_command_block[facing=%s]{auto:1b,TrackOutput:0b}"

        facing_x = 1
        facing_z = 1
        row_end_pos = None
        # Place layers of command blocks
        for y in range(int(dims.y)):
            if facing_z == 1:
                z_range = range(int(dims.z))
            else:
                z_range = range(int(dims.z) - 1, -1, -1)

            pos = None
            # Place rows on the x axis with alternating directions
            for z in z_range:
                pos = self.origin + Vector3(0, y, z)
                if facing_x == 1:
                    row_end_pos = int(offset_dims.x) - 1
                else:
                    row_end_pos = self.origin.x

                # Place row
                commands.append(
                    f"fill "
                    f"~{pos.x:.0f} ~{pos.y:.0f} ~{pos.z:.0f} "
                    f"~{dims.x:.0f} ~{pos.y:.0f} ~{pos.z:.0f} "
                    f"{block % ('east' if facing_x==1 else 'west')}"
                )
                # Replace row end block which turns to the new row
                commands.append(
                    f"setblock "
                    f"~{row_end_pos} ~{pos.y:.0f} ~{pos.z:.0f} "
                    f"{block % ('south' if facing_z==1 else 'north')}"
                )

                facing_x *= -1

            # Replace the last row's end block with one that points up to the
            # next layer
            commands[-1] = (
                f"setblock "
                f"~{row_end_pos} ~{pos.y:.0f} ~{pos.z:.0f} "
                f"{block % 'up'}"
            )

            facing_z *= -1

        return commands

    def format_commands(self) -> list[str]:
        snakey = Snakey(self.dimensions, len(self.commands))
        commands = []
        for pos_and_facing, cmd in zip(snakey, self.commands):
            pos, _ = pos_and_facing
            pos += self.origin
            commands.append(
                f"data modify block "
                f"~{pos.x:.0f} ~{pos.y:.0f} ~{pos.z:.0f} "
                f"Command set value {cmd!r}"
            )
        return commands


if __name__ == '__main__':
    from pathlib import Path
    import sys

    def main():
        if len(sys.argv) != 2:
            return

        file = Path(sys.argv[1])
        if not file.exists():
            return

        cmds = []
        with file.open() as f:
            for line in f.readlines():
                match = command_pattern.match(line)
                if match:
                    cmds.append(match['command'])

        combiner = CommandCombiner(cmds)
        for combined in combiner.combine():
            print(combined, end='\n\n')

    main()
