from collections.abc import Generator
import re

from typing import NoReturn, Optional

from nbt_encoder import NBTEncoder

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

    def __init__(self, commands: list[str]):
        self.commands = commands
        self.nbt_encoder = NBTEncoder(quote_strings=False)

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

        commands = ['fill ~1 ~-3 ~1 ~2 ~-3 ~2 quartz_block']
        commands.append('kill @e[type=command_block_minecart,distance=..2]')
        minecarts = [NBTUtils.cmd_minecart(repr(cmd)) for cmd in commands]

        for minecarts_slice in (
                NBTUtils.slice_by_length(minecarts, self.nbt_encoder, init_len)
        ):
            falling_blocks[-1]['Passengers'] = minecarts_slice
            tag = self.nbt_encoder.encode(falling_blocks[0])
            yield f"{summon_cmd}{tag}"


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