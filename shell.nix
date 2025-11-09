{ pkgs ? import <nixpkgs> {} }:

let
  pythonEnv = pkgs.python312.withPackages (ps: [ 
    ps.torchWithRocm
    (ps.torchvision.override { torch = ps.torchWithRocm; })
    (ps.torchaudio.override { torch = ps.torchWithRocm; })
    ps.scipy
    ps.scikit-learn
    ps.scikit-image
    ps.pandas
    ps.matplotlib
    ps.gymnasium
    ps.stable-baselines3.override {torch = ps.torchWithRocm;}
  ]);

in
pkgs.mkShell {
  nativeBuildInputs = with pkgs; [
    # Compilers and toolchains
    gcc
    lldb
    gdb

    # Build systems and package managers
    cmake
    ninja
    meson
    pkg-config

    # Project helpers
    ccache
    gnumake
    git
  ];

  buildInputs = with pkgs; [
    # Python environment with PyTorch
    pythonEnv
    rocmPackages.clr

    # C++ Libraries
    boost
    elfutils
    ncurses
    openssl
    zlib
    glm
    SDL2
    SDL2_gfx
    libpng
    freetype
    libGLU
    libsamplerate
    speexdsp
    glfw
    glm
    vulkan-headers
    vulkan-loader
    vulkan-tools
    nasm
    mesa
    bintools-unwrapped # resolve dis-asm

    # Libraries needed for PyTorch
    libz
    stdenv.cc.cc.lib
    libGL
    glib
    libglvnd
  ];

  shellHook = ''
    export CFLAGS="-O3 -march=native -msse2 -DXXH_NO_FORCE_INLINE=1"
    export CXXFLAGS="$CFLAGS"
    export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [
      pkgs.libz
      pkgs.stdenv.cc.cc.lib
      pkgs.libGL
      pkgs.glib
      pkgs.libglvnd
    ]}"
    alias python="python3.12"
  '';
}