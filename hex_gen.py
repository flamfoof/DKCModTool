"""
Hex patch file generator for the Connect Mod Installer.
Generates .hex files compatible with the existing mod installer format.

.hex format (little endian):
  8 bytes: Starting offset
  8 bytes: Size of data
  X bytes: Data to write at the offset
  ... repeat ...
"""
import struct
import os


class HexPatch:
    """Represents a single hex edit (offset + data)."""
    
    def __init__(self, offset, data, description=""):
        self.offset = offset
        self.data = data if isinstance(data, bytes) else bytes(data)
        self.description = description
    
    def __repr__(self):
        hex_str = ' '.join(f'{b:02X}' for b in self.data[:16])
        if len(self.data) > 16:
            hex_str += " ..."
        return f"HexPatch(0x{self.offset:X}, {len(self.data)} bytes: {hex_str}) [{self.description}]"


class HexGenerator:
    """Generates .hex patch files from a list of edits."""
    
    def __init__(self):
        self.patches = []
    
    def add_patch(self, offset, data, description=""):
        self.patches.append(HexPatch(offset, data, description))
    
    def add_byte_patch(self, offset, value, description=""):
        self.patches.append(HexPatch(offset, bytes([value & 0xFF]), description))
    
    def add_uint16_patch(self, offset, value, description=""):
        self.patches.append(HexPatch(offset, struct.pack('<H', value), description))
    
    def add_uint32_patch(self, offset, value, description=""):
        self.patches.append(HexPatch(offset, struct.pack('<I', value), description))
    
    def add_string_patch(self, offset, text, pad_to=0, description=""):
        encoded = text.encode('ascii')
        if pad_to > 0:
            encoded = encoded[:pad_to]
            encoded = encoded + b'\x00' * (pad_to - len(encoded))
        self.patches.append(HexPatch(offset, encoded, description))
    
    def generate(self, output_path):
        """Write patches to a .hex file in the mod installer format.
        Note: Despite docs saying 'little endian', the actual format uses big-endian
        for the 8-byte offset and size fields."""
        with open(output_path, 'wb') as f:
            for patch in self.patches:
                f.write(struct.pack('>Q', patch.offset))
                f.write(struct.pack('>Q', len(patch.data)))
                f.write(patch.data)
        print(f"[+] Generated {output_path} with {len(self.patches)} patches")
        return output_path
    
    def generate_changelog(self, output_path=None):
        """Generate a human-readable changelog of all patches."""
        lines = []
        for patch in self.patches:
            hex_str = ' '.join(f'{patch.data[i]:02X}' for i in range(len(patch.data)))
            desc = f" // {patch.description}" if patch.description else ""
            lines.append(f"{{ 0x{patch.offset:X} = {hex_str} }}{desc}")
        text = '\n'.join(lines)
        if output_path:
            with open(output_path, 'w') as f:
                f.write(text)
        return text
    
    @staticmethod
    def read_hex_file(filepath):
        """Read and parse an existing .hex file."""
        patches = []
        with open(filepath, 'rb') as f:
            data = f.read()
        pos = 0
        while pos < len(data):
            if pos + 16 > len(data):
                break
            offset = struct.unpack_from('>Q', data, pos)[0]
            pos += 8
            size = struct.unpack_from('>Q', data, pos)[0]
            pos += 8
            if pos + size > len(data):
                break
            patch_data = data[pos:pos+size]
            pos += size
            patches.append(HexPatch(offset, patch_data))
        return patches
    
    @staticmethod
    def describe_hex_file(filepath):
        """Return a human-readable description of a .hex file."""
        patches = HexGenerator.read_hex_file(filepath)
        lines = [f"=== {os.path.basename(filepath)} ({len(patches)} patches) ==="]
        for i, p in enumerate(patches):
            hex_str = ' '.join(f'{b:02X}' for b in p.data[:32])
            if len(p.data) > 32:
                hex_str += " ..."
            lines.append(f"  [{i}] Offset 0x{p.offset:X}, {len(p.data)} bytes: {hex_str}")
        return '\n'.join(lines)


def diff_to_hex(original_path, modified_path, output_path, description=""):
    """Compare two binary files and generate a .hex patch file with the differences."""
    with open(original_path, 'rb') as f:
        original = f.read()
    with open(modified_path, 'rb') as f:
        modified = f.read()
    
    gen = HexGenerator()
    min_len = min(len(original), len(modified))
    
    # Find contiguous diff regions
    i = 0
    while i < min_len:
        if original[i] != modified[i]:
            start = i
            while i < min_len and original[i] != modified[i]:
                i += 1
            diff_data = modified[start:i]
            gen.add_patch(start, diff_data, description)
        else:
            i += 1
    
    # Handle size difference (modified is larger)
    if len(modified) > len(original):
        gen.add_patch(len(original), modified[len(original):], "appended data")
    
    if gen.patches:
        gen.generate(output_path)
        print(f"[+] Found {len(gen.patches)} difference regions")
    else:
        print("[*] Files are identical, no patches generated")
    
    return gen
