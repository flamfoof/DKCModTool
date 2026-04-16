"""Apply .hex patch files to a binary file."""
import sys
import struct
import os

def apply_hex_file(target_path, hex_path):
    """Read a .hex patch file and apply it to the target binary."""
    with open(target_path, 'rb') as f:
        data = bytearray(f.read())

    with open(hex_path, 'rb') as f:
        hex_data = f.read()

    patches_applied = 0
    pos = 0
    while pos < len(hex_data):
        if pos + 16 > len(hex_data):
            break
        offset = struct.unpack_from('>Q', hex_data, pos)[0]
        pos += 8
        size = struct.unpack_from('>Q', hex_data, pos)[0]
        pos += 8
        if pos + size > len(hex_data):
            print(f"[ERROR] Truncated patch at offset 0x{offset:X}")
            break
        patch_data = hex_data[pos:pos + size]
        pos += size

        if offset + size > len(data):
            print(f"[ERROR] Patch at 0x{offset:X} ({size} bytes) exceeds file size ({len(data)} bytes)")
            return False

        old_bytes = ' '.join(f'{b:02X}' for b in data[offset:offset + size])
        new_bytes = ' '.join(f'{b:02X}' for b in patch_data)
        print(f"  [PATCH] 0x{offset:X}: {old_bytes} -> {new_bytes}")
        data[offset:offset + size] = patch_data
        patches_applied += 1

    with open(target_path, 'wb') as f:
        f.write(data)

    print(f"[+] Applied {patches_applied} patches to {os.path.basename(target_path)}")
    return True

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: hex_apply.py <target_file> <hex_patch_file> [hex_patch_file2 ...]")
        sys.exit(1)

    target = sys.argv[1]
    for hex_file in sys.argv[2:]:
        print(f"Applying {os.path.basename(hex_file)}...")
        if not apply_hex_file(target, hex_file):
            sys.exit(1)
