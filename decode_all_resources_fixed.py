#!/usr/bin/env python3
"""
LOOM 모든 리소스 디코딩 및 재구성 (개선 버전)
- 이미지: 재구성된 포맷
- 사운드/스크립트/기타: extract_resources.py의 분류 사용
"""
import os
import json
from pathlib import Path


def xor_decrypt(data):
    """XOR 0xFF 복호화"""
    return bytearray([b ^ 0xFF for b in data])


def extract_room_image(room_data):
    """Room에서 배경 이미지 데이터 추출 및 재구성"""
    if len(room_data) < 10:
        return None

    # Room 헤더 파싱
    width = room_data[4] | (room_data[5] << 8)
    height = room_data[6] | (room_data[7] << 8)

    # SMAP = Resource 0 (리소스 테이블 첫 번째)
    resource_table_start = 0x0A
    smap_ptr = room_data[resource_table_start] | (room_data[resource_table_start + 1] << 8)

    if smap_ptr >= len(room_data):
        return None

    # Strip offset 읽기 (16-color: SMAP+2부터)
    strip_offsets = []
    max_strips = min(200, (width + 7) // 8)

    for i in range(max_strips):
        offset_pos = smap_ptr + 2 + i * 2
        if offset_pos + 1 >= len(room_data):
            break

        strip_offset = room_data[offset_pos] | (room_data[offset_pos + 1] << 8)

        # 0이거나 범위 벗어나면 끝
        if strip_offset == 0 or smap_ptr + strip_offset >= len(room_data):
            break

        # SMAP 기준 상대 주소 → 절대 주소
        abs_offset = smap_ptr + strip_offset
        strip_offsets.append(abs_offset)

    if len(strip_offsets) == 0:
        return None

    # 새로운 이미지 데이터 재구성
    header_size = 4  # width + height
    new_table_size = len(strip_offsets) * 2
    total_strip_data_size = 0

    # 각 strip 크기 계산
    strip_sizes = []
    for i in range(len(strip_offsets)):
        strip_start = strip_offsets[i]
        strip_end = strip_offsets[i + 1] if i < len(strip_offsets) - 1 else len(room_data)
        strip_size = strip_end - strip_start
        strip_sizes.append(strip_size)
        total_strip_data_size += strip_size

    # 새 데이터 버퍼 생성
    new_data = bytearray(header_size + new_table_size + total_strip_data_size)

    # Width & height
    new_data[0] = width & 0xFF
    new_data[1] = (width >> 8) & 0xFF
    new_data[2] = height & 0xFF
    new_data[3] = (height >> 8) & 0xFF

    # 새 offset table 작성 (상대 주소, headerSize 기준)
    current_offset = header_size + new_table_size
    for i in range(len(strip_offsets)):
        table_pos = header_size + i * 2
        new_data[table_pos] = current_offset & 0xFF
        new_data[table_pos + 1] = (current_offset >> 8) & 0xFF
        current_offset += strip_sizes[i]

    # Strip 데이터 복사
    write_pos = header_size + new_table_size
    for i in range(len(strip_offsets)):
        strip_start = strip_offsets[i]
        strip_size = strip_sizes[i]
        strip_data = room_data[strip_start:strip_start + strip_size]
        new_data[write_pos:write_pos + strip_size] = strip_data
        write_pos += strip_size

    return bytes(new_data), width, height, len(strip_offsets)


def process_all_rooms():
    """모든 Room 처리 (extract_resources.py 결과 사용)"""
    decoded_dir = Path('decoded2')
    decoded_dir.mkdir(exist_ok=True)

    # out/_summary.json 읽기 (정확한 리소스 분류)
    with open('out/_summary.json', 'r') as f:
        original_summary = json.load(f)

    all_rooms = {}

    # 각 LFL 파일 처리
    for file_info in original_summary['files']:
        room_num_str = file_info['file']
        room_num = int(room_num_str)

        lfl_file = Path(f'{room_num_str}.LFL')
        if not lfl_file.exists():
            continue

        print(f'\n📂 {lfl_file.name} 처리 중...')

        # XOR 복호화
        with open(lfl_file, 'rb') as f:
            encrypted = f.read()
        decrypted = xor_decrypt(encrypted)

        # Room 정보
        width = decrypted[4] | (decrypted[5] << 8)
        height = decrypted[6] | (decrypted[7] << 8)
        print(f'   Room: {width}×{height}px')

        # Room 디렉토리 생성
        room_dir = decoded_dir / f'room_{room_num_str}'
        room_dir.mkdir(exist_ok=True)

        room_info = {
            'room_number': room_num,
            'width': width,
            'height': height,
            'resources': []
        }

        # 배경 이미지 재구성
        try:
            reconstructed, img_width, img_height, num_strips = extract_room_image(decrypted)
            if reconstructed:
                type_dir = room_dir / 'background'
                type_dir.mkdir(exist_ok=True)
                filepath = type_dir / 'background.bin'
                filepath.write_bytes(reconstructed)

                print(f'   ✅ [0] background/background.bin - {len(reconstructed)} bytes (재구성됨: {img_width}×{img_height}, {num_strips} strips)')

                room_info['resources'].append({
                    'id': 0,
                    'type': 'background',
                    'subtype': 'image',
                    'filename': 'background.bin',
                    'path': f'room_{room_num_str}/background/background.bin',
                    'size': len(reconstructed),
                    'width': img_width,
                    'height': img_height,
                    'strips': num_strips,
                    'reconstructed': True
                })
        except Exception as e:
            print(f'   ⚠️  배경 이미지 재구성 실패: {e}')

        # 나머지 리소스 (out/ 디렉토리에서 복사)
        for res in file_info['resources']:
            res_id = res['id']
            res_type = res['type']
            src_path = Path('out') / res['path']

            if not src_path.exists():
                continue

            data = src_path.read_bytes()

            # 타입별 디렉토리
            type_dir = room_dir / res_type
            type_dir.mkdir(exist_ok=True)

            # 파일명 (out/의 파일명 사용)
            filename = src_path.name
            filepath = type_dir / filename
            filepath.write_bytes(data)

            # 타입 이모지
            type_emoji = {
                'graphics': '🎨',
                'sounds': '🔊',
                'scripts': '📜',
                'unknown': '❓'
            }.get(res_type, '📦')

            print(f'   {type_emoji} [{res_id}] {res_type}/{filename} - {len(data)} bytes')

            room_info['resources'].append({
                'id': res_id,
                'type': res_type,
                'filename': filename,
                'path': f'room_{room_num_str}/{res_type}/{filename}',
                'size': len(data),
                'entropy': res['entropy'],
                'reconstructed': False
            })

        all_rooms[room_num_str] = room_info

    return all_rooms


def create_resources_json(all_rooms, output_path):
    """resources.json 생성"""
    # 통계 계산
    total_resources = 0
    type_counts = {
        'background': 0,
        'graphics': 0,
        'sounds': 0,
        'scripts': 0,
        'palettes': 0,
        'unknown': 0
    }

    for room_info in all_rooms.values():
        total_resources += len(room_info['resources'])
        for res in room_info['resources']:
            res_type = res['type']
            if res_type in type_counts:
                type_counts[res_type] += 1

    resources_data = {
        'game': 'LOOM',
        'version': 'SCUMM v3',
        'format': 'decoded',
        'total_rooms': len(all_rooms),
        'total_resources': total_resources,
        'background_images': type_counts['background'],
        'graphics': type_counts['graphics'],
        'sounds': type_counts['sounds'],
        'scripts': type_counts['scripts'],
        'palettes': type_counts['palettes'],
        'unknown': type_counts['unknown'],
        'rooms': []
    }

    # Room 정보 추가
    for room_num, room_info in sorted(all_rooms.items()):
        room_entry = {
            'room': room_num,
            'width': room_info['width'],
            'height': room_info['height'],
            'total_resources': len(room_info['resources']),
            'resources': room_info['resources']
        }
        resources_data['rooms'].append(room_entry)

    # JSON 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(resources_data, f, indent=2, ensure_ascii=False)

    return resources_data


def main():
    print('🎮 LOOM 모든 리소스 디코딩 시작 (개선 버전)')
    print('=' * 70)

    # 모든 Room 처리
    all_rooms = process_all_rooms()

    # resources.json 생성
    print('\n📊 resources.json 생성 중...')
    resources_data = create_resources_json(all_rooms, Path('decoded2/resources.json'))

    # 결과 출력
    print('\n' + '=' * 70)
    print('✅ 디코딩 완료!')
    print(f'   총 Room: {resources_data["total_rooms"]}개')
    print(f'   총 리소스: {resources_data["total_resources"]}개')
    print(f'      🖼️  배경 이미지: {resources_data["background_images"]}개 (재구성됨)')
    print(f'      🎨 그래픽: {resources_data["graphics"]}개')
    print(f'      🔊 사운드: {resources_data["sounds"]}개')
    print(f'      📜 스크립트: {resources_data["scripts"]}개')
    print(f'      ❓ 미분류: {resources_data["unknown"]}개')
    print(f'\n   출력 디렉토리: decoded2/')
    print(f'   리소스 맵: decoded2/resources.json')


if __name__ == '__main__':
    main()
