# AutoKart64

Ongoing project to use machine learning to play Mario Kart 64. Uses Mupen64plus emulator.

## Setup

### Building Mupen64Plus

- Install dependencies for building Mupen64Plus, then run:

``` bash
cd mupen64plus
chmod +x build.sh
./build.sh
```

See [full setup instructions](./mupen64plus/README.md).

### Dev Setup

- Example:

``` bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- Or on NixOS:

``` bash
nix-shell
```
