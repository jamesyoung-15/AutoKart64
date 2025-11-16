import re

import numpy as np
from dasbus.connection import SessionMessageBus
from dasbus.typing import get_variant

import gi

gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("Gst", "1.0")
from gi.repository import GLib, Gst, Gio  # type: ignore

Gst.init(None)


class WaylandScreenCapture:
    def __init__(self):
        self.loop = GLib.MainLoop()
        self.bus = SessionMessageBus()
        self.request_iface = "org.freedesktop.portal.Request"
        self.screen_cast_iface = "org.freedesktop.portal.ScreenCast"

        self.request_token_counter = 0
        self.session_token_counter = 0

        if self.bus.connection is None:
            raise Exception("Failed to connect to D-Bus session bus")
        self.sender_name = re.sub(
            r"\.", r"_", self.bus.connection.get_unique_name()[1:]
        )

        self.session = None
        self.pipeline = None
        self.node_id = None
        self.fd = None

        self.portal = self.bus.get_proxy(
            "org.freedesktop.portal.Desktop",
            "/org/freedesktop/portal/desktop",
            self.screen_cast_iface,
        )

        # For OpenCV frame capture
        self.latest_frame = None
        self.frame_ready = False

    def new_request_path(self):
        self.request_token_counter += 1
        token = "u%d" % self.request_token_counter
        path = "/org/freedesktop/portal/desktop/request/%s/%s" % (
            self.sender_name,
            token,
        )
        return (path, token)

    def new_session_path(self):
        self.session_token_counter += 1
        token = "u%d" % self.session_token_counter
        path = "/org/freedesktop/portal/desktop/session/%s/%s" % (
            self.sender_name,
            token,
        )
        return (path, token)

    def screen_cast_call(self, method, callback, *args, options=None):
        if self.bus.connection is None:
            raise Exception("D-Bus connection is not available")

        if options is None:
            options = {}

        (request_path, request_token) = self.new_request_path()

        self.bus.connection.signal_subscribe(
            "org.freedesktop.portal.Desktop",
            self.request_iface,
            "Response",
            request_path,
            None,
            0,
            callback,
        )

        options["handle_token"] = get_variant("s", request_token)
        method(*(args + (options,)))

    def on_start_response(self, connection, sender, path, interface, signal, params):
        response = params[0]
        results = params[1]

        if response != 0:
            print(f"Failed to start: {response}")
            self.loop.quit()
            return

        print("Stream started successfully")
        for node_id, stream_properties in results["streams"]:
            print(f"Got stream node_id: {node_id}")
            self.node_id = node_id
            self.setup_pipewire_stream(node_id)
            break

    def on_select_sources_response(
        self, connection, sender, path, interface, signal, params
    ):
        response = params[0]
        results = params[1]

        if response != 0:
            print(f"Failed to select sources: {response}")
            self.loop.quit()
            return

        print("Sources selected")
        self.screen_cast_call(
            self.portal.Start, self.on_start_response, self.session, ""
        )

    def on_create_session_response(
        self, connection, sender, path, interface, signal, params
    ):
        response = params[0]
        results = params[1]

        if response != 0:
            print(f"Failed to create session: {response}")
            self.loop.quit()
            return

        self.session = results["session_handle"]
        print(f"Session created: {self.session}")

        self.screen_cast_call(
            self.portal.SelectSources,
            self.on_select_sources_response,
            self.session,
            options={
                "multiple": get_variant("b", False),
                "types": get_variant("u", 2),  # 1 = monitor, 2 = window
            },
        )

    def setup_pipewire_stream(self, node_id):
        """Setup GStreamer pipeline with appsink for OpenCV"""
        if self.bus.connection is None:
            raise Exception("D-Bus connection is not available")

        result = self.bus.connection.call_with_unix_fd_list_sync(
            "org.freedesktop.portal.Desktop",
            "/org/freedesktop/portal/desktop",
            self.screen_cast_iface,
            "OpenPipeWireRemote",
            GLib.Variant("(oa{sv})", (self.session, {})),
            GLib.VariantType("(h)"),
            Gio.DBusCallFlags.NONE,
            -1,
            None,
            None,
        )
        variant_result, fd_list = result  # type: ignore
        fd_index = variant_result.unpack()[0]
        self.fd = fd_list.get(fd_index)

        # Create pipeline with appsink for OpenCV integration
        pipeline_str = (
            f"pipewiresrc fd={self.fd} path={node_id} ! "
            "video/x-raw,format=BGRx ! "
            "videoconvert ! "
            "video/x-raw,format=BGR ! "
            "appsink name=sink emit-signals=true max-buffers=1 drop=true"
        )

        print(f"Creating pipeline: {pipeline_str}")
        self.pipeline = Gst.parse_launch(pipeline_str)

        # Get the appsink element
        appsink = self.pipeline.get_by_name("sink")
        appsink.connect("new-sample", self.on_new_sample)

        # Start playing
        self.pipeline.set_state(Gst.State.PLAYING)
        print("Pipeline started")

    def on_new_sample(self, sink):
        """Callback when new frame is available"""
        sample = sink.emit("pull-sample")
        if sample:
            buf = sample.get_buffer()
            caps = sample.get_caps()

            # Get frame dimensions
            structure = caps.get_structure(0)
            width = structure.get_value("width")
            height = structure.get_value("height")

            # Extract buffer data
            success, map_info = buf.map(Gst.MapFlags.READ)
            if success:
                # Convert to numpy array
                frame_data = np.ndarray(
                    shape=(height, width, 3), dtype=np.uint8, buffer=map_info.data
                )

                # Make a copy since the buffer will be unmapped
                self.latest_frame = frame_data.copy()
                self.frame_ready = True

                buf.unmap(map_info)

        return Gst.FlowReturn.OK

    def start_capture(self):
        """Start the screen capture session"""
        print("Starting screen capture session...")
        print("A dialog will appear - select your screen and click 'Share'")

        (session_path, session_token) = self.new_session_path()
        self.screen_cast_call(
            self.portal.CreateSession,
            self.on_create_session_response,
            options={"session_handle_token": get_variant("s", session_token)},
        )

        # Run the main loop in a separate thread or use timeout
        # For now, we'll iterate it manually
        context = GLib.MainContext.default()

        # Wait for pipeline to be ready (user selects screen)
        timeout = 0
        while self.pipeline is None and timeout < 300:  # 30 seconds timeout
            context.iteration(True)
            timeout += 1

        if self.pipeline is None:
            raise Exception("Failed to start capture - timeout or user cancelled")

        print("Capture started successfully!")

    def read_frame(self, return_latest_frame=False):
        """Read the latest frame (call this in your main loop)"""
        # Iterate GLib context to process new samples
        context = GLib.MainContext.default()
        context.iteration(False)

        if self.frame_ready:
            self.frame_ready = False
            return self.latest_frame
        if return_latest_frame:
            return self.latest_frame
        return None

    def stop(self):
        """Stop the capture"""
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
        if hasattr(self, "loop"):
            self.loop.quit()
