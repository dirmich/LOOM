#!/usr/bin/env python3
"""
실패한 오브젝트 패턴 분석
"""
import json
from pathlib import Path
from collections import Counter


def xor_decrypt(data):
    """XOR 0xFF 복호화"""
    return bytearray([b ^ 0xFF for b in data])


def analyze_failed_patterns():
    """실패한 오브젝트 패턴 분석"""
    # objects_analysis.json 읽기
    with open('analyze/objects_analysis.json', 'r') as f:
        analysis = json.load(f)

    # objects_png_results.json 읽기 (성공한 것들)
    with open('analyze/objects_png_results.json', 'r') as f:
        results = json.load(f)

    successful_ids = set()
    for obj in results['objects']:
        successful_ids.add((obj['room'], obj['object_id']))

    print('🔍 실패한 오브젝트 패턴 분석')
    print('=' * 70)

    # 실패한 오브젝트 수집
    failed_objects = []
    size_distribution = Counter()

    for room in analysis['rooms'][:5]:
        room_num = room['room']
        lfl_file = Path(f'{room_num}.LFL')

        if not lfl_file.exists():
            continue

        # LFL 읽기
        with open(lfl_file, 'rb') as f:
            encrypted = f.read()
        room_data = xor_decrypt(encrypted)

        for obj in room['objects']:
            obj_id = obj['id']
            obim_size = obj['obim_size']

            # 빈 오브젝트 스킵
            if obim_size == 0:
                continue

            # 성공한 오브젝트 스킵
            if (room_num, obj_id) in successful_ids:
                continue

            # 실패한 오브젝트
            obim_offset = obj['obim_offset']
            obim_data = room_data[obim_offset:obim_offset + obim_size]

            failed_objects.append({
                'room': room_num,
                'object_id': obj_id,
                'size': obim_size,
                'offset': obim_offset,
                'data': obim_data
            })

            size_distribution[obim_size] += 1

    print(f'\n총 실패 오브젝트: {len(failed_objects)}개')
    print(f'\n크기별 분포 (상위 10개):')
    for size, count in size_distribution.most_common(10):
        print(f'   {size:5d} bytes: {count:3d}개')

    # 19-byte 오브젝트 분석
    print('\n\n📦 19-byte 오브젝트 분석 (처음 5개):')
    print('-' * 70)

    nineteen_byte_objects = [obj for obj in failed_objects if obj['size'] == 19]

    for i, obj in enumerate(nineteen_byte_objects[:5]):
        print(f"\n[{i}] Room {obj['room']}, Object {obj['object_id']}")
        print(f"    Offset: 0x{obj['offset']:04X}")

        # Hex dump
        data = obj['data']
        print(f"    Hex:")
        for j in range(0, len(data), 16):
            chunk = data[j:j+16]
            hex_str = ' '.join(f'{b:02X}' for b in chunk)
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
            print(f"       {j:04X}  {hex_str:<48}  {ascii_str}")

    # 100-200 byte 오브젝트 샘플
    print('\n\n📦 100-200 byte 오브젝트 샘플 (처음 3개):')
    print('-' * 70)

    medium_objects = [obj for obj in failed_objects if 100 <= obj['size'] <= 200]

    for i, obj in enumerate(medium_objects[:3]):
        print(f"\n[{i}] Room {obj['room']}, Object {obj['object_id']}, {obj['size']} bytes")
        print(f"    Offset: 0x{obj['offset']:04X}")

        # Hex dump (처음 64 바이트)
        data = obj['data']
        print(f"    Hex (처음 64 bytes):")
        for j in range(0, min(64, len(data)), 16):
            chunk = data[j:j+16]
            hex_str = ' '.join(f'{b:02X}' for b in chunk)
            print(f"       {j:04X}  {hex_str}")

        # Strip offset table 파싱 시도
        print(f"    Strip offset 파싱 시도 (offset 8):")
        offsets = []
        for j in range(8, min(8 + 20, len(data)), 2):
            offset = data[j] | (data[j+1] << 8)
            if offset == 0 or offset >= len(data):
                break
            if offsets and offset <= offsets[-1]:
                break
            offsets.append(offset)

        if offsets:
            print(f"       발견: {[f'0x{o:04X}' for o in offsets[:10]]}")
        else:
            print(f"       없음 - 다른 구조?")

    print('\n' + '=' * 70)


if __name__ == '__main__':
    analyze_failed_patterns()
