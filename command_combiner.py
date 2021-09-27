from abc import ABCMeta, abstractmethod
from collections.abc import Generator
import re

# This lookahead thing using tmp is an emulation of an atomic group
from typing import NoReturn, Optional

COMMAND_BLOCK_TEXT_LIMIT = 32500
command_pattern = re.compile(
    r'^(?=(?P<tmp>\s*))(?P=tmp)(?!#)\s*(?P<command>\S.*)$'
)

r'summon falling_block ~ ~5 ~ {BlockState:{Name:stone},Time:1b,'
r'Passengers:[{id:\"minecraft:falling_block\",Time:0,'
r'Passengers:[{id:\"minecraft:falling_block\",Time:1b,BlockState:{Name:redstone_block},'
r'Passengers:[{id:\"minecraft:falling_block\",Time:0,'
r'Passengers:[{id:\"minecraft:falling_block\",BlockState:{Name:activator_rail},Time:1b,'
r'Passengers:[{id:command_block_minecart, Command:}]'


class NBTNode(metaclass=ABCMeta):

    @abstractmethod
    def encode(self) -> str:
        pass


class RawNBT(NBTNode):

    def __init__(self, text: str):
        self.text = text

    def encode(self):
        return self.text


class NBTEncoder:

    def __init__(self, quote_strings: bool = True):
        self.quote_strings = quote_strings

    def encode(self, obj):
        if isinstance(obj, NBTNode):
            return obj.encode()

        if isinstance(obj, dict):
            return self.encode_dict(obj)

        if isinstance(obj, list):
            return self.encode_list(obj)

        if isinstance(obj, str):
            return self.encode_str(obj)

        if isinstance(obj, float):
            return self.encode_float(obj)

        if isinstance(obj, bool):
            # bools are also ints, so do this before ints
            return self.encode_bool(obj)

        if isinstance(obj, int) and not isinstance(obj, bool):
            return self.encode_int(obj)

        if obj is None:
            return self.encode_none()

        raise ValueError(
            f"Failed to match type of {obj} ({type(obj)}) to any NBT type"
        )

    def encode_dict(self, obj: dict) -> str:
        items = ['{']
        for k, v in obj.items():
            items.extend([k, ':', self.encode(v), ','])
        items[-1] = '}'
        return ''.join(items)

    def encode_list(self, obj: list) -> str:
        items = ['[']
        for i in obj:
            items.extend([self.encode(i), ','])
        items[-1] = ']'
        return ''.join(items)

    def encode_str(self, obj: str) -> str:
        if self.quote_strings:
            return repr(obj)
        return obj

    def encode_float(self, obj: float) -> str:
        return f'{obj:.6}'

    def encode_int(self, obj: int) -> str:
        return str(obj)

    def encode_bool(self, obj: bool) -> str:
        return str(obj).lower()

    def encode_none(self) -> str:
        return 'null'


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

    parent = Path(__file__).parent

    cmds = []
    with open(parent / 'commands.txt', 'rt') as f:
        for line in f.readlines():
            match = command_pattern.match(line)
            if match:
                cmds.append(match['command'])

    combiner = CommandCombiner(cmds)
    for combined in combiner.combine():
        print(combined, end='\n\n')
