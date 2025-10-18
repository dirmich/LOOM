#!/usr/bin/env python3
"""
v3 디코더 실패한 16개 오브젝트 상세 분석
"""
import json
from pathlib import Path
from collections import Counter


def xor_decrypt(data):
    """XOR 0xFF 복호화"""
    return bytearray([b ^ 0xFF for b in data])


def analyze_remaining_failures():
    """v3에서 실패한 16개 오브젝트 분석"""

    # objects_analysis.json 읽기 (전체 248개)
    with open('analyze/objects_analysis.json', 'r') as f:
        analysis = json.load(f)

    # objects_png_v3_results.json 읽기 (성공한 111개)
    with open('analyze/objects_png_v3_results.json', 'r') as f:
        v3_results = json.load(f)

    # 성공한 오브젝트 ID 수집
    successful_ids = set()
    for obj in v3_results['objects']:
        successful_ids.add((obj['room'], obj['object_id']))

    print('🔍 v3 디코더 실패한 오브젝트 상세 분석')
    print('=' * 70)
    print(f'\n총 오브젝트: {v3_results["stats"]["total"]}개')
    print(f'성공: {v3_results["stats"]["success"]}개')
    print(f'빈 오브젝트: {v3_results["stats"]["empty"]}개')
    print(f'메타데이터: {v3_results["stats"]["meta"]}개 (19-byte)')
    print(f'실패: {v3_results["stats"]["failed"]}개')

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

            # 19-byte 메타데이터 스킵
            if obim_size == 19:
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

    print(f'\n\n📦 실패한 {len(failed_objects)}개 오브젝트 분석')
    print('=' * 70)

    # 크기별 분포
    print('\n크기별 분포:')
    for size, count in sorted(size_distribution.items()):
        print(f'   {size:5d} bytes: {count:3d}개')

    # 각 실패 오브젝트 상세 분석
    print('\n\n📋 실패 오브젝트 상세 분석')
    print('-' * 70)

    for i, obj in enumerate(failed_objects):
        print(f"\n[{i}] Room {obj['room']}, Object {obj['object_id']} ({obj['size']} bytes)")
        print(f"    Offset: 0x{obj['offset']:04X}")

        data = obj['data']

        # Hex dump (처음 64 bytes)
        print(f"    Hex (처음 64 bytes):")
        for j in range(0, min(64, len(data)), 16):
            chunk = data[j:j+16]
            hex_str = ' '.join(f'{b:02X}' for b in chunk)
            print(f"       {j:04X}  {hex_str}")

        # 여러 헤더 크기로 strip offset 파싱 시도
        print(f"\n    Strip offset 파싱 시도:")

        for header_size in [0, 2, 4, 6, 8, 10, 12]:
            if header_size >= len(data):
                continue

            print(f"       Header {header_size} bytes:")
            offsets = []
            ptr = header_size

            for k in range(10):  # 최대 10개 strip만 확인
                if ptr + 1 >= len(data):
                    break
                offset = data[ptr] | (data[ptr+1] << 8)

                if offset == 0 or offset >= len(data):
                    break
                if offsets and offset <= offsets[-1]:
                    break
                if offset < header_size + 2:
                    break

                offsets.append(offset)
                ptr += 2

            if offsets:
                offset_str = ', '.join(f'0x{o:04X}' for o in offsets[:10])
                print(f"          Offsets: [{offset_str}]")
                print(f"          Count: {len(offsets)} strips")
            else:
                print(f"          ❌ 유효한 offset 없음")

        # 특수 패턴 검사
        print(f"\n    패턴 분석:")

        # 모든 바이트가 0인지
        if all(b == 0 for b in data):
            print(f"       ⚠️  모두 0x00 (빈 데이터)")

        # 반복 패턴
        if len(set(data[:16])) == 1:
            print(f"       ⚠️  반복 패턴: 0x{data[0]:02X}")

        # ASCII 텍스트?
        ascii_count = sum(1 for b in data[:32] if 32 <= b < 127)
        if ascii_count > 24:  # 75% 이상
            ascii_text = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[:32])
            print(f"       💬 ASCII 텍스트 가능성: \"{ascii_text}\"")

    # JSON으로 결과 저장
    result_data = {
        'total_failed': len(failed_objects),
        'size_distribution': dict(size_distribution),
        'failed_objects': [
            {
                'room': obj['room'],
                'object_id': obj['object_id'],
                'size': obj['size'],
                'offset': obj['offset'],
                'hex_preview': obj['data'][:64].hex()
            }
            for obj in failed_objects
        ]
    }

    output_path = Path('analyze/remaining_failures.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)

    print(f'\n\n💾 결과 저장: {output_path}')
    print('=' * 70)


if __name__ == '__main__':
    analyze_remaining_failures()
