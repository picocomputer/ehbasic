# Example for controlling RP6502 RIA via UART

import sys,io,subprocess,serial,binascii

class Serial:
    def __init__(self, name, timeout=0.2):
        self.out = serial.Serial()
        self.out.setPort(name)
        self.out.timeout = timeout
        self.out.open()

    def send_break(self, duration=0.01):
        ''' Stop the 6502 and return to monitor. '''
        self.out.read_all()
        self.out.send_break(duration)
        bytes = self.out.read_until(']')
        if bytes[-1:] != b']':
            sys.exit('Failed to break')

    def write(self, str):
        ''' Send anything. Does not read reply. '''
        self.out.write(bytes(str, 'utf-8'))

    def basic_command(self, str):
        ''' Send one line using "0\b" faux flow control. '''
        self.out.write(b'0')
        while True:
            r = self.out.read()
            if r == b'\x00': # huh, zeros?
                continue
            if r == b'0':
                break
            sys.exit("Error")
        self.out.write(b'\b')
        self.out.write(bytes(str, 'utf-8'))
        self.out.write(b'\r')
        self.out.read_until()

    def wait_for_basic_ready(self):
        ''' Wait for BASIC Ready. '''
        while True:
            #TODO timeout
            if b'Ready\r\n' == self.out.readline():
                break

    def monitor_command(self, str):
        ''' Send one line and wait for next monitor prompt '''
        self.out.write(bytes(str, 'utf-8'))
        self.out.write(b'\r')
        while True:
            r = self.out.read()
            if r == b'?':
                print(']'+str)
                sys.exit('?'+self.out.read_until().decode('utf-8').strip())
            if r == b']':
                break
            if r == '':
                sys.exit('Timeout')

    def send_binary(self, addr, data):
        ''' Send data to memory using fast BINARY command. '''
        command = f'BINARY ${addr:04X} ${len(data):04X} ${binascii.crc32(data):08X}\r'
        self.out.write(bytes(command, 'utf-8'))
        self.out.write(data)
        while True:
            r = self.out.read()
            if r == b'?':
                print(']'+command)
                print('?'+self.out.read_until().decode('utf-8').strip())
                sys.exit("Error")
            if r == b']':
                break

    def reset_vector(self, addr=None):
        ''' Set reset vector. Use start address of last file as default. '''
        if addr == None:
            addr = self.reset_vector_guess
        if addr == None:
            sys.exit("Reset vector not set")
        self.send_binary(0xFFFC, bytearray([addr & 0xFF, addr >> 8]))

    def send_file_to_memory(self, name, addr=None):
        ''' Send binary file. addr=None uses first two bytes as address.'''
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
            self.send_binary(addr, data[pos:pos+size])
            addr += size
            pos += size

    def upload(self, name, readable):
        ''' Upload readable (file,rom,etc) to remote file "name" '''
        data = readable.read()
        #TODO
        # print(data)


class ROM:
    def __init__(self):
        self.out = io.BytesIO(b'')

    def read(self):
        self.out.seek(0)
        return self.out.read()

    def caps(self, val):
        ''' Use CAPS mode for this ROM. '''
        self.out.write(bytes(f'CAPS\n', 'utf-8'))

    def phi2(self, khz):
        ''' Set PHI2 in khz. '''
        self.out.write(bytes(f'PHI2 {khz}\n', 'utf-8'))

    def reset(self):
        ''' Start the 6502. '''
        self.out.write(bytes(f'RESET\n', 'utf-8'))

    def binary(self, addr, data):
        ''' Send data to memory using fast BINARY command. '''
        command = f'BINARY ${addr:04X} ${len(data):04X} ${binascii.crc32(data):08X}\n'
        self.out.write(bytes(command, 'utf-8'))
        self.out.write(data)

    def binary_file(self, name, addr=None):
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

    def reset_vector(self, addr=None):
        ''' Set reset vector. Use start address of last file as default. '''
        if addr == None:
            addr = self.reset_vector_guess
        if addr == None:
            sys.exit("Reset vector not set")
        self.binary(0xFFFC, bytearray([addr & 0xFF, addr >> 8]))

### Above should be importable module one day

def run(args) -> subprocess.CompletedProcess:
    ''' Run a system process. For example, a compiler. '''
    cp = subprocess.run(args)
    if cp.returncode != 0:
        sys.exit(cp.returncode)

run(['64tass', '--mw65c02', 'min_mon.asm'])

# ser=Serial('/dev/ttyACM0')
# ser.send_break()
# ser.send_file_to_memory('a.out')
# ser.monitor_command('start')
# ser.write('C')
# ser.write('\r')
# ser.wait_for_basic_ready()
# ser.basic_command('10 PRINT "Hello, World!"')
# ser.basic_command('RUN')

rom=ROM()
rom.binary_file('a.out')
rom.reset()

ser=Serial('/dev/ttyACM0')
ser.upload('basic.rp6502', rom)
