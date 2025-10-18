#!/usr/bin/env python3
"""
OBIM에서 IMHD 태그 검색
"""
from pathlib import Path


def xor_decrypt(data):
    """XOR 0xFF 복호화"""
    return bytearray([b ^ 0xFF for b in data])


# LFL 파일 읽기
lfl_path = Path('01.LFL')
with open(lfl_path, 'rb') as f:
    encrypted = f.read()
data = xor_decrypt(encrypted)

# Object 0 OBIM: 0x18DE, 109 bytes
obim_offset = 0x18DE
obim_size = 109
obim_data = data[obim_offset:obim_offset + obim_size]

print('🔍 OBIM에서 IMHD 태그 검색')
print('=' * 70)
print(f'OBIM offset: 0x{obim_offset:04X}')
print(f'OBIM size: {obim_size} bytes')
print()

# IMHD 태그 검색
imhd_tag = b'IMHD'
if imhd_tag in obim_data:
    pos = obim_data.index(imhd_tag)
    print(f'✅ IMHD 태그 발견! offset: {pos}')

    # IMHD 이후 데이터
    imhd_start = pos + 4
    print(f'\nIMHD 헤더 (offset {imhd_start}):')
    for i in range(imhd_start, min(imhd_start + 32, len(obim_data)), 16):
        chunk = obim_data[i:i+16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        print(f'   {i:04X}  {hex_str}')
else:
    print('❌ IMHD 태그 없음 → GF_OLD_BUNDLE 또는 GF_SMALL_HEADER without tags')
    print('\n첫 32 바이트 (ImageHeader 추정):')
    for i in range(0, min(32, len(obim_data)), 16):
        chunk = obim_data[i:i+16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        print(f'   {i:04X}  {hex_str}')

    # ImageHeader 구조로 파싱 시도
    if len(obim_data) >= 18:
        obj_id = obim_data[0] | (obim_data[1] << 8)
        image_count = obim_data[2] | (obim_data[3] << 8)
        width = obim_data[12] | (obim_data[13] << 8)
        height = obim_data[14] | (obim_data[15] << 8)
        hotspot_num = obim_data[16] | (obim_data[17] << 8)

        print(f'\n📊 ImageHeader 파싱 (추정):')
        print(f'   obj_id: {obj_id}')
        print(f'   image_count: {image_count}')
        print(f'   width: {width}')
        print(f'   height: {height}')
        print(f'   hotspot_num: {hotspot_num}')

        # 합리적인 값인지 확인
        if 1 <= width <= 320 and 1 <= height <= 200 and image_count <= 20:
            print(f'\n✅ 합리적인 값! width={width}, height={height}')

            # Image 데이터 시작 위치
            image_data_start = 18 + hotspot_num * 4
            print(f'   Image 데이터 시작: offset {image_data_start}')
        else:
            print(f'\n⚠️  비합리적인 값')

print()
print('=' * 70)

# 다른 큰 오브젝트도 테스트
print('\n📦 Object 52 (4250 bytes) 테스트:')
obim_offset = 0x3233
obim_size = 4250
obim_data = data[obim_offset:obim_offset + obim_size]

if b'IMHD' in obim_data:
    pos = obim_data.index(b'IMHD')
    print(f'✅ IMHD 태그 발견! offset: {pos}')
else:
    print('❌ IMHD 태그 없음')

# GF_SMALL_HEADER일 경우 8바이트 스킵 후 데이터
print('\nGF_SMALL_HEADER 가설 (8바이트 스킵):')
skip_offset = 8
for i in range(skip_offset, min(skip_offset + 32, len(obim_data)), 16):
    chunk = obim_data[i:i+16]
    hex_str = ' '.join(f'{b:02X}' for b in chunk)
    print(f'   {i:04X}  {hex_str}')
