#!/usr/bin/env python3
"""
스크립트 디스어셈블 상태 확인
"""
import json
from pathlib import Path


def check_scripts():
    """스크립트 디스어셈블 상태 확인"""

    # resources.json 읽기
    with open('decoded2/resources.json', 'r') as f:
        resources = json.load(f)

    print('📜 스크립트 디스어셈블 상태 확인')
    print('=' * 70)

    total_scripts = 0
    success = 0
    failed = []

    for room in resources['rooms']:
        room_num = room['room']
        scripts = [r for r in room['resources'] if r['type'] == 'scripts']

        if not scripts:
            continue

        for script in scripts:
            total_scripts += 1

            # 원본 파일
            src_path = Path('decoded2') / script['path'].replace('room_', 'room_')

            # 디스어셈블된 파일
            output_name = script['filename'].replace('.bin', '.txt')
            output_path = Path('disassembled') / f'room_{room_num}' / output_name

            if output_path.exists():
                success += 1
            else:
                failed.append({
                    'room': room_num,
                    'filename': script['filename'],
                    'path': str(src_path),
                    'size': script['size']
                })

    print(f'\n총 스크립트: {total_scripts}개')
    print(f'성공: {success}개 ({success*100//total_scripts}%)')
    print(f'실패: {len(failed)}개\n')

    if failed:
        print('실패한 스크립트:')
        print('-' * 70)
        for f in failed:
            print(f"  Room {f['room']:>2s} | {f['filename']:20s} | {f['size']:6d} bytes")

        # 실패 원인 분석
        print('\n\n🔍 실패 원인 분석:')
        print('-' * 70)

        for f in failed:
            src_path = Path(f['path'])

            print(f"\n{f['filename']}:")

            if not src_path.exists():
                print(f'   ❌ 원본 파일 없음: {src_path}')
                continue

            # 파일 읽기
            with open(src_path, 'rb') as fp:
                data = fp.read()

            # 처음 64 bytes 확인
            print(f'   크기: {len(data)} bytes')
            print(f'   Hex (처음 32 bytes):')
            hex_str = ' '.join(f'{b:02X}' for b in data[:32])
            print(f'      {hex_str}')

            # SCUMM 스크립트 헤더 확인
            if len(data) < 8:
                print(f'   ⚠️  너무 작음 (< 8 bytes)')
                continue

            # LE 16-bit size
            size = data[0] | (data[1] << 8)
            print(f'   헤더 크기: {size}')

            if size != len(data):
                print(f'   ⚠️  크기 불일치: 헤더={size}, 실제={len(data)}')

    print('\n' + '=' * 70)


if __name__ == '__main__':
    check_scripts()
