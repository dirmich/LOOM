#!/usr/bin/env python3
"""
SCUMM v3 코스튬(Costume) 리소스 찾기
"""
from pathlib import Path


def xor_decrypt(data):
    """XOR 0xFF 복호화"""
    return bytearray([b ^ 0xFF for b in data])


def find_costumes_in_lfl(lfl_path):
    """LFL 파일에서 코스튬 찾기"""

    with open(lfl_path, 'rb') as f:
        encrypted = f.read()

    data = xor_decrypt(encrypted)

    print(f'📂 {lfl_path.name}')
    print(f'   크기: {len(data):,} bytes')

    # Room 헤더 확인
    if len(data) < 10:
        print('   ❌ 너무 작음')
        return

    # SCUMM v3 Room 헤더
    # [0-1]: Room size (LE)
    # [2-3]: Magic? (usually 0x0000 or ignored)
    # [4-5]: Width (LE)
    # [6-7]: Height (LE)
    # [8]: Number of objects (LE)

    room_size = data[0] | (data[1] << 8)
    width = data[4] | (data[5] << 8)
    height = data[6] | (data[7] << 8)
    num_objects = data[8]

    print(f'   Room: {width}×{height}, {num_objects} objects')
    print(f'   Room size in header: {room_size}')

    # Object table은 offset 29에서 시작 (v3)
    # SCUMM v3 resource index는 000.LFL에 있음

    # 00.LFL 특별 처리 (resource index)
    if lfl_path.name == '00.LFL':
        print('\n   🔍 00.LFL은 리소스 인덱스 파일입니다')

        # Version magic number
        magic = data[0] | (data[1] << 8)
        print(f'   Version magic: 0x{magic:04X}')

        # Global objects 읽기 (SCUMM v3: offset 2)
        ptr = 2

        # 글로벌 오브젝트 테이블
        num_global_objects = data[ptr]
        print(f'\n   📦 Global Objects: {num_global_objects}개')
        ptr += 1

        # Global object table 스킵
        # 각 entry: 1 byte (class data)
        ptr += num_global_objects

        # Resource type lists
        # rtRoom, rtCostume, rtScript, rtSound

        resource_types = ['Room', 'Costume', 'Script', 'Sound']

        for rt_name in resource_types:
            if ptr >= len(data):
                break

            # Resource count
            num_resources = data[ptr]
            print(f'\n   📚 {rt_name} Resources: {num_resources}개')
            ptr += 1

            if num_resources == 0:
                continue

            # Room numbers for each resource
            print(f'      Room assignments:')
            for i in range(num_resources):
                if ptr >= len(data):
                    break
                room_num = data[ptr]
                if i < 10 or rt_name == 'Costume':
                    print(f'         {rt_name} {i:3d} → Room {room_num:3d}')
                ptr += 1

            if num_resources > 10 and rt_name != 'Costume':
                print(f'         ... ({num_resources - 10} more)')

            # Offsets for each resource (LE 16-bit in v3!)
            if rt_name == 'Costume':
                print(f'\n      Costume Offsets:')
                for i in range(num_resources):
                    if ptr + 1 >= len(data):
                        break
                    offset = data[ptr] | (data[ptr+1] << 8)
                    if offset == 0xFFFF:
                        print(f'         Costume {i:3d} → INVALID')
                    else:
                        print(f'         Costume {i:3d} → offset 0x{offset:04X}')
                    ptr += 2
            else:
                ptr += num_resources * 2


def main():
    """메인 함수"""
    print('🎭 SCUMM v3 코스튬(Costume) 리소스 찾기')
    print('=' * 70)

    lfl_files = sorted(Path('.').glob('*.LFL'))

    if not lfl_files:
        print('❌ LFL 파일을 찾을 수 없습니다')
        return

    # 00.LFL 먼저 분석 (리소스 인덱스)
    idx_file = Path('00.LFL')
    if idx_file.exists():
        find_costumes_in_lfl(idx_file)

    print('\n' + '=' * 70)


if __name__ == '__main__':
    main()
