# Phana's Command Combiner (Minecraft 1.17)

[![release](https://img.shields.io/github/v/release/phanabani/phanas-command-combiner)](https://github.com/phanabani/phanas-command-combiner/releases)
[![license](https://img.shields.io/github/license/phanabani/phanas-command-combiner)](LICENSE)

Combine several Minecraft commands into one command. Inspired by 
[MrGarretto's Command Combiner](https://mrgarretto.com/cmdcombiner).

## Table of Contents

- [Install](#install)
- [Usage](#usage)
- [License](#license)

## Install

Clone the repo

```shell
git clone https://github.com/Phanabani/phanas-command-combiner.git
cd phanas-command-combiner
```

## Usage

### Combining

Run the module as a Python module.

```shell
python -m phanas_command_combiner <COMMANDS_FILE> <OUTPUT_FILE>
```

`COMMANDS_FILE` is a plaintext file with one command per line. mcfunction format
is properly handled (blank lines and #comments are ignored).

`OUTPUT_FILE` is where the combined commands will be written. If the combined
command is too long, it may be split into a few separate commands, one per line.

### Using in Minecraft

Place a command block and paste in one line at a time from `OUTPUT_FILE` into
the block. Trigger the command block, and new command blocks will be generated
in an 8×8 region diagonally adjacent to the command block you triggered in the
positive X and Z directions.

If the commands were too long for one combined command, multiple combined
commands will be generated, one per line in `OUTPUT_FILE`. Paste and run each
of these in the same command block to fill in all of your commands.

Depending on how many commands you have, the 8×8 region can expand indefinitely
vertically to accommodate them.

**⚠️ WARNING: Please be sure this region will not delete other important
blocks!! ⚠️**

## License

[MIT © Phanabani.](LICENSE)
