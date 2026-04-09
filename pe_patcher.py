"""
PE file parser and patcher for Dokapon Kingdom: Connect DkkStm.exe.
Dynamically reads PE headers to find correct offsets - no hardcoded values.
Replaces the old DKCedit loader functionality.
"""
import struct
import math
import os
import json


class PESection:
    SIZE = 40  # Section header is always 40 bytes
    
    def __init__(self, data, offset):
        self.header_offset = offset
        self.name = data[offset:offset+8].rstrip(b'\x00').decode('ascii', errors='replace')
        self.virtual_size = struct.unpack_from('<I', data, offset + 8)[0]
        self.virtual_address = struct.unpack_from('<I', data, offset + 12)[0]
        self.raw_size = struct.unpack_from('<I', data, offset + 16)[0]
        self.raw_address = struct.unpack_from('<I', data, offset + 20)[0]
        self.reloc_ptr = struct.unpack_from('<I', data, offset + 24)[0]
        self.linenum_ptr = struct.unpack_from('<I', data, offset + 28)[0]
        self.reloc_count = struct.unpack_from('<H', data, offset + 32)[0]
        self.linenum_count = struct.unpack_from('<H', data, offset + 34)[0]
        self.characteristics = struct.unpack_from('<I', data, offset + 36)[0]
    
    def to_dict(self):
        return {
            "name": self.name,
            "virtual_size": f"0x{self.virtual_size:X}",
            "virtual_address": f"0x{self.virtual_address:X}",
            "raw_size": f"0x{self.raw_size:X}",
            "raw_address": f"0x{self.raw_address:X}",
            "characteristics": f"0x{self.characteristics:X}",
        }
    
    def __repr__(self):
        return (f"Section({self.name}, VA=0x{self.virtual_address:X}, "
                f"VS=0x{self.virtual_size:X}, RA=0x{self.raw_address:X}, "
                f"RS=0x{self.raw_size:X})")


class PEPatcher:
    """Dynamic PE patcher that reads headers to determine all offsets."""
    
    MOD_SECTION_NAME = b'.dkcedit'
    MOD_SECTION_CHARS = 0xE0000040  # read/write/execute + initialized data
    
    def __init__(self, filepath):
        self.filepath = filepath
        with open(filepath, 'rb') as f:
            self.data = bytearray(f.read())
        self.file_size = len(self.data)
        self._parse_headers()
    
    def _parse_headers(self):
        # DOS header
        if self.data[0:2] != b'MZ':
            raise ValueError("Not a valid PE file (missing MZ header)")
        self.pe_offset = struct.unpack_from('<I', self.data, 0x3C)[0]
        
        # PE signature
        if self.data[self.pe_offset:self.pe_offset+4] != b'PE\x00\x00':
            raise ValueError("Not a valid PE file (missing PE signature)")
        
        # COFF header
        coff_off = self.pe_offset + 4
        self.machine = struct.unpack_from('<H', self.data, coff_off)[0]
        self.num_sections = struct.unpack_from('<H', self.data, coff_off + 2)[0]
        self.num_sections_offset = coff_off + 2
        self.timestamp = struct.unpack_from('<I', self.data, coff_off + 4)[0]
        self.opt_header_size = struct.unpack_from('<H', self.data, coff_off + 16)[0]
        
        # Optional header
        self.opt_offset = coff_off + 20
        self.opt_magic = struct.unpack_from('<H', self.data, self.opt_offset)[0]
        self.is_pe32plus = (self.opt_magic == 0x20B)
        
        if self.is_pe32plus:
            self.image_base = struct.unpack_from('<Q', self.data, self.opt_offset + 24)[0]
            self.section_alignment = struct.unpack_from('<I', self.data, self.opt_offset + 32)[0]
            self.file_alignment = struct.unpack_from('<I', self.data, self.opt_offset + 36)[0]
            self.image_size_offset = self.opt_offset + 56
            self.image_size = struct.unpack_from('<I', self.data, self.image_size_offset)[0]
            self.headers_size = struct.unpack_from('<I', self.data, self.opt_offset + 60)[0]
        else:
            self.image_base = struct.unpack_from('<I', self.data, self.opt_offset + 28)[0]
            self.section_alignment = struct.unpack_from('<I', self.data, self.opt_offset + 32)[0]
            self.file_alignment = struct.unpack_from('<I', self.data, self.opt_offset + 36)[0]
            self.image_size_offset = self.opt_offset + 56
            self.image_size = struct.unpack_from('<I', self.data, self.image_size_offset)[0]
            self.headers_size = struct.unpack_from('<I', self.data, self.opt_offset + 60)[0]
        
        # Section headers
        self.section_headers_offset = self.opt_offset + self.opt_header_size
        self.sections = []
        for i in range(self.num_sections):
            off = self.section_headers_offset + i * PESection.SIZE
            self.sections.append(PESection(self.data, off))
    
    def _align(self, value, alignment):
        return math.ceil(value / alignment) * alignment
    
    def get_info(self):
        """Return a dictionary of PE file information."""
        last_sec = self.sections[-1]
        last_raw_end = last_sec.raw_address + last_sec.raw_size
        last_virt_end = last_sec.virtual_address + last_sec.virtual_size
        next_virt = self._align(last_virt_end, self.section_alignment)
        
        # Space available for new section header
        headers_end = self.section_headers_offset + self.num_sections * PESection.SIZE
        first_raw = self.sections[0].raw_address
        header_space = first_raw - headers_end
        
        # Check if already modded
        has_dkcedit = any(s.name == '.dkcedit' for s in self.sections)
        
        return {
            "file_path": self.filepath,
            "file_size": self.file_size,
            "pe_type": "PE32+" if self.is_pe32plus else "PE32",
            "image_base": f"0x{self.image_base:X}",
            "section_alignment": f"0x{self.section_alignment:X}",
            "file_alignment": f"0x{self.file_alignment:X}",
            "image_size": f"0x{self.image_size:X}",
            "num_sections": self.num_sections,
            "sections": [s.to_dict() for s in self.sections],
            "next_virtual_address": f"0x{next_virt:X}",
            "next_raw_address": f"0x{last_raw_end:X}",
            "header_space_available": header_space,
            "can_add_section": header_space >= PESection.SIZE,
            "has_dkcedit_section": has_dkcedit,
        }
    
    def is_modded(self):
        """Check if the exe already has a .dkcedit section."""
        return any(s.name == '.dkcedit' for s in self.sections)
    
    def add_mod_section(self, section_size=0x2000):
        """Add the .dkcedit section to the PE file for code injection."""
        if self.is_modded():
            print("[!] File already has a .dkcedit section")
            dkc = next(s for s in self.sections if s.name == '.dkcedit')
            return {
                "virtual_address": dkc.virtual_address,
                "raw_address": dkc.raw_address,
                "virtual_size": dkc.virtual_size,
                "raw_size": dkc.raw_size,
            }
        
        # Check space for new section header
        headers_end = self.section_headers_offset + self.num_sections * PESection.SIZE
        first_raw = self.sections[0].raw_address
        if first_raw - headers_end < PESection.SIZE:
            raise RuntimeError("Not enough space in PE header for a new section")
        
        # Calculate addresses
        last_sec = self.sections[-1]
        last_raw_end = last_sec.raw_address + last_sec.raw_size
        last_virt_end = last_sec.virtual_address + last_sec.virtual_size
        new_virt_addr = self._align(last_virt_end, self.section_alignment)
        new_raw_addr = self._align(last_raw_end, self.file_alignment)
        new_virt_size = self._align(section_size, self.section_alignment)
        new_raw_size = self._align(section_size, self.file_alignment)
        new_image_size = self._align(new_virt_addr + new_virt_size, self.section_alignment)
        
        # 1. Increment section count
        new_count = self.num_sections + 1
        struct.pack_into('<H', self.data, self.num_sections_offset, new_count)
        
        # 2. Write new section header
        new_header_offset = headers_end
        # Name (8 bytes, padded with nulls)
        name_bytes = self.MOD_SECTION_NAME + b'\x00' * (8 - len(self.MOD_SECTION_NAME))
        self.data[new_header_offset:new_header_offset+8] = name_bytes
        struct.pack_into('<I', self.data, new_header_offset + 8, new_virt_size)
        struct.pack_into('<I', self.data, new_header_offset + 12, new_virt_addr)
        struct.pack_into('<I', self.data, new_header_offset + 16, new_raw_size)
        struct.pack_into('<I', self.data, new_header_offset + 20, new_raw_addr)
        struct.pack_into('<I', self.data, new_header_offset + 24, 0)  # reloc ptr
        struct.pack_into('<I', self.data, new_header_offset + 28, 0)  # linenum ptr
        struct.pack_into('<H', self.data, new_header_offset + 32, 0)  # reloc count
        struct.pack_into('<H', self.data, new_header_offset + 34, 0)  # linenum count
        struct.pack_into('<I', self.data, new_header_offset + 36, self.MOD_SECTION_CHARS)
        
        # 3. Update image size
        struct.pack_into('<I', self.data, self.image_size_offset, new_image_size)
        
        # 4. Append section data (zeros + DKCedit marker)
        marker = b'DKCedit: ModSection v2.0'
        section_data = marker + b'\x00' * (new_raw_size - len(marker))
        
        # Pad file to new_raw_addr if needed
        if len(self.data) < new_raw_addr:
            self.data.extend(b'\x00' * (new_raw_addr - len(self.data)))
        
        self.data.extend(section_data[:new_raw_size])
        
        # 5. Write mod space tracker (4 bytes at start of section + marker length)
        mod_start_offset = new_raw_addr + len(marker)
        # Store the amount of space used (initially 0) right after the marker
        space_used_offset = new_raw_addr + len(marker)
        struct.pack_into('<I', self.data, space_used_offset, 0)
        
        # Re-parse headers
        self._parse_headers()
        
        result = {
            "virtual_address": new_virt_addr,
            "raw_address": new_raw_addr,
            "virtual_size": new_virt_size,
            "raw_size": new_raw_size,
            "new_image_size": new_image_size,
            "mod_code_start_raw": new_raw_addr + len(marker) + 4,
            "mod_code_start_virt": new_virt_addr + len(marker) + 4,
            "space_used_offset": space_used_offset,
        }
        
        print(f"[+] Added .dkcedit section:")
        print(f"    Virtual: 0x{new_virt_addr:X} (size: 0x{new_virt_size:X})")
        print(f"    Raw:     0x{new_raw_addr:X} (size: 0x{new_raw_size:X})")
        print(f"    Image:   0x{new_image_size:X}")
        print(f"    Code start (raw):  0x{result['mod_code_start_raw']:X}")
        print(f"    Code start (virt): 0x{result['mod_code_start_virt']:X}")
        
        return result
    
    def get_mod_section_info(self):
        """Get info about the existing .dkcedit section."""
        for s in self.sections:
            if s.name == '.dkcedit':
                marker_len = len(b'DKCedit: ModSection v2.0')
                space_used_offset = s.raw_address + marker_len
                space_used = struct.unpack_from('<I', self.data, space_used_offset)[0]
                code_start_raw = s.raw_address + marker_len + 4
                code_start_virt = s.virtual_address + marker_len + 4
                return {
                    "section": s,
                    "space_used": space_used,
                    "space_used_offset": space_used_offset,
                    "code_start_raw": code_start_raw,
                    "code_start_virt": code_start_virt,
                    "available_space": s.raw_size - marker_len - 4 - space_used,
                    "next_code_raw": code_start_raw + space_used,
                    "next_code_virt": code_start_virt + space_used,
                }
        return None
    
    def inject_mod(self, mod_bin_path, variables_path, functions_path):
        """Inject a compiled mod.bin into the .dkcedit section."""
        if not self.is_modded():
            print("[!] File has not been patched yet. Adding .dkcedit section first...")
            self.add_mod_section()
        
        info = self.get_mod_section_info()
        if info is None:
            raise RuntimeError("Failed to find .dkcedit section")
        
        # Read mod files
        with open(mod_bin_path, 'rb') as f:
            mod_data = f.read()
        
        variables = []
        if os.path.exists(variables_path):
            with open(variables_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        variables.append(int(line, 16))
        
        functions = []
        if os.path.exists(functions_path):
            with open(functions_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        functions.append(int(line, 16))
        
        # Check space
        if len(mod_data) > info["available_space"]:
            raise RuntimeError(
                f"Mod too large: {len(mod_data)} bytes, "
                f"only {info['available_space']} bytes available"
            )
        
        # Write mod code with NOP detection (same logic as old DKCedit loader)
        # Uses explicit index to correctly skip consumed bytes after NOP markers
        file_addr = info["next_code_raw"]
        virt_addr = info["next_code_virt"]
        space_used = info["space_used"]
        var_idx = 0
        func_idx = 0
        
        nop_buffer = [0, 0, 0, 0]
        i = 0
        
        while i < len(mod_data):
            byte = mod_data[i]
            # Shift NOP detection buffer
            nop_buffer = nop_buffer[1:] + [byte]
            
            # Check for NOP RAX (48 0F 1F C0) - function call marker
            if nop_buffer == [0x48, 0x0F, 0x1F, 0xC0]:
                self.data[file_addr] = byte
                file_addr += 1; virt_addr += 1; space_used += 1; i += 1
                
                # Read call/jmp opcode byte
                if i < len(mod_data):
                    self.data[file_addr] = mod_data[i]
                    file_addr += 1; virt_addr += 1; space_used += 1; i += 1
                
                # Write calculated relative offset, skip 4 placeholder bytes
                if func_idx < len(functions):
                    target = functions[func_idx]
                    func_idx += 1
                    call_offset = target - (virt_addr + 4)
                    struct.pack_into('<i', self.data, file_addr, call_offset)
                    file_addr += 4; virt_addr += 4; space_used += 4; i += 4
                
            # Check for NOP RBX (48 0F 1F C3) - variable reference marker
            elif nop_buffer == [0x48, 0x0F, 0x1F, 0xC3]:
                self.data[file_addr] = byte
                file_addr += 1; virt_addr += 1; space_used += 1; i += 1
                
                # Read 3 instruction bytes (mov opcode + register encoding)
                for _ in range(3):
                    if i < len(mod_data):
                        self.data[file_addr] = mod_data[i]
                        file_addr += 1; virt_addr += 1; space_used += 1; i += 1
                
                # Write calculated relative offset, skip 4 placeholder bytes
                if var_idx < len(variables):
                    target = variables[var_idx]
                    var_idx += 1
                    var_offset = target - (virt_addr + 4)
                    struct.pack_into('<i', self.data, file_addr, var_offset)
                    file_addr += 4; virt_addr += 4; space_used += 4; i += 4
                
            # Check for NOP RCX (48 0F 1F C1) - pointer replacement marker
            elif nop_buffer == [0x48, 0x0F, 0x1F, 0xC1]:
                self.data[file_addr] = byte
                file_addr += 1; virt_addr += 1; space_used += 1; i += 1
                
                # Patch the original code location with a jump to our code
                if func_idx + 1 < len(functions):
                    physical_addr = functions[func_idx]
                    func_idx += 1
                    virtual_addr = functions[func_idx]
                    func_idx += 1
                    offset = virt_addr - virtual_addr
                    struct.pack_into('<i', self.data, physical_addr, offset)
                
            else:
                self.data[file_addr] = byte
                file_addr += 1; virt_addr += 1; space_used += 1; i += 1
        
        # Update space used
        struct.pack_into('<I', self.data, info["space_used_offset"], space_used)
        
        print(f"[+] Mod injected: {len(mod_data)} bytes")
        print(f"    Space used: {space_used} / {info['available_space'] + info['space_used']} bytes")
        
        return True
    
    def save(self, filepath=None):
        """Save the modified PE file."""
        filepath = filepath or self.filepath
        with open(filepath, 'wb') as f:
            f.write(self.data)
        print(f"[+] Saved to: {filepath}")
    
    def export_info_json(self, output_path):
        """Export PE info to JSON."""
        info = self.get_info()
        with open(output_path, 'w') as f:
            json.dump(info, f, indent=2)
        return output_path
