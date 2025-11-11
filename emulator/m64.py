# This script is based on mupen64plusui-python (https://github.com/mupen64plus/mupen64plus-ui-python)
# Refer to the Mupen64Plus API as well for C++ APIs (https://www.mupen64plus.org/wiki/index.php/Mupen64Plus_v2.0_Core_Config)

import ctypes
import _ctypes
import subprocess
import time
import os
import sys
import threading
from ctypes import CDLL, c_void_p, c_char_p, c_int, POINTER

# header file defines
from emulator.defs import *


# def debug_callback(context, level, message):
#     if level <= M64MSG_ERROR:
#         sys.stderr.write("%s: %s\n" % (context.decode(), message.decode()))
#     elif level == M64MSG_WARNING:
#         sys.stderr.write("%s: %s\n" % (context.decode(), message.decode()))
#     elif level == M64MSG_INFO or level == M64MSG_STATUS:
#         sys.stderr.write("%s: %s\n" % (context.decode(), message.decode()))


# def state_callback(context, param, value):
#     if param == M64CORE_VIDEO_SIZE:
#         pass
#     elif param == M64CORE_VIDEO_MODE:
#         pass

# DEBUGFUNC = C.CFUNCTYPE(None, C.c_char_p, C.c_int, C.c_char_p)
# STATEFUNC = C.CFUNCTYPE(None, C.c_char_p, C.c_int, C.c_int)

# DEBUG_CALLBACK = DEBUGFUNC(debug_callback)
# STATE_CALLBACK = STATEFUNC(state_callback)


class M64Py:
    plugin_map = {
        M64PLUGIN_RSP: {},
        M64PLUGIN_GFX: {},
        M64PLUGIN_AUDIO: {},
        M64PLUGIN_INPUT: {},
    }

    def __init__(self):
        """Constructor"""
        super().__init__()
        self.m64p = None
        self.config = None
        self.state = M64EMU_STOPPED
        self.game_started = False

    def get_handle(self):
        """Return core library handle"""
        return self.m64p

    def core_load(self, path: str = ""):
        """Load core"""
        try:
            if path:
                self.m64p = ctypes.cdll.LoadLibrary(path)
            else:
                raise Exception("No path specified")
        except Exception as err:
            self.m64p = None
            print(err)

    def core_unload(self):
        """Unload core"""
        if self.m64p:
            _ctypes.dlclose(self.m64p._handle)

    def core_start(self, path: str):
        """Start Core"""
        if not self.m64p:
            raise Exception("Core library not loaded")
        # rval = self.m64p.CoreStartup(ctypes.c_int(CORE_API_VERSION), None, ctypes.c_char_p(os.path.dirname(path).encode()),ctypes.c_char_p(b"Core"), DEBUG_CALLBACK, ctypes.c_char_p(b"State"), STATE_CALLBACK)
        rval = self.m64p.CoreStartup(
            ctypes.c_int(CORE_API_VERSION),
            None,
            ctypes.c_char_p(os.path.dirname(path).encode()),
            None,
            None,
            None,
            None,
        )
        if rval == M64ERR_SUCCESS:
            # self.config = Config(self)
            print("Core started")
        else:
            print("Error starting core library")

    def core_shutdown(self):
        """Shutdown core"""
        if self.m64p:
            print("Shutting core down")
            self.m64p.CoreShutdown()
        return M64ERR_SUCCESS

    def getplugin_version(self, handle: CDLL, path: str):
        """Retrieve plugin info"""
        try:
            type_ptr = ctypes.pointer(ctypes.c_int())
            ver_ptr = ctypes.pointer(ctypes.c_int())
            api_ptr = ctypes.pointer(ctypes.c_int())
            name_ptr = ctypes.pointer(ctypes.c_char_p())
            cap_ptr = ctypes.pointer(ctypes.c_int())
            rval = handle.PluginGetVersion(
                type_ptr, ver_ptr, api_ptr, name_ptr, cap_ptr
            )
        except AttributeError:
            raise Exception("Plugin version error.")
        except OSError as err:
            raise Exception("Plugin version error.")
        else:
            if rval == M64ERR_SUCCESS:
                return (
                    type_ptr.contents.value,
                    ver_ptr.contents.value,
                    api_ptr.contents.value,
                    name_ptr.contents.value.decode(),
                    cap_ptr.contents.value,
                )
            else:
                raise Exception("Plugin version error.")

    def plugin_load_single(self, path: str):
        """Load a plugin from passed path"""
        if not os.path.isfile(path):
            raise Exception("Plugin path does not exist")

        try:
            plugin_handle = ctypes.cdll.LoadLibrary(path)
            version = self.getplugin_version(plugin_handle, path)
            if version:
                plugin_type, plugin_version, plugin_api, plugin_desc, pluginCap = (
                    version
                )
                plugin_name = os.path.basename(path)
                self.plugin_map[plugin_type][plugin_name] = (
                    plugin_handle,
                    path,
                    PLUGIN_NAME[plugin_type],
                    plugin_desc,
                    plugin_version,
                )
        except OSError as e:
            raise Exception("Error loading plugin")

    def plugin_load_all(self, plugin_location: str):
        """Load all the default plugins from defs.py"""
        for key, value in PLUGIN_DEFAULT.items():
            path = (
                plugin_location + value
            )  # path of each plugin (eg. ./mupen64plus-audio-sdl.so)
            # print(path)
            self.plugin_load_single(path)

    def plugin_startup(self, handle: CDLL, name: str, desc: str):
        """Start individual plugin"""
        if not self.m64p:
            raise Exception("Core not started")
        if not handle or self.m64p._handle is None:
            raise Exception("Plugin or core handle not valid")

        # rval = handle.PluginStartup(ctypes.c_void_p(self.m64p._handle), name, DEBUG_CALLBACK)
        rval = handle.PluginStartup(ctypes.c_void_p(self.m64p._handle), None, None)
        if rval != M64ERR_SUCCESS:
            raise Exception("Error starting plugin")

    def plugin_startup_all(self):
        """Start all plugins in plugin map"""
        for plugin_type in self.plugin_map.keys():
            for plugin_info in self.plugin_map[plugin_type].values():
                (
                    plugin_handle,
                    plugin_path,
                    plugin_name,
                    plugin_desc,
                    plugin_version,
                ) = plugin_info
                self.plugin_startup(plugin_handle, plugin_name, plugin_desc)
                # print(plugin_map)

    def plugin_shutdown(self, handle, desc):
        """Shutdown single plugin"""
        rval = handle.PluginShutdown()

    def plugin_shutdown_all(self):
        """Shutdown all plugins"""
        for plugin_type in self.plugin_map.keys():
            for plugin_info in self.plugin_map[plugin_type].values():
                (
                    plugin_handle,
                    plugin_path,
                    plugin_name,
                    plugin_desc,
                    plugin_version,
                ) = plugin_info
                self.plugin_shutdown(plugin_handle, plugin_desc)
        print("Shutting plugins down")

    def plugin_attach(self):
        """Attach plugins to core"""
        for plugin_type in PLUGIN_ORDER:
            # TODO: ran into weird issue where audio plugin causes floating point exception
            # if plugin_type == M64PLUGIN_AUDIO:
            # continue
            (plugin_handle, plugin_path, plugin_name, plugin_desc, plugin_version) = (
                list(self.plugin_map[plugin_type].values())[0]
            )
            rval = self.m64p.CoreAttachPlugin(
                ctypes.c_int(plugin_type), ctypes.c_void_p(plugin_handle._handle)
            )
            if rval != M64ERR_SUCCESS:
                raise Exception(
                    "Failed to attach plugin %s to core" % plugin_name.decode()
                )
            else:
                print("Attached plugin: %s" % plugin_name.decode())

    def plugin_detatch(self):
        """Detatch plugin from core"""
        for plugin_type in PLUGIN_ORDER:
            (plugin_handle, plugin_path, plugin_name, plugin_desc, plugin_version) = (
                list(self.plugin_map[plugin_type].values())[0]
            )
            rval = self.m64p.CoreDetachPlugin(ctypes.c_int(plugin_type))
            if rval != M64ERR_SUCCESS:
                raise Exception(
                    "Failed to detach plugin %s to core" % plugin_name.decode()
                )
            else:
                print("Detached plugins")

    def rom_open(self, rom_path):
        """Open ROM file"""
        # load rom
        rom_length = ctypes.c_int(os.path.getsize(rom_path))
        try:
            f = open(rom_path, "rb")
        except IOError:
            raise IOError("ROM does not exist. Check path")
        rom_file = f.read()
        f.close()
        rom_buffer = ctypes.c_buffer(rom_file)
        rom_test = self.m64p.CoreDoCommand(
            M64CMD_ROM_OPEN, rom_length, ctypes.byref(rom_buffer)
        )
        if rom_test != M64ERR_SUCCESS:
            raise Exception("Failed to open ROM")
        del rom_buffer

    def rom_close(self):
        """Close ROM file"""
        self.m64p.CoreDoCommand(M64CMD_ROM_CLOSE)

    def rom_get_header(self):
        """Get header data of ROM"""
        pass

    def rom_get_settings(self):
        """Get settings of ROM"""
        pass

    def start_emulator(self):
        """Start emulator and run ROM"""
        print("Starting Emulator")
        rval = self.m64p.CoreDoCommand(M64CMD_EXECUTE, 0, None)
        if rval != M64ERR_SUCCESS:
            print("Couldn't start emulator")
        return rval

    def stop_emulator(self):
        """Stop emulator"""
        rval = self.m64p.CoreDoCommand(M64CMD_STOP, 0, None)

    def state_load(self, state_path="~/.local/share/mupen64plus/save/"):
        """Load a saved state file from current slot"""
        print("Loading state")
        path = ctypes.c_char_p(state_path.encode())
        rval = self.m64p.CoreDoCommand(M64CMD_STATE_LOAD, ctypes.c_int(1), path)
        if rval != M64ERR_SUCCESS:
            print("Failed to load state")

    def read_memory(self, address=None):
        """Read an address from N64 memory space to retrive its value"""
        if self.m64p and self.game_started:
            if address:
                value = ctypes.c_int()
                value = self.m64p.DebugMemRead32(ctypes.c_uint(address))
                return value
            else:
                print("No address input")
                return None
        else:
            print("M64 not started!")
            return None

    def get_game_started(self):
        return self.game_started

    def run_emulator(self, core_path=None, plugin_path=None, rom_path=None):
        """
        Combine initialization process:
        1. Load and start core (using default configs from ~/.config/mupen64plus/mupen64plus.cfg)
        2. Find, load, start default plugins
        3. Open and load ROM
        4. Play ROM
        5. Attach plugins
        6. Start emulator
        7. Cleanup when finished
        """
        if core_path and plugin_path and rom_path:
            self.core_load(core_path)
            self.core_start(core_path)
            self.plugin_load_all(plugin_path)
            self.plugin_startup_all()
            self.rom_open(rom_path)
            self.plugin_attach()
            self.game_started = True
            self.start_emulator()
            self.close_emulator()
        else:
            raise Exception("Please specify plugin, core, and rom path")

    def close_emulator(self):
        self.game_started = False
        self.plugin_detatch()
        self.rom_close()
        self.plugin_shutdown_all()
        self.core_shutdown()
        self.core_unload()
