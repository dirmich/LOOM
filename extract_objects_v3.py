#!/usr/bin/env python3
"""
SCUMM v3 오브젝트 추출
ScummVM object.cpp의 ScummEngine_v3old::resetRoomObjects() 구현
"""
import json
from pathlib import Path


def xor_decrypt(data):
    """XOR 0xFF 복호화"""
    return bytearray([b ^ 0xFF for b in data])


def extract_objects_from_room(lfl_path):
    """SCUMM v3 Room에서 오브젝트 추출"""
    # LFL 파일 읽기 및 복호화
    with open(lfl_path, 'rb') as f:
        encrypted = f.read()
    data = xor_decrypt(encrypted)

    # Room 헤더 파싱
    if len(data) < 32:
        return None

    width = data[4] | (data[5] << 8)
    height = data[6] | (data[7] << 8)

    print(f'\n📂 {lfl_path.name}')
    print(f'   Room: {width}×{height}px')

    # SCUMM v3: 오브젝트 테이블은 offset 29부터 시작
    # ScummVM object.cpp line 920-921
    obj_table_offset = 29

    # 먼저 오브젝트 개수를 알아야 함
    # Resource table에서 추정
    resource_table_start = 0x0A

    # Resource 0 (SMAP) offset 읽기
    smap_offset = data[resource_table_start] | (data[resource_table_start + 1] << 8)

    # 오브젝트 테이블은 29 ~ smap_offset 사이
    # 각 오브젝트: 2 bytes (OBIM offset) + 나중에 2 bytes (OBCD offset)
    # 총 테이블 크기를 4로 나누면 오브젝트 개수

    # 더 정확한 방법: offset 29에서 시작해서 offset들을 읽어봄
    ptr = obj_table_offset
    obim_offsets = []
    obcd_offsets = []

    # 최대 200개까지 시도
    for i in range(200):
        if ptr + 1 >= len(data):
            break

        offset = data[ptr] | (data[ptr + 1] << 8)

        # Offset이 0이거나 파일 범위를 벗어나면 끝
        if offset == 0 or offset >= len(data):
            break

        obim_offsets.append(offset)
        ptr += 2

    num_objects = len(obim_offsets)

    if num_objects == 0:
        print('   ⚠️  오브젝트 없음')
        return None

    # OBCD offsets 읽기
    for i in range(num_objects):
        if ptr + 1 >= len(data):
            break
        offset = data[ptr] | (data[ptr + 1] << 8)
        obcd_offsets.append(offset)
        ptr += 2

    print(f'   오브젝트 개수: {num_objects}개')

    # 각 오브젝트 분석
    objects = []
    for i in range(num_objects):
        obim_offset = obim_offsets[i]
        obcd_offset = obcd_offsets[i] if i < len(obcd_offsets) else 0

        obj_info = {
            'id': i,
            'obim_offset': obim_offset,
            'obcd_offset': obcd_offset,
        }

        # OBIM 데이터 크기 추정
        if i < num_objects - 1:
            # 다음 OBIM 또는 첫 OBCD까지
            next_offset = obim_offsets[i + 1] if i + 1 < len(obim_offsets) else obcd_offsets[0]
            obim_size = next_offset - obim_offset
        else:
            # 마지막 오브젝트: OBCD까지
            obim_size = obcd_offset - obim_offset if obcd_offset > obim_offset else 100

        # OBIM 데이터 추출
        if obim_offset < len(data):
            obim_data = data[obim_offset:obim_offset + obim_size]
            obj_info['obim_size'] = len(obim_data)

            # OBIM 구조 간단 분석
            # SCUMM v3 GF_OLD_BUNDLE: 헤더 없이 바로 이미지 데이터
            # GF_SMALL_HEADER: 8바이트 헤더

            print(f'   [{i}] OBIM@{obim_offset:04X} ({len(obim_data)} bytes), OBCD@{obcd_offset:04X}')

        objects.append(obj_info)

    return {
        'room': lfl_path.stem,
        'width': width,
        'height': height,
        'num_objects': num_objects,
        'objects': objects
    }


def main():
    """모든 Room 처리"""
    print('🎮 SCUMM v3 오브젝트 추출')
    print('=' * 70)

    lfl_files = sorted(Path('.').glob('*.LFL'))

    all_rooms = []
    total_objects = 0

    for lfl_file in lfl_files[:5]:  # 처음 5개만 테스트
        room_info = extract_objects_from_room(lfl_file)
        if room_info:
            all_rooms.append(room_info)
            total_objects += room_info['num_objects']

    # 결과 출력
    print('\n' + '=' * 70)
    print(f'✅ 분석 완료!')
    print(f'   Rooms: {len(all_rooms)}개')
    print(f'   총 오브젝트: {total_objects}개')

    # JSON 저장
    output_path = Path('analyze/objects_analysis.json')
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'total_rooms': len(all_rooms),
            'total_objects': total_objects,
            'rooms': all_rooms
        }, f, indent=2, ensure_ascii=False)

    print(f'   출력: {output_path}')


if __name__ == '__main__':
    main()
