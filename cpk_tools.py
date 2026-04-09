"""
CRI CPK archive reader/writer for Dokapon Kingdom: Connect.
Implements the minimum CRI UTF table parsing and CPK file replacement
needed for asset mod installation.

CPK Structure:
  - "CPK " header at 0x00, UTF table at 0x10 (metadata: TocOffset, ContentOffset, etc.)
  - "TOC " section at TocOffset, UTF table at TocOffset+0x10 (file listing)
  - File data at ContentOffset + per-file FileOffset
"""
import struct
import os
import copy


# ============================================================================
# CRI UTF Table Parser
# ============================================================================

# Data type constants (low nibble of column flags)
TYPE_UINT8  = 0x00
TYPE_INT8   = 0x01
TYPE_UINT16 = 0x02
TYPE_INT16  = 0x03
TYPE_UINT32 = 0x04
TYPE_INT32  = 0x05
TYPE_UINT64 = 0x06
TYPE_INT64  = 0x07
TYPE_FLOAT  = 0x08
TYPE_DOUBLE = 0x09
TYPE_STRING = 0x0A
TYPE_DATA   = 0x0B

# Storage type constants (high nibble of column flags)
STORAGE_ZERO     = 0x10  # always zero / not stored
STORAGE_CONSTANT = 0x30  # same value for all rows, stored after column def
STORAGE_PERROW   = 0x50  # per-row data

DATA_TYPE_SIZES = {
    TYPE_UINT8: 1, TYPE_INT8: 1,
    TYPE_UINT16: 2, TYPE_INT16: 2,
    TYPE_UINT32: 4, TYPE_INT32: 4,
    TYPE_UINT64: 8, TYPE_INT64: 8,
    TYPE_FLOAT: 4, TYPE_DOUBLE: 8,
    TYPE_STRING: 4,  # uint32 offset into string table
    TYPE_DATA: 8,    # uint32 offset + uint32 size
}


# ============================================================================
# CRI UTF Encryption / Decryption
# ============================================================================

def cri_decrypt(data, xor_init=0x5F, xor_mult=0x15):
    """Decrypt CRI UTF table data using multiplicative XOR cipher."""
    result = bytearray(len(data))
    xor = xor_init
    for i in range(len(data)):
        result[i] = data[i] ^ xor
        xor = (xor * xor_mult) & 0xFF
    return bytes(result)


def cri_encrypt(data, xor_init=0x5F, xor_mult=0x15):
    """Encrypt CRI UTF table data. Same as decrypt (XOR is symmetric)."""
    return cri_decrypt(data, xor_init, xor_mult)


def is_utf_encrypted(data, offset=0):
    """Check if UTF table data at the given offset is encrypted (not starting with @UTF)."""
    if offset + 4 > len(data):
        return False
    return data[offset:offset+4] != b'@UTF'


class UTFColumn:
    def __init__(self, flags, name, constant_value=None, constant_offset=None):
        self.flags = flags
        self.name = name
        self.storage_type = flags & 0xF0
        self.data_type = flags & 0x0F
        self.constant_value = constant_value
        self.constant_offset = constant_offset  # absolute file offset of constant value


class UTFTable:
    """Parser for CRI's @UTF binary table format."""
    
    def __init__(self, data, base_offset=0):
        self.data = data
        self.base_offset = base_offset
        self.columns = []
        self.rows = []
        self._row_field_offsets = []  # Track byte positions for modification
        self._parse()
    
    def _read_u8(self, off):
        return self.data[off]
    
    def _read_u16(self, off):
        return struct.unpack_from('>H', self.data, off)[0]
    
    def _read_u32(self, off):
        return struct.unpack_from('>I', self.data, off)[0]
    
    def _read_u64(self, off):
        return struct.unpack_from('>Q', self.data, off)[0]
    
    def _read_float(self, off):
        return struct.unpack_from('>f', self.data, off)[0]
    
    def _read_double(self, off):
        return struct.unpack_from('>d', self.data, off)[0]
    
    def _read_string(self, string_table_off, str_off):
        start = string_table_off + str_off
        end = self.data.index(0, start)
        return self.data[start:end].decode('utf-8', errors='replace')
    
    def _read_value(self, off, data_type, string_table_off, data_section_off):
        if data_type == TYPE_UINT8:
            return self._read_u8(off), 1
        elif data_type == TYPE_INT8:
            return struct.unpack_from('>b', self.data, off)[0], 1
        elif data_type == TYPE_UINT16:
            return self._read_u16(off), 2
        elif data_type == TYPE_INT16:
            return struct.unpack_from('>h', self.data, off)[0], 2
        elif data_type == TYPE_UINT32:
            return self._read_u32(off), 4
        elif data_type == TYPE_INT32:
            return struct.unpack_from('>i', self.data, off)[0], 4
        elif data_type == TYPE_UINT64:
            return self._read_u64(off), 8
        elif data_type == TYPE_INT64:
            return struct.unpack_from('>q', self.data, off)[0], 8
        elif data_type == TYPE_FLOAT:
            return self._read_float(off), 4
        elif data_type == TYPE_DOUBLE:
            return self._read_double(off), 8
        elif data_type == TYPE_STRING:
            str_off = self._read_u32(off)
            return self._read_string(string_table_off, str_off), 4
        elif data_type == TYPE_DATA:
            data_off = self._read_u32(off)
            data_size = self._read_u32(off + 4)
            abs_off = data_section_off + data_off
            return {"offset": abs_off, "size": data_size}, 8
        return None, 0
    
    def _parse(self):
        off = self.base_offset
        
        magic = self.data[off:off+4]
        if magic != b'@UTF':
            raise ValueError(f"Not a UTF table at offset 0x{off:X}: {magic}")
        
        table_size = self._read_u32(off + 4)
        table_start = off + 8  # data begins after magic + size
        
        rows_offset = self._read_u32(table_start + 0)
        string_offset = self._read_u32(table_start + 4)
        data_offset = self._read_u32(table_start + 8)
        # All offsets are relative to table_start
        
        self.table_name_offset = self._read_u32(table_start + 12)
        num_columns = self._read_u16(table_start + 16)
        self.row_length = self._read_u16(table_start + 18)
        num_rows = self._read_u32(table_start + 20)
        
        self.abs_rows_offset = table_start + rows_offset
        self.abs_string_offset = table_start + string_offset
        self.abs_data_offset = table_start + data_offset
        self.table_name = self._read_string(self.abs_string_offset, self.table_name_offset)
        
        # Parse column definitions
        col_off = table_start + 24
        self.columns = []
        for _ in range(num_columns):
            flags = self._read_u8(col_off)
            col_off += 1
            
            name_off = self._read_u32(col_off)
            col_off += 4
            name = self._read_string(self.abs_string_offset, name_off)
            
            storage = flags & 0xF0
            dtype = flags & 0x0F
            
            constant_value = None
            constant_abs_offset = None
            if storage == STORAGE_CONSTANT:
                constant_abs_offset = col_off
                constant_value, size = self._read_value(
                    col_off, dtype, self.abs_string_offset, self.abs_data_offset
                )
                col_off += size
            
            self.columns.append(UTFColumn(flags, name, constant_value, constant_abs_offset))
        
        # Parse rows
        self.rows = []
        self._row_field_offsets = []
        for r in range(num_rows):
            row = {}
            field_offsets = {}
            row_off = self.abs_rows_offset + r * self.row_length
            cur_off = row_off
            
            for col in self.columns:
                if col.storage_type == STORAGE_ZERO:
                    row[col.name] = 0 if col.data_type < TYPE_STRING else None
                elif col.storage_type == STORAGE_CONSTANT:
                    row[col.name] = col.constant_value
                elif col.storage_type == STORAGE_PERROW:
                    field_offsets[col.name] = cur_off  # Track position
                    val, size = self._read_value(
                        cur_off, col.data_type, self.abs_string_offset, self.abs_data_offset
                    )
                    row[col.name] = val
                    cur_off += size
            
            self.rows.append(row)
            self._row_field_offsets.append(field_offsets)
    
    def get_field_offset(self, row_idx, field_name):
        """Get the absolute byte offset of a field value in a specific row."""
        if row_idx < len(self._row_field_offsets):
            return self._row_field_offsets[row_idx].get(field_name)
        return None


# ============================================================================
# CPK File Handler
# ============================================================================

class CPKFile:
    """Reader/writer for CRI CPK archive files.
    Handles encrypted UTF tables (Dokapon Kingdom Connect uses XOR cipher)."""
    
    def __init__(self, filepath):
        self.filepath = filepath
        self.filesize = os.path.getsize(filepath)
        self.encrypted = False
        
        with open(filepath, 'rb') as f:
            self.header_data = bytearray(f.read(min(self.filesize, 0x100000)))
        
        self._parse_header()
        self._parse_toc()
    
    def _decrypt_utf_region(self, data, utf_offset):
        """Decrypt a UTF table region in-place if encrypted."""
        if is_utf_encrypted(data, utf_offset):
            self.encrypted = True
            # Decrypt from utf_offset to end of UTF table
            # First decrypt 8 bytes to get magic + table_size
            header = cri_decrypt(bytes(data[utf_offset:utf_offset+8]))
            if header[0:4] != b'@UTF':
                raise ValueError(f"Decryption failed at 0x{utf_offset:X}")
            table_size = struct.unpack_from('>I', header, 4)[0]
            # Decrypt the full UTF table (magic + size + table_data)
            total_size = 8 + table_size
            decrypted = cri_decrypt(bytes(data[utf_offset:utf_offset+total_size]))
            data[utf_offset:utf_offset+total_size] = decrypted
            return total_size
        return 0
    
    def _parse_header(self):
        """Parse the CPK header to get metadata."""
        magic = self.header_data[0:4]
        if magic != b'CPK ':
            raise ValueError(f"Not a CPK file: {self.filepath}")
        
        # UTF table starts at offset 0x10, may be encrypted
        self._decrypt_utf_region(self.header_data, 0x10)
        self.header_table = UTFTable(self.header_data, 0x10)
        
        if not self.header_table.rows:
            raise ValueError("CPK header has no rows")
        
        header = self.header_table.rows[0]
        self.toc_offset = header.get('TocOffset', 0)
        self.content_offset = header.get('ContentOffset', 0)
        self.file_count = header.get('Files', 0)
        self.align = header.get('Align', 2048)
        self.toc_size = header.get('TocSize', 0)
        
        # If ContentOffset is 0, files are relative to TocOffset
        if self.content_offset == 0:
            self.content_offset = self.toc_offset
    
    def _parse_toc(self):
        """Parse the TOC to build the file listing."""
        if self.toc_offset == 0:
            self.toc_table = None
            self.files = []
            return
        
        # Read TOC data
        toc_read_size = min(self.toc_size + 0x100 if self.toc_size else 0x200000, 
                           self.filesize - self.toc_offset)
        
        with open(self.filepath, 'rb') as f:
            f.seek(self.toc_offset)
            toc_data = bytearray(f.read(toc_read_size))
        
        # Verify TOC magic
        if toc_data[0:4] != b'TOC ':
            raise ValueError(f"Invalid TOC at offset 0x{self.toc_offset:X}")
        
        # UTF table at toc_offset + 0x10, may be encrypted
        self._decrypt_utf_region(toc_data, 0x10)
        self.toc_raw = toc_data
        self.toc_table = UTFTable(toc_data, 0x10)
        
        # Build file list
        self.files = []
        for i, row in enumerate(self.toc_table.rows):
            dir_name = row.get('DirName', '') or ''
            file_name = row.get('FileName', '') or ''
            file_size = row.get('FileSize', 0) or 0
            extract_size = row.get('ExtractSize', 0) or 0
            file_offset = row.get('FileOffset', 0) or 0
            
            if dir_name:
                full_path = f"{dir_name}/{file_name}"
            else:
                full_path = file_name
            
            # Absolute offset in the CPK file
            abs_offset = self.content_offset + file_offset
            
            self.files.append({
                'index': i,
                'dir': dir_name,
                'name': file_name,
                'path': full_path,
                'file_size': file_size,
                'extract_size': extract_size,
                'file_offset': file_offset,
                'abs_offset': abs_offset,
            })
    
    def list_files(self):
        """Return list of all files in the archive."""
        return self.files
    
    def find_file(self, filename):
        """Find a file entry by name (case-insensitive, matches filename only)."""
        filename_lower = filename.lower()
        for f in self.files:
            if f['name'].lower() == filename_lower:
                return f
            if f['path'].lower() == filename_lower:
                return f
        return None
    
    def extract_file(self, entry, output_path):
        """Extract a single file from the archive."""
        with open(self.filepath, 'rb') as f:
            f.seek(entry['abs_offset'])
            data = f.read(entry['file_size'])
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(data)
        return len(data)
    
    def replace_file(self, filename, new_data_path):
        """
        Replace a file in the CPK archive.
        
        Strategy:
        - If new file <= old file size: overwrite in place
        - If new file > old file size: append to end of CPK, update offset
        
        Updates the TOC in the file, re-encrypting if the original was encrypted.
        Returns True on success, False if file not found.
        """
        entry = self.find_file(filename)
        if entry is None:
            return False
        
        with open(new_data_path, 'rb') as f:
            new_data = f.read()
        
        new_size = len(new_data)
        old_size = entry['file_size']
        row_idx = entry['index']
        
        # We need to read the TOC, modify it (decrypted), then re-encrypt and write back
        with open(self.filepath, 'r+b') as f:
            if new_size <= old_size:
                # Overwrite file data in place
                f.seek(entry['abs_offset'])
                f.write(new_data)
                if new_size < old_size:
                    f.write(b'\x00' * (old_size - new_size))
            else:
                # Append file data to end of CPK
                f.seek(0, 2)
                current_pos = f.tell()
                aligned_pos = ((current_pos + self.align - 1) // self.align) * self.align
                if aligned_pos > current_pos:
                    f.write(b'\x00' * (aligned_pos - current_pos))
                
                new_abs_offset = f.tell()
                f.write(new_data)
                
                new_file_offset = new_abs_offset - self.content_offset
                entry['file_offset'] = new_file_offset
                entry['abs_offset'] = new_abs_offset
                
                # Update FileOffset in decrypted TOC data
                self._update_toc_field(row_idx, 'FileOffset', new_file_offset)
            
            # Update FileSize and ExtractSize in decrypted TOC data
            self._update_toc_field(row_idx, 'FileSize', new_size)
            self._update_toc_field(row_idx, 'ExtractSize', new_size)
            
            # Write the updated TOC back (re-encrypting if needed)
            self._write_toc(f)
        
        entry['file_size'] = new_size
        entry['extract_size'] = new_size
        return True
    
    def _update_toc_field(self, row_idx, field_name, value):
        """Update a field value in the decrypted TOC data buffer."""
        off = self.toc_table.get_field_offset(row_idx, field_name)
        if off is None:
            return
        col = self._find_column(field_name)
        if col is None:
            return
        if col.data_type == TYPE_UINT32:
            struct.pack_into('>I', self.toc_raw, off, value)
        elif col.data_type == TYPE_UINT64:
            struct.pack_into('>Q', self.toc_raw, off, value)
        elif col.data_type == TYPE_UINT16:
            struct.pack_into('>H', self.toc_raw, off, value)
    
    def _write_toc(self, f):
        """Write the (possibly modified) TOC back to the file, re-encrypting if needed."""
        toc_to_write = bytearray(self.toc_raw)
        
        if self.encrypted:
            # Re-encrypt the UTF table portion (starts at offset 0x10 within TOC)
            # Get the UTF table size from the decrypted data
            table_size = struct.unpack_from('>I', toc_to_write, 0x14)[0]
            total_utf_size = 8 + table_size  # @UTF magic + size field + table data
            utf_region = bytes(toc_to_write[0x10:0x10+total_utf_size])
            encrypted = cri_encrypt(utf_region)
            toc_to_write[0x10:0x10+total_utf_size] = encrypted
        
        f.seek(self.toc_offset)
        f.write(toc_to_write)
    
    def _find_column(self, name):
        """Find a TOC column definition by name."""
        if self.toc_table:
            for col in self.toc_table.columns:
                if col.name == name:
                    return col
        return None
    
    def __repr__(self):
        return (f"CPKFile({self.filepath}, {len(self.files)} files, "
                f"TocOffset=0x{self.toc_offset:X}, ContentOffset=0x{self.content_offset:X})")
