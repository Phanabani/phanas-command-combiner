from collections.abc import Generator

from typing import NoReturn, Optional

from .nbt_encoder import NBTEncoder
from .snakey import Snakey
from .vector import Vector3

COMMAND_BLOCK_TEXT_LIMIT = 32500


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
        if len(entities) < 2:
            # Nothing to stack
            return

        for i in range(len(entities) - 1):
            entities[i]['Passengers'] = [entities[i + 1]]

    @staticmethod
    def slice_by_length(
            tags: list[dict], encoder: NBTEncoder, init_len: int = 0,
            post_commands: Optional[list[dict]] = None
    ) -> Generator[int]:
        tags = list(tags)  # make copy
        if post_commands is not None:
            init_len += len(encoder.encode(post_commands))

        while tags:
            window_addend = len(tags)
            window = window_addend
            best_window = 0
            while window_addend > 0 and window <= len(tags):
                # This algorithm is inspired by binary search
                # It basically finds the largest window over tags which
                # starts at 0 and contains the longest encoded NBT string
                # which is less than the command block character limit
                encoded_len = len(encoder.encode(tags[:window]))

                window_addend //= 2
                if encoded_len + init_len <= COMMAND_BLOCK_TEXT_LIMIT:
                    best_window = window
                    window += window_addend
                else:
                    window -= window_addend

            yield [*tags[:best_window], *post_commands]
            # Remove this slice and continue slicing if anything is left
            del tags[:best_window]


class CommandCombiner:

    origin = Vector3(1, -3, 1)

    def __init__(
            self, commands: list[str], dimensions: Optional[Vector3] = None,
            run_once: bool = False, support_blocks: bool = True
    ):
        """
        Combine Minecraft commands into fewer long commands. This uses stacked
        command block minecarts to generate a region of chain command blocks
        with `commands` inside them. Use `run_once` to skip chain command block
        generation and run `commands` straight from the minecarts.

        :param commands: a list of commands to combine
        :param dimensions: the dimensions of the output command blocks. Set Y
            to -1 to automatically set the height based on the number of
            commands
        :param run_once: if true, don't create and command blocks and instead
            run the commands straight from the command block minecarts
        :param support_blocks: generate support blocks (stone, redstone block,
            activator rail) under the minecarts. Set to false if you already
            have these blocks set up.
        """
        self.commands = commands
        self.nbt_encoder = NBTEncoder(quote_strings=False)
        if dimensions is None:
            dimensions = Vector3(8, -1, 8)
        self.dimensions = dimensions
        self.run_once = run_once
        self.support_blocks = support_blocks

    def combine(self) -> Generator[str]:
        if not self.commands:
            return

        if self.support_blocks:
            summon_offset = 1
        else:
            summon_offset = 3
        summon_cmd = f'summon falling_block ~ ~{summon_offset} ~ '

        support_blocks = self.get_support_blocks()
        NBTUtils.stack(support_blocks)

        support_blocks[-1]['Passengers'] = []
        init_len = (
                # Skip length of the empty brackets
                len(summon_cmd) + len(self.nbt_encoder.encode(support_blocks[0])) - 2
        )

        place_cmd_blocks = self.place_command_blocks()
        main_commands = self.format_commands()
        cleanup_cmds = self.cleanup_commands()
        commands = [
            *place_cmd_blocks, *main_commands
        ]
        commands_minecarts = [NBTUtils.cmd_minecart(repr(cmd)) for cmd in commands]
        cleanup_minecarts = [NBTUtils.cmd_minecart(repr(cmd)) for cmd in cleanup_cmds]

        for minecarts_slice in (
                NBTUtils.slice_by_length(
                    commands_minecarts, self.nbt_encoder, init_len,
                    post_commands=cleanup_minecarts
                )
        ):
            support_blocks[-1]['Passengers'] = minecarts_slice
            tag = self.nbt_encoder.encode(support_blocks[0])
            yield f"{summon_cmd}{tag}"

    def get_support_blocks(self):
        if not self.support_blocks:
            return [NBTUtils.falling_block('fire', with_id=False)]

        # This is soooo weird right? The old method of just stacking the blocks
        # directly on top of each other doesn't seem to work anymore in 1.17.
        # I found through lots of experimentation that this sequence works.
        # You need buffer blocks between the actual blocks, because these will
        # break instead of placing down.
        #
        # It gets even weirder after the redstone block. I found that you have
        # to buffer the buffer block with a DIFFERENT buffer block. I tried
        # lots of combinations and this was the only thing that's actually
        # worked.
        #
        # Also FYI I used fire/soul fire here because they don't have an
        # item type associated with them, so them don't drop an item unlike most
        # other blocks I tried using as buffers (nether/end portals also work).
        # I also have to kill a falling block at the end because one of the
        # fires apparently DOES place after the other commands run and the
        # setup is deleted. I know it looks insane... but also kind of
        # captivating visually!!
        return [
            NBTUtils.falling_block('stone', with_id=False),
            NBTUtils.falling_block('fire'),
            NBTUtils.falling_block('fire'),
            NBTUtils.falling_block('redstone_block'),
            NBTUtils.falling_block('fire'),
            NBTUtils.falling_block('soul_fire'),
            NBTUtils.falling_block('fire'),
            NBTUtils.falling_block('fire'),
            NBTUtils.falling_block('activator_rail'),
        ]

    def place_command_blocks(self) -> list[str]:
        if self.run_once:
            return []

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
        if self.run_once:
            return self.commands

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

    def cleanup_commands(self) -> list[str]:
        cmds = [
            'data modify block ~ ~-3 ~ Command set value ""'
        ]
        if self.support_blocks:
            cmds.extend([
                'setblock ~ ~-2 ~ command_block{auto:1b,Command:"fill ~ ~ ~ ~ ~2 ~ air"}',
                'kill @e[type=falling_block,distance=..1]',
            ])
        cmds.append('kill @e[type=command_block_minecart,distance=..1]')
        return cmds
