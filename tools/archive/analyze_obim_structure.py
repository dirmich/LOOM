#!/usr/bin/env python3
"""
OBIM (Object Image) 구조 분석
ScummVM 소스 분석 결과 기반
"""
import sys
from pathlib import Path


def analyze_obim(filepath):
    """OBIM 파일 구조 분석"""
    data = Path(filepath).read_bytes()
    print(f'📦 파일: {filepath}')
    print(f'   크기: {len(data)} bytes')
    print('=' * 70)

    # Hex dump 처음 256 바이트
    print('\n🔍 Hex Dump (처음 256 바이트):')
    for i in range(0, min(256, len(data)), 16):
        chunk = data[i:i+16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        print(f'{i:04X}  {hex_str:<48}  {ascii_str}')

    # SCUMM v3 구조 분석 (GF_SMALL_HEADER 또는 GF_OLD_BUNDLE)
    print('\n\n📊 구조 분석:')

    # 처음 2-8 바이트는 크기 정보일 가능성
    if len(data) >= 8:
        size_le16 = data[0] | (data[1] << 8)
        size_le32 = data[0] | (data[1] << 8) | (data[2] << 16) | (data[3] << 24)

        print(f'\n   가능한 크기 헤더:')
        print(f'      16-bit LE: {size_le16}')
        print(f'      32-bit LE: {size_le32}')
        print(f'      실제 크기: {len(data)}')

    # 4-char 태그 찾기 (IMHD, IM00-IM0F 등)
    print(f'\n   4-char 태그 검색:')
    tags_found = []
    for i in range(0, len(data) - 3):
        tag = data[i:i+4]
        # ASCII 문자로만 구성된 태그 찾기
        if all(32 <= b < 127 for b in tag):
            tag_str = tag.decode('ascii')
            if tag_str.isupper() or tag_str.startswith('IM'):
                tags_found.append((i, tag_str))

    if tags_found:
        for offset, tag in tags_found[:20]:  # 처음 20개만
            print(f'      [{offset:04X}] {tag}')
    else:
        print(f'      (4-char 태그 없음 - SCUMM v3 GF_OLD_BUNDLE 포맷)')

    # 가능한 이미지 헤더 찾기 (width, height)
    print(f'\n   가능한 이미지 헤더 (width×height):')
    for i in range(0, min(32, len(data) - 4), 2):
        width = data[i] | (data[i+1] << 8)
        height = data[i+2] | (data[i+3] << 8)

        # 합리적인 범위의 width/height
        if 1 <= width <= 320 and 1 <= height <= 200:
            print(f'      [{i:04X}] {width}×{height}')

    print('\n' + '=' * 70)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        # 기본: 작은 파일 하나 분석
        filepath = 'out/graphics/02_res002.bin'
    else:
        filepath = sys.argv[1]

    analyze_obim(filepath)
