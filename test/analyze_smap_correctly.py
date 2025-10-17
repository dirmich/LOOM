#!/usr/bin/env python3
"""
SCUMM v3 (LOOM) SMAP 분석 - small header 포맷
"""

# XOR decrypt
with open('01.LFL', 'rb') as f:
    encrypted = f.read()
decrypted = bytes([b ^ 0xFF for b in encrypted])

print("🔍 SCUMM v3 SMAP 분석 (small header)\n" + "="*60)

# Resource table at 0x0A
resourceTableStart = 0x0A
resourceOffsets = []
for i in range(10):
    pos = resourceTableStart + i * 2
    if pos + 1 >= len(decrypted):
        break
    offset = decrypted[pos] | (decrypted[pos + 1] << 8)
    if offset == 0:
        break
    resourceOffsets.append((i, offset))

print("📦 리소스:")
for i, offset in resourceOffsets:
    print(f"  리소스 {i}: 0x{offset:04X} ({offset})")
print()

# 각 리소스 분석
for i, resource_offset in resourceOffsets:
    print(f"\n🔍 리소스 {i} at 0x{resource_offset:04X}:")

    # Small header: smap_ptr = ptr 직접 사용
    # 16-color: offset = READ_LE_UINT16(smap_ptr + stripnr * 2 + 2)
    smap_ptr = resource_offset

    # 첫 2바이트 확인
    print(f"  첫 2 bytes: 0x{decrypted[smap_ptr]:02X} 0x{decrypted[smap_ptr+1]:02X}")

    # Strip offset 읽기 (offset+2부터 시작)
    strip_offsets = []
    for strip_idx in range(50):  # 최대 50 strips
        offset_pos = smap_ptr + 2 + strip_idx * 2
        if offset_pos + 1 >= len(decrypted):
            break

        strip_offset = decrypted[offset_pos] | (decrypted[offset_pos + 1] << 8)

        # 0이거나 파일 범위 벗어나면 중단
        if strip_offset == 0 or strip_offset >= len(decrypted):
            break

        # SMAP 내부 상대 offset
        abs_offset = smap_ptr + strip_offset
        if abs_offset >= len(decrypted):
            break

        strip_offsets.append((strip_idx, strip_offset, abs_offset))

    if len(strip_offsets) > 0:
        print(f"  ✅ Strip 개수: {len(strip_offsets)}")
        print(f"  첫 5개 strip offset:")
        for strip_idx, rel_offset, abs_offset in strip_offsets[:5]:
            # Strip 데이터 첫 10바이트
            data_sample = decrypted[abs_offset:abs_offset+10]
            hex_str = ' '.join(f'{b:02X}' for b in data_sample)
            print(f"    Strip {strip_idx}: rel=0x{rel_offset:04X} abs=0x{abs_offset:04X} data=[{hex_str}]")

print()
print("="*60)
