#!/usr/bin/env python3
"""
LFL 파일 구조 정확히 분석
"""
from pathlib import Path

def analyze_lfl(filename):
    """LFL 파일의 실제 구조 분석"""
    # Read and decrypt
    data = Path(filename).read_bytes()
    decrypted = bytes([b ^ 0xFF for b in data])

    print(f"=== {filename} 구조 분석 ===\n")
    print(f"파일 크기: {len(decrypted):,} bytes\n")

    # 첫 32 바이트 헥스 덤프
    print("첫 32 바이트 (헥스):")
    for i in range(0, 32, 16):
        hex_str = ' '.join(f'{b:02x}' for b in decrypted[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in decrypted[i:i+16])
        print(f"  {i:04x}: {hex_str:<48}  {ascii_str}")

    print()

    # 문서에 따르면:
    # 0x00-0x01: Width
    # 0x02-0x03: Height
    # 0x04+: Resource offset table

    width_doc = decrypted[0x00] | (decrypted[0x01] << 8)
    height_doc = decrypted[0x02] | (decrypted[0x03] << 8)

    print("문서 기반 파싱 (0x00부터):")
    print(f"  Width:  0x{width_doc:04x} ({width_doc})")
    print(f"  Height: 0x{height_doc:04x} ({height_doc})")
    print()

    # 서버 코드가 읽는 위치
    width_server = decrypted[0x04] | (decrypted[0x05] << 8)
    height_server = decrypted[0x06] | (decrypted[0x07] << 8)

    print("서버 코드 파싱 (0x04부터):")
    print(f"  Width:  0x{width_server:04x} ({width_server})")
    print(f"  Height: 0x{height_server:04x} ({height_server})")
    print()

    # Resource offset table 읽기 (문서 기반)
    print("Resource offset table (문서 기반, 0x04부터):")
    for i in range(10):
        pos = 0x04 + i * 2
        if pos + 1 >= len(decrypted):
            break
        offset = decrypted[pos] | (decrypted[pos + 1] << 8)
        print(f"  [{i:2d}] @0x{pos:04x}: 0x{offset:04x} ({offset:5d})")

    print()

    # Resource offset table 읽기 (서버 코드 기반)
    print("Resource offset table (서버 코드, 0x0A부터):")
    for i in range(10):
        pos = 0x0A + i * 2
        if pos + 1 >= len(decrypted):
            break
        offset = decrypted[pos] | (decrypted[pos + 1] << 8)
        print(f"  [{i:2d}] @0x{pos:04x}: 0x{offset:04x} ({offset:5d})")

    print()

    # 각 오프셋 위치의 데이터 미리보기
    print("각 리소스 오프셋 위치의 데이터:")
    for i in range(5):
        pos = 0x04 + i * 2
        if pos + 1 >= len(decrypted):
            break
        offset = decrypted[pos] | (decrypted[pos + 1] << 8)
        if offset < len(decrypted):
            preview = ' '.join(f'{b:02x}' for b in decrypted[offset:offset+16])
            print(f"  Offset 0x{offset:04x}: {preview}")

# Analyze room files
for room_num in [1, 2, 3]:
    filename = f'{room_num:02d}.LFL'
    if Path(filename).exists():
        analyze_lfl(filename)
        print("\n" + "="*60 + "\n")
