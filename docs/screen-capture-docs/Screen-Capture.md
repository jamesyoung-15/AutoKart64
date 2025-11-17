# Capturing Mario Kart 64 Screen with Python

TLDR: Use `python-mss` for most cases, on Linux Wayland use `Gstreamer + Pipewire`.

## Overview

For most operating systems and platforms, using `python-mss` should do the trick. The [doc](https://python-mss.readthedocs.io/) shows the usage, and it's supported by Windows, Mac, and Linux (X11).

For Linux setup with Wayland (my situation), `python-mss` doesn't work. The Wayland protocol blocks applications from directly accessing screen content for security, where applications must go through the XDG Desktop Portal. This means that screen capturing is less straight-forward than say X11, hence why some Python libraries like `mss` doesn't work.

Nevertheless, I found a solution thanks to this [code snippet](https://stackoverflow.com/questions/44104331/how-to-capture-screen-on-waylandgnome-in-python-code) which uses Gstreamer (see below).

## Wayland Python Recording Solutions

### Gstreamer

The Gstreamer library gives a good performant way to have screen capturing in Python. We use a few components:

- XDG Desktop Portal: Used to grant access to desktop features, we call ScreenCast for users to give permission to record certain screen/window
- D-Bus: Used to call XDG Desktop Portal
- Pipewire: Compositor streams raw video data of window/monitor via Pipewire
- Gstreamer: Connects to Pipewire stream, decodes video format, buffers frames

In Python, I use the libraries:

- [`dasbus`](https://github.com/dasbus-project/dasbus) (dbus library)
- [`PyGObject`](https://pygobject.gnome.org/) (bindings for GObject based libraries like Gstreamer)

My Python code basically follows this workflow:

1. Create DBus session to communicate with XDG Desktop Portal
2. Create a screen capture session through the ScreenCast portal interface
3. User receives a prompt to select window/screen to capture with Pipewire
4. After user selection, we get the node_id and file descriptor for where to read the raw video stream
5. Setup Gstreamer pipeline to read from the Pipewire source, decode the video, provide frames
6. Convert frames to Numpy array which can be used for downstream tasks

### UDP Stream

Another option is to use something like OBS to capture the application/window and stream it via UDP, then in our Python application we connect to the UDP stream. This removes the complicated setup and is also platform agnostic.

However, this introduces network latency and manual setup, where before each run we have to first run the game, have OBS capture the game screen, setup OBS to stream to source, setup UDP stream. Overall, this is a less preferred approach for me.

### Pillow ImageGrab

Technically, you can use Pillow's ImageGrab, which takes a screenshot of the screen, ie: `ImageGrab.grab(bbox=(0, 0, 600, 480))`. However, running this within a while loop for live screen capture gave me less than 2 FPS, where in the console it shows that it is constantly initializing the VAAPI hardware acceleration for each frame capture.

My guess is on Wayland, Pillow's ImageGrab automatically calls XDG Desktop Portal, initializes the Pipewire session, initializes VAAPI hardware encoder, gets a screen capture and encodes it, decodes it back to image, returns it to Python.

For a screenshot this is fine (which is what this was designed for). However, for a video stream, it will need to re-run this pipeline (eg. request new session, capture frame, tear down everything) each time, causing FPS to be pretty low.

## Resources

- [StackOverflow Example Python to Capture Wayland](https://stackoverflow.com/questions/44104331/how-to-capture-screen-on-waylandgnome-in-python-code)
- [Example Wayland Python Screen Capture Snippet](https://gitlab.gnome.org/-/snippets/19)
- [Wayland Damage Tracking (why screen record sometimes doesn't update)](https://emersion.fr/blog/2019/intro-to-damage-tracking/)
