# Mupen64Plus Setup

We need to compile Mupen64Plus from source code since the binaries don't include the option to turn on debugger mode to read from game memory.

It is based on the instructions from Mupen64Plus' [documentation](mupen64plus.org/wiki/index.php?title=CompilingFromGit).

## Setup Instructions

### Requirements

See Mupen64Plus' [documentation](mupen64plus.org/wiki/index.php?title=CompilingFromGit), install the required and optional dependencies. Also install `binutils-dev` if you run into no `dis-asm.h` issue.

### Building Project

The `build.sh` script grabs the source code (core + plugins) into `source` directory and builds the project into `build`. Using their provided scripts (see `build_scripts`).

``` bash
chmod +x build.sh
./build.sh
```
