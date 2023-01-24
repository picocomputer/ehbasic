# Control RP6502 RIA via UART

import sys,io,time,subprocess,serial,binascii
from typing import Union

class Monitor:
    DEFAULT_TIMEOUT = 0.2
    serial = serial.Serial()

    def __init__(self, name, timeout=DEFAULT_TIMEOUT):
        self.serial.setPort(name)
        self.serial.timeout = timeout
        self.serial.open()

    def send_break(self, duration=0.01):
        ''' Stop the 6502 and return to monitor. '''
        self.serial.read_all()
        self.serial.send_break(duration)
        self.wait_for_prompt(']')

    def command(self, str):
        ''' Send one command and wait for next monitor prompt '''
        self.serial.write(bytes(str, 'utf-8'))
        self.serial.write(b'\r')
        self.wait_for_prompt(']')

    def reset(self):
        ''' Start the 6502. '''
        self.serial.write(b'RESET\r')
        self.serial.read_until()

    def binary(self, addr:int, data):
        ''' Send data to memory using BINARY command. '''
        command = f'BINARY ${addr:04X} ${len(data):03X} ${binascii.crc32(data):08X}\r'
        self.serial.write(bytes(command, 'utf-8'))
        self.serial.write(data)
        self.wait_for_prompt(']')

    def upload(self, name, data):
        ''' Upload readable (file,rom,etc) to remote file "name" '''
        self.serial.write(bytes(f'UPLOAD {name}\r', 'utf-8'))
        self.wait_for_prompt('}')
        data.seek(0)
        while True:
            chunk = data.read(1024)
            if len(chunk) == 0:
                break
            command = f'${len(chunk):03X} ${binascii.crc32(chunk):08X}\r'
            self.serial.write(bytes(command, 'utf-8'))
            self.serial.write(chunk)
            self.wait_for_prompt('}')
        self.serial.write(b'END\r')
        self.wait_for_prompt(']')

    def send_reset_vector(self, addr:Union[int, None]=None):
        ''' Set reset vector. Use start address of last file as default. '''
        if addr == None:
            addr = self.reset_vector_guess
        if addr == None:
            raise RuntimeError("Reset vector not set")
        self.binary(0xFFFC, bytearray([addr & 0xFF, addr >> 8]))

    def send_file_to_memory(self, name, addr:Union[int, None]=None):
        ''' Send binary file. addr=None uses first two bytes as address.'''
        with open(name, 'rb') as f:
            if addr==None:
                data = f.read(2)
                addr = data[0] + data[1] * 256
            self.reset_vector_guess = addr
            while True:
                data = f.read(1024)
                if len(data) == 0:
                    break
                self.binary(addr, data)
                addr += len(data)

    def wait_for_prompt(self, prompt, timeout=DEFAULT_TIMEOUT):
        ''' Wait for prompt. '''
        prompt = bytes(prompt, 'utf-8')
        start = time.monotonic()
        while True:
            if len(prompt) == 1:
                data = self.serial.read()
            else:
                data = self.serial.read_until()
            if data[0:1] == b'?':
                monitor_result = data.decode('utf-8')
                monitor_result += self.serial.read_until().decode('utf-8').strip()
                raise RuntimeError(monitor_result)
            if data == prompt:
                break
            if len(data) == 0:
                if time.monotonic() - start > timeout:
                    raise TimeoutError()

    def basic_command(self, str, timeout=DEFAULT_TIMEOUT):
        ''' Send one line using "0\b" faux flow control. '''
        self.serial.write(b'0')
        start = time.monotonic()
        while True:
            r = self.serial.read()
            if r == b'\x00': # huh, zeros?
                continue
            if r == b'0':
                break
            if time.monotonic() - start > timeout:
                raise TimeoutError()
        self.serial.write(b'\b')
        self.serial.write(bytes(str, 'utf-8'))
        self.serial.write(b'\r')
        self.serial.read_until()

    def basic_wait_for_ready(self, timeout=DEFAULT_TIMEOUT):
        ''' Wait for BASIC Ready. '''
        self.wait_for_prompt('Ready\r\n', timeout)


class ROM:
    def __init__(self):
        self.out = io.BytesIO(b'')
        # Shebang.
        self.out.write(b"#!RP6502\n")

    def seek(self, pos: int) -> int:
        return self.out.seek(pos)

    def read(self, size: Union[int, None]) -> bytes:
        return self.out.read(size)

    def comment(self, str):
        ''' Comments before binary data are used for help and info. '''
        self.out.write(b'# ')
        self.out.write(bytes(str, 'utf-8'))
        self.out.write(b'\n')

    def binary(self, addr, data):
        ''' Binary memory data. '''
        command = f'${addr:04X} ${len(data):03X} ${binascii.crc32(data):08X}\n'
        self.out.write(bytes(command, 'utf-8'))
        self.out.write(data)

    def binary_file(self, name, addr: Union[int, None]=None):
        ''' Binary memory data from file. addr=None uses first two bytes as address.'''
        with open(name, 'rb') as f:
            data = f.read()
        pos = 0
        if addr==None:
            pos += 2
            addr = data[0] + data[1] * 256
        self.reset_vector_guess = addr
        while pos < len(data):
            size = len(data) - pos
            if size > 1024:
                size = 1024
            self.binary(addr, data[pos:pos+size])
            addr += size
            pos += size

    def reset_vector(self, addr: Union[int, None]=None):
        ''' Set reset vector. Use start address of last file as default. '''
        if addr == None:
            addr = self.reset_vector_guess
        if addr == None:
            raise RuntimeError("Reset vector not set")
        self.binary(0xFFFC, bytearray([addr & 0xFF, addr >> 8]))

def run(args) -> subprocess.CompletedProcess:
    ''' Run a system process. For example, a compiler. '''
    cp = subprocess.run(args)
    if cp.returncode != 0:
        sys.exit(cp.returncode)

#################################################
### Above should be importable module one day ###
#################################################

run(['64tass', '--mw65c02', 'min_mon.asm'])

if False: # Send to memory and test
    mon=Monitor('/dev/ttyACM0')
    mon.send_break()
    mon.send_file_to_memory('a.out')
    mon.reset()
    mon.serial.write(b'C') # [C]old/[W]arm ?
    mon.serial.write(b'\r') # Memory size ?
    mon.basic_wait_for_ready(1)
    mon.basic_command('10 PRINT "Hello, World!"')
    mon.basic_command('RUN')
    mon.basic_wait_for_ready(1)
else: # Upload to USB drive
    rom=ROM()
    rom.comment("Lee Davidson's EhBASIC 2.22p5 for the Picocomputer 6502")
    rom.comment('')
    rom.comment('EhBASIC is free but not copyright free. For non commercial use there is only')
    rom.comment('one restriction, any derivative work should include, in any binary image')
    rom.comment('distributed, the string "Derived from EhBASIC" and in any distribution that')
    rom.comment('includes human readable files a file that includes the above string in a')
    rom.comment('human readable form e.g. not as a comment in an HTML file.')
    rom.comment('')
    rom.comment('Referfence manual and more information is currently maintained here:')
    rom.comment('http://retro.hansotten.nl/6502-sbc/lee-davison-web-site/enhanced-6502-basic/')
    rom.comment('')
    rom.comment('The source code and build tools for this distribution is here:')
    rom.comment('https://github.com/picocomputer/ehbasic')
    rom.comment('')
    rom.comment('The original website went down after Lee passed away on September 21, 2013.')
    rom.comment('The Internet Archive Wayback Machine has a snapshot from March 8, 2013:')
    rom.comment('http://mycorner.no-ip.org/6502/ehbasic/index.html')
    rom.binary_file('a.out')

    mon=Monitor('/dev/ttyACM0')
    mon.send_break()
    mon.upload('basic.rp6502', rom)
