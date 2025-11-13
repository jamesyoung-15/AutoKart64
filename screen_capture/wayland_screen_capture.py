import re
import time

import cv2
import numpy as np
import dbus
from dbus.mainloop.glib import DBusGMainLoop

import gi
gi.require_version('GLib', '2.0')
gi.require_version('GObject', '2.0')
gi.require_version('Gst', '1.0')
from gi.repository import GLib, Gst # type: ignore

DBusGMainLoop(set_as_default=True)
Gst.init(None)


class WaylandScreenCapture:
    """ 
    Class to capture screen on Wayland using PipeWire and GStreamer,
    integrated with OpenCV for frame processing.
    """
    
    def __init__(self):
        """ Initialize the Wayland screen capture session. """
        self.loop = GLib.MainLoop()
        self.bus = dbus.SessionBus()
        self.request_iface = "org.freedesktop.portal.Request"
        self.screen_cast_iface = "org.freedesktop.portal.ScreenCast"
        
        self.request_token_counter = 0
        self.session_token_counter = 0
        self.sender_name = re.sub(r"\.", r"_", self.bus.get_unique_name()[1:])

        self.session = None
        self.pipeline = None
        self.node_id = None
        self.fd = None

        self.portal = self.bus.get_object(
            "org.freedesktop.portal.Desktop", "/org/freedesktop/portal/desktop"
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

    def screen_cast_call(self, method, callback, *args, options={}):
        (request_path, request_token) = self.new_request_path()
        self.bus.add_signal_receiver(
            callback,
            "Response",
            self.request_iface,
            "org.freedesktop.portal.Desktop",
            request_path,
        )
        options["handle_token"] = request_token
        method(*(args + (options,)), dbus_interface=self.screen_cast_iface)

    def on_start_response(self, response, results):
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

    def on_select_sources_response(self, response, results):
        if response != 0:
            print(f"Failed to select sources: {response}")
            self.loop.quit()
            return

        print("Sources selected")
        self.screen_cast_call(
            self.portal.Start, self.on_start_response, self.session, ""
        )

    def on_create_session_response(self, response, results):
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
                "multiple": False,
                "types": dbus.UInt32(2),  # 1 = monitor, 2 = window
            },
        )

    def setup_pipewire_stream(self, node_id):
        """Setup GStreamer pipeline with appsink for OpenCV"""
        empty_dict = dbus.Dictionary(signature="sv")
        fd_object = self.portal.OpenPipeWireRemote(
            self.session, empty_dict, dbus_interface=self.screen_cast_iface
        )
        if not fd_object:
            raise Exception("Failed to open PipeWire remote")
        self.fd = fd_object.take()

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
            options={"session_handle_token": session_token},
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

    def read_frame(self):
        """Read the latest frame (call this in your main loop)"""
        # Iterate GLib context to process new samples
        context = GLib.MainContext.default()
        context.iteration(False)

        if self.frame_ready:
            self.frame_ready = False
            return self.latest_frame
        return None

    def stop(self):
        """Stop the capture"""
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
        if hasattr(self, "loop"):
            self.loop.quit()
