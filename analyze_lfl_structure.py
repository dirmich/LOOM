#!/usr/bin/env python3
"""
LFL 파일 구조 분석 - SMAP chunk 찾기
"""
import struct

# XOR decrypt
with open('01.LFL', 'rb') as f:
    encrypted = f.read()
decrypted = bytes([b ^ 0xFF for b in encrypted])

print("🔍 LFL 파일 구조 분석\n" + "="*60)
print(f"파일 크기: {len(decrypted)} bytes\n")

# Header
print("📋 헤더:")
print(f"  Bytes 0-3: {' '.join(f'{b:02X}' for b in decrypted[0:4])}")
print(f"  Room width: {decrypted[4] | (decrypted[5] << 8)}")
print(f"  Room height: {decrypted[6] | (decrypted[7] << 8)}")
print(f"  Bytes 8-9: {' '.join(f'{b:02X}' for b in decrypted[8:10])}")
print()

# Resource table at 0x0A
print("📦 리소스 테이블 (0x0A부터):")
resourceTableStart = 0x0A
for i in range(10):
    pos = resourceTableStart + i * 2
    if pos + 1 >= len(decrypted):
        break
    offset = decrypted[pos] | (decrypted[pos + 1] << 8)
    if offset == 0:
        break
    print(f"  리소스 {i}: offset 0x{offset:04X} ({offset})")
print()

# Chunk 찾기
print("🔖 Chunk 분석:")
pos = 0
chunk_count = 0
while pos < min(len(decrypted), 2000):
    if pos + 8 > len(decrypted):
        break

    # 4-byte tag 읽기 (big-endian ASCII)
    tag_bytes = decrypted[pos:pos+4]

    # ASCII 문자인지 확인
    try:
        tag = tag_bytes.decode('ascii')
        if all(32 <= b < 127 for b in tag_bytes):
            # Size 읽기 (little-endian)
            size = struct.unpack('<I', decrypted[pos+4:pos+8])[0]

            # 합리적인 크기인지 확인
            if 0 < size < len(decrypted):
                print(f"  Chunk at 0x{pos:04X}: '{tag}' size={size} (0x{size:04X})")

                # SMAP이면 상세 분석
                if tag == 'SMAP':
                    print(f"    ✅ SMAP 발견!")
                    smap_start = pos + 8
                    print(f"    SMAP 데이터 시작: 0x{smap_start:04X}")

                    # 첫 10개 strip offset 읽기 (16-color: offset + 2부터)
                    print(f"    첫 10개 strip offset:")
                    for i in range(10):
                        offset_pos = smap_start + 2 + i * 2
                        if offset_pos + 1 < len(decrypted):
                            strip_offset = decrypted[offset_pos] | (decrypted[offset_pos + 1] << 8)
                            # SMAP 내부 상대 offset
                            abs_offset = smap_start + strip_offset
                            print(f"      Strip {i}: 0x{strip_offset:04X} (절대 0x{abs_offset:04X})")

                chunk_count += 1
                if chunk_count > 20:
                    break

                # 다음 chunk로
                pos += 8 + size
                continue
    except:
        pass

    pos += 1

print()
print("="*60)
