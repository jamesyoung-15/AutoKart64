{ pkgs ? import <nixpkgs> {} }:

let
  pythonEnv = pkgs.python312.withPackages (ps: [ 
    # PyTorch with ROCm support
    ps.torchWithRocm
    (ps.torchvision.override { torch = ps.torchWithRocm; })
    (ps.torchaudio.override { torch = ps.torchWithRocm; })
    
    # common ml/data science packages
    ps.scipy
    ps.scikit-learn
    ps.scikit-image
    ps.pandas
    ps.matplotlib
    ps.ipykernel
    ps.jupyterlab
    (ps.opencv4.override { enableGtk2 = true; })

    ps.gymnasium
    ps.pygame
    (ps.stable-baselines3.override {torch = ps.torchWithRocm;})

    ps.python-dotenv
    ps.pytest

    ps.mss

    ps.pygobject3
    ps.gst-python
    ps.dbus-python
    ps.dasbus
    ps.evdev

    ps.ruff
  ]);

in
pkgs.mkShell {
  nativeBuildInputs = with pkgs; [
    gcc
    lldb
    gdb
    cmake
    ninja
    meson
    pkg-config
    ccache
    gnumake
    git
  ];

  buildInputs = with pkgs; [
    # Python environment with PyTorch
    pythonEnv
    rocmPackages.clr

    # libraries for building Mupen64Plus
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
    pkgs.pre-commit

    # Libraries needed for PyTorch
    libz
    stdenv.cc.cc.lib
    libGL
    glib
    libglvnd

    # gstreamer
    pkgs.gst_all_1.gstreamer
    pkgs.gst_all_1.gst-plugins-base
    pkgs.gst_all_1.gst-plugins-good
    pkgs.gst_all_1.gst-plugins-bad
    pkgs.gst_all_1.gst-plugins-ugly
    pkgs.gst_all_1.gst-plugins-base
    pkgs.gst_all_1.gst-libav
    pkgs.gobject-introspection
    pkgs.pipewire
    pkgs.cacert
    pkgs.glib-networking

    pkgs.ydotool
    pkgs.libinput
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
      pkgs.zlib
    ]}"
    alias python="python3.12"
    export GIO_EXTRA_MODULES="${pkgs.glib-networking}/lib/gio/modules"

    # Start ydotoold if not already running
    if ! pgrep -x ydotoold >/dev/null 2>&1; then
      echo "Starting ydotoold..."
      ydotoold --socket /tmp/ydotool_socket &
      disown
    else
      echo "ydotoold already running."
    fi
  '';
}
