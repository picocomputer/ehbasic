#!/usr/bin/env python3
#
# Copyright (c) 2025 Rumbledethumps
#
# SPDX-License-Identifier: BSD-3-Clause
# SPDX-License-Identifier: Unlicense

# Developer tool for RP6502

import os
import re
import time
import serial
import binascii
import argparse
import configparser
import platform
import sys
import select
import ctypes
from typing import Union

# Detect POSIX terminal
try:
    import tty
except:
    pass


class Console:
    """Manages the RP6502 console over a serial connection."""

    DEFAULT_TIMEOUT = 0.5
    UART_BAUDRATE = 115200

    def default_device():
        # Hint at where the USB CDC mounts on various OSs
        if platform.system() == "Windows":
            return "COM1"
        elif platform.system() == "Darwin":
            return "/dev/cu.usbmodem"
        elif platform.system() == "Linux":
            return "/dev/ttyACM0"
        else:
            return "/dev/tty"

    def __init__(self, name: str, timeout: float = DEFAULT_TIMEOUT):
        """Initialize console over serial connection."""
        self.serial = serial.Serial()
        self.serial.setPort(name)
        self.serial.timeout = timeout
        self.serial.baudrate = self.UART_BAUDRATE
        self.serial.open()

    def code_page(self, timeout: float = DEFAULT_TIMEOUT) -> str:
        """Fetch code page to use for terminal encoding"""
        self.serial.write(b"set cp\r")
        self.wait_for_prompt(":", timeout)
        result = self.serial.read_until().decode("ascii")
        return f"cp{re.sub(r'[^0-9]', '', result)}"

    def terminal(self, cp):
        """Dispatch to the correct terminal emulator"""
        print("Console terminal. CTRL-A then B for break or X for exit.")
        # We also accept CTRL-A F and CTRL-A Q for minicom habits.
        if "tty" in globals():
            self.term_posix(cp)
        else:
            self.term_windows(cp)

    def term_posix(self, cp: str):
        """POSIX terminal emulator for Linux, BSD, MacOS, etc."""
        tty.setraw(sys.stdin.fileno())
        ctrl_a_pressed = False
        while True:
            ready, _, _ = select.select([sys.stdin, self.serial], [], [], None)
            if sys.stdin in ready:
                char = os.read(sys.stdin.fileno(), 1).decode("utf-8", errors="ignore")
                if char == "\x01":  # CTRL-A
                    ctrl_a_pressed = True
                    self.serial.write(char.encode(cp))
                elif ctrl_a_pressed and char.lower() in "bf":
                    self.send_break()  # eats prompt
                    sys.stdout.write("\r\n]")  # fake prompt
                    ctrl_a_pressed = False
                elif ctrl_a_pressed and char.lower() in "xq":
                    sys.stdout.write("\r\n")
                    if sys.stdin.isatty():
                        os.system("stty sane")
                    break
                else:
                    ctrl_a_pressed = False
                    self.serial.write(char.encode(cp))
            if self.serial in ready:
                data = self.serial.read(1)
                if len(data) > 0:
                    try:
                        sys.stdout.write(data.decode(cp))
                    except UnicodeDecodeError:
                        sys.stdout.write(f"\\x{data[0]:02x}")
                    sys.stdout.flush()

    def term_windows(self, cp):
        """Windows terminal emulator using Console API"""
        ctrl_a_pressed = False
        while True:
            try:
                if self.serial.in_waiting > 0:
                    data = self.serial.read(1)
                    if len(data) > 0:
                        try:
                            sys.stdout.write(data.decode(cp))
                        except UnicodeDecodeError:
                            sys.stdout.write(f"\\x{data[0]:02x}")
                        sys.stdout.flush()
                key_in = self.term_windows_keyboard()
                if key_in:
                    if key_in == "\x01":  # CTRL-A
                        ctrl_a_pressed = True
                        self.serial.write(key_in.encode(cp))
                    elif ctrl_a_pressed and key_in.lower() in "bf":
                        self.send_break()  # eats prompt
                        sys.stdout.write("\r\n]")  # fake prompt
                        ctrl_a_pressed = False
                    elif ctrl_a_pressed and key_in.lower() in "xq":
                        sys.stdout.write("\r\n")
                        break
                    else:
                        ctrl_a_pressed = False
                        self.serial.write(key_in.encode(cp))
                else:
                    if self.serial.in_waiting == 0:
                        time.sleep(0.001)
            except KeyboardInterrupt:
                self.serial.write(b"\x03")

    def term_windows_keyboard(self) -> Union[str, None]:
        """Get a key event as ANSI using Windows Console API"""

        # FFI setup
        from ctypes import wintypes

        if not hasattr(self, "_stdin_handle"):
            self._stdin_handle = ctypes.windll.kernel32.GetStdHandle(-10)

        class KEY_EVENT_RECORD(ctypes.Structure):
            _fields_ = [
                ("bKeyDown", wintypes.BOOL),
                ("wRepeatCount", wintypes.WORD),
                ("wVirtualKeyCode", wintypes.WORD),
                ("wVirtualScanCode", wintypes.WORD),
                ("uChar", wintypes.WCHAR),
                ("dwControlKeyState", wintypes.DWORD),
            ]

        class INPUT_RECORD(ctypes.Structure):
            _fields_ = [
                ("EventType", wintypes.WORD),
                ("Event", KEY_EVENT_RECORD),
            ]

        # Check if input is available
        events_available = wintypes.DWORD()
        ctypes.windll.kernel32.GetNumberOfConsoleInputEvents(
            self._stdin_handle, ctypes.byref(events_available)
        )
        if events_available.value == 0:
            return None

        # Read input event
        input_record = INPUT_RECORD()

        if not ctypes.windll.kernel32.ReadConsoleInputW(
            self._stdin_handle,
            ctypes.byref(input_record),
            1,
            ctypes.byref(wintypes.DWORD()),
        ):
            return None

        # Only process key down events (EventType 1 = KEY_EVENT)
        if input_record.EventType != 1 or not input_record.Event.bKeyDown:
            return None

        # Modifier state
        alt = bool(input_record.Event.dwControlKeyState & (0x0001 | 0x0002))
        ctrl = bool(input_record.Event.dwControlKeyState & (0x0004 | 0x0008))
        shift = bool(input_record.Event.dwControlKeyState & 0x0010)
        modifier = 1
        if shift:
            modifier += 1
        if alt:
            modifier += 2
        if ctrl:
            modifier += 4
        if modifier == 1:
            modifier = False

        # Virtual key codes
        vk_code = input_record.Event.wVirtualKeyCode
        if vk_code == 0x0D:  # Enter/Return
            return "\r"
        elif vk_code == 0x08:  # Backspace
            return "\b"
        elif vk_code == 0x57 and ctrl:  # Ctrl+Backspace
            return "\b"
        elif vk_code == 0x09:  # Tab
            return "\t"
        elif vk_code == 0x1B:  # Escape
            return "\x1b"
        elif vk_code == 0x20:  # Space
            return " "
        elif vk_code == 0x70:  # F1
            return f"\x1b[1;{modifier}P" if modifier else "\x1bOP"
        elif vk_code == 0x71:  # F2
            return f"\x1b[1;{modifier}Q" if modifier else "\x1bOQ"
        elif vk_code == 0x72:  # F3
            return f"\x1b[1;{modifier}R" if modifier else "\x1bOR"
        elif vk_code == 0x73:  # F4
            return f"\x1b[1;{modifier}S" if modifier else "\x1bOS"
        elif vk_code == 0x74:  # F5
            return f"\x1b[15;{modifier}~" if modifier else "\x1b[15~"
        elif vk_code == 0x75:  # F6
            return f"\x1b[17;{modifier}~" if modifier else "\x1b[17~"
        elif vk_code == 0x76:  # F7
            return f"\x1b[18;{modifier}~" if modifier else "\x1b[18~"
        elif vk_code == 0x77:  # F8
            return f"\x1b[19;{modifier}~" if modifier else "\x1b[19~"
        elif vk_code == 0x78:  # F9
            return f"\x1b[20;{modifier}~" if modifier else "\x1b[20~"
        elif vk_code == 0x79:  # F10
            return f"\x1b[21;{modifier}~" if modifier else "\x1b[21~"
        elif vk_code == 0x7A:  # F11
            return f"\x1b[23;{modifier}~" if modifier else "\x1b[23~"
        elif vk_code == 0x7B:  # F12
            return f"\x1b[24;{modifier}~" if modifier else "\x1b[24~"
        elif vk_code == 0x26:  # Up arrow
            return f"\x1b[1;{modifier}A" if modifier else "\x1b[A"
        elif vk_code == 0x28:  # Down arrow
            return f"\x1b[1;{modifier}B" if modifier else "\x1b[B"
        elif vk_code == 0x27:  # Right arrow
            return f"\x1b[1;{modifier}C" if modifier else "\x1b[C"
        elif vk_code == 0x25:  # Left arrow
            return f"\x1b[1;{modifier}D" if modifier else "\x1b[D"
        elif vk_code == 0x24:  # Home
            return f"\x1b[1;{modifier}H" if modifier else "\x1b[H"
        elif vk_code == 0x23:  # End
            return f"\x1b[1;{modifier}F" if modifier else "\x1b[F"
        elif vk_code == 0x21:  # Page Up
            return f"\x1b[5;{modifier}~" if modifier else "\x1b[5~"
        elif vk_code == 0x22:  # Page Down
            return f"\x1b[6;{modifier}~" if modifier else "\x1b[6~"
        elif vk_code == 0x2D:  # Insert
            return f"\x1b[2;{modifier}~" if modifier else "\x1b[2~"
        elif vk_code == 0x2E:  # Delete
            return f"\x1b[3;{modifier}~" if modifier else "\x1b[3~"

        # ASCII codes
        char = input_record.Event.uChar
        if ctrl and not alt:
            if char:
                ch = ord(char)
                if ord("`") <= ch <= ord("~"):
                    return chr(ch - 96)
                elif ord("@") <= ch <= ord("_"):
                    return chr(ch - 64)
            # Ctrl+A through Ctrl+Z using virtual key codes
            if 65 <= vk_code <= 90:
                return chr(vk_code - 64)
            return None
        if char and ord(char) != 0:
            return char
        return None

    def send_break(self, duration: float = 0.01, retries: int = 1):
        """Stop the 6502 and return to monitor."""
        self.serial.read_all()
        self.serial.send_break(duration)
        try:
            self.wait_for_prompt("]")
            return
        except TimeoutError as te:
            if retries <= 0:
                raise
        self.send_break(duration, retries - 1)

    def command(self, cmd: str, timeout: float = DEFAULT_TIMEOUT):
        """Send one command and wait for next monitor prompt."""
        self.serial.write(bytes(cmd, "ascii"))
        self.serial.write(b"\r")
        self.wait_for_prompt("]", timeout)

    def reset(self):
        """Start the 6502."""
        self.serial.write(b"RESET\r")
        self.serial.read_until()

    def binary(self, addr: int, data: bytes):
        """Send data to memory using BINARY command."""
        command = f"BINARY ${addr:04X} ${len(data):03X} ${binascii.crc32(data):08X}\r"
        self.serial.write(bytes(command, "utf-8"))
        self.serial.write(data)
        self.wait_for_prompt("]")

    def upload(self, file, name: str):
        """Upload readable file to remote file "name"."""
        self.serial.write(bytes(f"UPLOAD {name}\r", "ascii"))
        self.wait_for_prompt("}")
        file.seek(0)
        while True:
            chunk = file.read(1024)
            if len(chunk) == 0:
                break
            command = f"${len(chunk):03X} ${binascii.crc32(chunk):08X}\r"
            self.serial.write(bytes(command, "ascii"))
            self.serial.write(chunk)
            self.wait_for_prompt("}")
        self.serial.write(b"END\r")
        self.wait_for_prompt("]")

    def send_rom(self, rom):
        """Send rom."""
        addr, data = rom.next_rom_data(0)
        while data is not None:
            self.binary(addr, data)
            addr += len(data)
            addr, data = rom.next_rom_data(addr)

    def wait_for_prompt(self, prompt: str, timeout: float = DEFAULT_TIMEOUT):
        """Wait for a specific prompt from the device."""
        prompt_bytes = bytes(prompt, "ascii")
        start = time.monotonic()
        at_line_start = True
        while True:
            if len(prompt) == 1:
                data = self.serial.read()
                if at_line_start and data == b"?":
                    monitor_result = data.decode("ascii")
                    monitor_result += self.serial.read_until().decode("ascii").strip()
                    raise RuntimeError(monitor_result)
                at_line_start = (data == b"\n" or data == b"\r")
            else:
                data = self.serial.read_until()
                if data.startswith(b"?"):
                    monitor_result = data.decode("ascii")
                    monitor_result += self.serial.read_until().decode("ascii").strip()
                    raise RuntimeError(monitor_result)
            if data.strip().lower() == prompt_bytes.lower():
                break
            if len(data) == 0:
                if time.monotonic() - start > timeout:
                    raise TimeoutError()


class ROM:
    """Virtual ROM aka The RP6502 ROM."""

    def __init__(self):
        """ROMs begin with up to a screen of help text"""
        """followed by a sparse array of virtual ROM."""
        self.help = []
        self.data = [0 for i in range(0x20000)]
        self.alloc = [0 for i in range(0x20000)]

    def add_help(self, string: str):
        """Add help string."""
        if len(string) > 80:
            raise RuntimeError("Help line > 80 cols")
        self.help.append(string)
        if len(self.help) > 24:
            raise RuntimeError("Help lines > 24 rows")

    def add_binary_data(self, data: bytes, addr: int):
        """Add binary data to ROM."""
        length = len(data)
        self.allocate_rom(addr, length)
        for i in range(length):
            self.data[addr + i] = data[i]

    def add_nmi_vector(self, addr: int):
        """Set NMI vector in $FFFA and $FFFB."""
        if not (0 <= addr <= 0xFFFF):
            raise RuntimeError(f"Invalid NMI vector: ${addr:04X}")
        self.allocate_rom(0xFFFA, 2)
        self.data[0xFFFA] = addr & 0xFF
        self.data[0xFFFB] = addr >> 8

    def add_reset_vector(self, addr: int):
        """Set reset vector in $FFFC and $FFFD."""
        if not (0 <= addr <= 0xFFFF):
            raise RuntimeError(f"Invalid reset vector: ${addr:04X}")
        self.allocate_rom(0xFFFC, 2)
        self.data[0xFFFC] = addr & 0xFF
        self.data[0xFFFD] = addr >> 8

    def add_irq_vector(self, addr: int):
        """Set IRQ vector in $FFFE and $FFFF."""
        if not (0 <= addr <= 0xFFFF):
            raise RuntimeError(f"Invalid IRQ vector: ${addr:04X}")
        self.allocate_rom(0xFFFE, 2)
        self.data[0xFFFE] = addr & 0xFF
        self.data[0xFFFF] = addr >> 8

    def add_binary_file(self, file: str, **addr):
        """Add binary memory data from file. The addr kwargs are: data, nmi, reset, and irq."""
        """Data is where to load the data, the rest are CPU vectors for $FFFA-$FFFF."""
        """Addresses should be an int, None to not provide, or True to read from the file."""
        """Vectors are read from the file in the order listed above."""
        with open(file, "rb") as f:
            data = f.read()
        if addr["data"] is None:
            raise RuntimeError("Address for data is required.")
        if addr["data"] is True:
            if len(data) < 2:
                raise RuntimeError("No data address found in file.")
            addr["data"] = data[0] + data[1] * 256
            data = data[2:]
        if addr["nmi"] is True:
            if len(data) < 2:
                raise RuntimeError("No nmi address found in file.")
            addr["nmi"] = data[0] + data[1] * 256
            data = data[2:]
        if addr["nmi"]:
            self.add_nmi_vector(addr["nmi"])
        if addr["reset"] is True:
            if len(data) < 2:
                raise RuntimeError("No reset address found in file.")
            addr["reset"] = data[0] + data[1] * 256
            data = data[2:]
        if addr["reset"]:
            self.add_reset_vector(addr["reset"])
        if addr["irq"] is True:
            if len(data) < 2:
                raise RuntimeError("No irq address found in file.")
            addr["irq"] = data[0] + data[1] * 256
            data = data[2:]
        if addr["irq"]:
            self.add_irq_vector(addr["irq"])
        self.add_binary_data(data, addr["data"])

    def add_rp6502_file(self, file: str):
        """Add RP6502 ROM data from file."""
        with open(file, "rb") as f:
            # Decode first line as cp850 because binary garbage can
            # raise here before our better message gets to the user.
            command = f.readline().decode("cp850")
            if not re.match(r"^#![Rr][Pp]6502\r?\n$", command):
                raise RuntimeError(f"Invalid RP6502 ROM file: {file}")
            while True:
                command = f.readline().decode("ascii").rstrip()
                if len(command) == 0:
                    break
                help_match = re.search(r"^ *(# )", command)
                if help_match:
                    self.add_help(command[help_match.start(1) + 2 :])
                    continue
                if re.search(r"^ *#$", command):
                    self.add_help("")
                    continue
                data_match = re.search(r"^ *([^ ]+) *([^ ]+) *([^ ]+) *$", command)
                if data_match:

                    def str_to_address(addr_str: str) -> int:
                        """Supports $FFFF number format."""
                        if addr_str:
                            addr_str = re.sub(r"^\$", "0x", addr_str)
                        if re.match(r"^(0x|)[0-9A-Fa-f]*$", addr_str):
                            return int(addr_str, 0)
                        else:
                            raise RuntimeError(f"Invalid address: {addr_str}")

                    addr = str_to_address(data_match.group(1))
                    length = str_to_address(data_match.group(2))
                    crc = str_to_address(data_match.group(3))
                    self.allocate_rom(addr, length)
                    data = f.read(length)
                    if len(data) != length or crc != binascii.crc32(data):
                        raise RuntimeError(f"Invalid CRC in block address: ${addr:04X}")
                    for i in range(length):
                        self.data[addr + i] = data[i]
                    continue
                raise RuntimeError(f"Corrupt RP6502 ROM file: {file}")

    def allocate_rom(self, addr: int, length: int):
        """Marks a range of memory as used."""
        if (
            (addr < 0x10000 and addr + length > 0x10000)
            or addr + length > 0x20000
            or addr < 0
            or length < 0
        ):
            raise IndexError(
                f"RP6502 invalid address ${addr:04X} or length ${length:03X}"
            )
        for i in range(length):
            if self.alloc[addr + i]:
                raise MemoryError(f"RP6502 ROM data already exists at ${addr+i:04X}")
            self.alloc[addr + i] = 1

    def has_reset_vector(self) -> bool:
        """Returns true if $FFFC and $FFFD have been set."""
        return bool(self.alloc[0xFFFC] and self.alloc[0xFFFD])

    def next_rom_data(self, addr: int):
        """Find next up-to-1k chunk starting at addr."""
        for addr in range(addr, 0x20000):
            if self.alloc[addr]:
                length = 0
                while self.alloc[addr + length]:
                    length += 1
                    if length == 1024 or addr + length == 0x10000:
                        break
                return addr, bytearray(self.data[addr : addr + length])
        return None, None


def exec_args():
    # Standard library argument parser
    parser = argparse.ArgumentParser(
        description="Interface with RP6502 RIA console. Manage RP6502 ROM packaging."
    )
    parser.add_argument(
        "command",
        choices=["run", "upload", "basic", "create"],
        help="{Run} local RP6502 ROM file by sending to RP6502 RAM. "
        "{Upload} any local files to RP6502 USB storage. "
        "{Basic} executes a program with the installed BASIC. "
        "{Create} RP6502 ROM file from a local binary file and additional local ROM files.",
    )
    parser.add_argument("filename", nargs="*", help="Local filename(s).")
    parser.add_argument("-o", dest="out", metavar="name", help="Output path/filename.")
    parser.add_argument(
        "-a",
        "--address",
        dest="address",
        metavar="addr",
        help="Starting address of data or `file` to read from file.",
    )
    parser.add_argument(
        "-n",
        "--nmi",
        dest="nmi",
        metavar="addr",
        help="NMI vector for $FFFA-$FFFB or `file` to read from file.",
    )
    parser.add_argument(
        "-r",
        "--reset",
        dest="reset",
        metavar="addr",
        help="Reset vector for $FFFC-$FFFD or `file` to read from file.",
    )
    parser.add_argument(
        "-i",
        "--irq",
        dest="irq",
        metavar="addr",
        help="IRQ vector for $FFFE-$FFFF or `file` to read from file.",
    )
    parser.add_argument(
        "-c",
        "--config",
        dest="config",
        metavar="name",
        help=f"Configuration file for console connection.",
    )
    parser.add_argument(
        "-D",
        "--device",
        dest="device",
        metavar="dev",
        default=Console.default_device(),
        help=f"Serial device name. Default={Console.default_device()}",
    )
    parser.add_argument(
        "-t",
        "--term",
        dest="term",
        metavar="bool",
        default="True",
        help=f"Enables console terminal on run.",
    )
    args = parser.parse_args()

    # Standard library configuration parser
    if args.config:
        config = configparser.ConfigParser()
        if not os.path.exists(args.config):
            config["RP6502"] = {"device": args.device, "term": args.term}
            with open(args.config, "w") as cfg:
                config.write(cfg)
        else:
            config.read(args.config)
        if config.has_section("RP6502"):
            args.device = config["RP6502"].get("device", args.device)
            args.term = config["RP6502"].get("term", args.term)

    # Because parser is bad at bool
    if args.term.lower() in ["t", "true"] or (args.term.isdigit() and args.term != "0"):
        args.term = True
    else:
        args.term = False

    # Additional validation and conversion
    def str_to_address(parser, str, errmsg):
        """Supports $FFFF number format."""
        if str:
            str = re.sub("^\\$", "0x", str)
            if re.match("^(0x|)[0-9A-Fa-f]*$", str):
                return int(str, 0)
            elif str.lower() == "file":
                return True
            else:
                parser.error(f"argument {errmsg}: invalid address: '{str}'")

    args.address = str_to_address(parser, args.address, "-a/--address")
    args.nmi = str_to_address(parser, args.nmi, "-n/--nmi")
    args.reset = str_to_address(parser, args.reset, "-r/--reset")
    args.irq = str_to_address(parser, args.irq, "-i/--irq")

    # Open console and extend error with a hint about the config file
    if args.command in ["run", "upload", "basic"]:
        print(f"[{os.path.basename(__file__)}] Opening device {args.device}")
        try:
            console = Console(args.device)
        except serial.SerialException as se:
            # On Windows, se.errno is None; on Unix it's 2 when serial port not found.
            if args.config and ("FileNotFoundError" in str(se) or se.errno == 2):
                error_msg = f"Using device config in {args.config}\n{str(se)}"
                raise serial.SerialException(error_msg) from se
            else:
                raise
        console.send_break()

    # python3 rp6502.py run
    if args.command == "run":
        print(f"[{os.path.basename(__file__)}] Loading ROM {args.filename[0]}")
        rom = ROM()
        rom.add_rp6502_file(args.filename[0])
        if args.reset != None:
            rom.add_reset_vector(args.reset)
        print(f"[{os.path.basename(__file__)}] Sending ROM")
        console.send_rom(rom)
        if args.term:
            code_page = console.code_page()
        if rom.has_reset_vector():
            console.reset()
        else:
            print(f"[{os.path.basename(__file__)}] No reset vector. Not resetting.")
        if args.term:
            console.terminal(code_page)

    # python3 rp6502.py upload
    if args.command == "upload":
        for file in args.filename:
            print(f"[{os.path.basename(__file__)}] Uploading {file}")
            with open(file, "rb") as f:
                if len(args.filename) == 1 and args.out != None:
                    dest = args.out
                else:
                    dest = os.path.basename(file)
                console.upload(f, dest)

    # python3 rp6502.py basic
    if args.command == "basic":
        code_page = console.code_page()
        print(f"[{os.path.basename(__file__)}] Starting BASIC")
        console.serial.write(b"BASIC\r")
        console.wait_for_prompt("READY\r\n")
        print(f"[{os.path.basename(__file__)}] Uploading program")
        with open(args.filename[0], "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f):
                # Wait the perfect amount of time it takes to parse the line
                # by waiting for a character to echo, then deleting it.
                console.serial.write(b"0")
                echo = console.serial.read(1)
                console.serial.write(b"\b")
                if echo != b"0":
                    msg = console.serial.read_until(b"\r\n").decode("ascii").strip()
                    raise RuntimeError(f"Line {line_num}: {msg}")
                console.serial.write(line.encode(code_page) + b"\r")
                console.serial.read_until(b"\r\n")
        print(f"[{os.path.basename(__file__)}] Running program")
        console.serial.write(b"RUN\r")
        if args.term:
            console.terminal(code_page)

    # python3 rp6502.py create
    if args.command == "create":
        if args.out == None:
            parser.error(f"argument -o required")
        if args.address == None:
            parser.error(f"argument -a/--address required")
        print(f"[{os.path.basename(__file__)}] Creating {args.out}")
        rom = ROM()
        print(f"[{os.path.basename(__file__)}] Adding binary asset {args.filename[0]}")
        rom.add_binary_file(
            args.filename[0],
            data=args.address,
            nmi=args.nmi,
            reset=args.reset,
            irq=args.irq,
        )
        for file in args.filename[1:]:
            print(f"[{os.path.basename(__file__)}] Adding ROM asset {file}")
            rom.add_rp6502_file(file)
        with open(args.out, "wb+") as file:
            file.write(b"#!RP6502\n")
            for help in rom.help:
                file.write(bytes(f"# {help}\n", "ascii"))
            addr, data = rom.next_rom_data(0)
            while data != None:
                file.write(
                    bytes(
                        f"${addr:04X} ${len(data):03X} ${binascii.crc32(data):08X}\n",
                        "ascii",
                    )
                )
                file.write(data)
                addr += len(data)
                addr, data = rom.next_rom_data(addr)


# This file may be included or run like a program. e.g.
#   import importlib
#   rp6502 = importlib.import_module("tools.rp6502")
if __name__ == "__main__":
    # VSCode SIGKILLs the terminal while in raw mode, return to cooked mode.
    if "tty" in globals() and sys.stdin.isatty():
        os.system("stty sane")
    # Catch the two most common failures when using from VSCode so that a
    # terminal message is displayed instead of triggering the Python debugger.
    try:
        exec_args()
    except serial.SerialException as se:
        print(f"[{os.path.basename(__file__)}] {str(se)}")
    except FileNotFoundError as fe:
        error_msg = str(fe)
        if re.search(r"\$\{[^}]*\}\.rp6502", error_msg):
            print(f"[{os.path.basename(__file__)}] Build may have failed.\n{error_msg}")
        else:
            raise
