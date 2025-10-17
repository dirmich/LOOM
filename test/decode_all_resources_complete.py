#!/usr/bin/env python3
"""
LOOM 모든 리소스 디코딩 및 재구성
- 이미지: 재구성된 포맷 (width, height, strip offset table, strip data)
- 사운드/스크립트/기타: 원본 데이터 그대로
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


def extract_all_resources(room_data):
    """Room의 모든 리소스 추출"""
    if len(room_data) < 10:
        return []

    width = room_data[4] | (room_data[5] << 8)
    height = room_data[6] | (room_data[7] << 8)

    # 리소스 테이블 읽기
    resource_table_start = 0x0A
    resource_offsets = []

    for i in range(50):  # 최대 50개 리소스
        pos = resource_table_start + i * 2
        if pos + 1 >= len(room_data):
            break
        offset = room_data[pos] | (room_data[pos + 1] << 8)
        if offset == 0:
            break
        resource_offsets.append((i, offset))

    # 중복 제거 (같은 offset을 가리키는 리소스들)
    unique_offsets = {}
    for idx, offset in resource_offsets:
        if offset not in unique_offsets:
            unique_offsets[offset] = []
        unique_offsets[offset].append(idx)

    sorted_offsets = sorted(unique_offsets.items())

    resources = []
    for i, (offset, indices) in enumerate(sorted_offsets):
        next_offset = sorted_offsets[i + 1][0] if i < len(sorted_offsets) - 1 else len(room_data)
        size = next_offset - offset
        resource_data = bytes(room_data[offset:next_offset])

        # 리소스 타입 추정
        if indices[0] == 0:
            res_type = 'background'
            res_subtype = 'image'
        elif size > 1000:
            res_type = 'graphics'
            res_subtype = 'object' if indices[0] > 0 and indices[0] < 10 else 'image'
        elif size > 100 and size < 1000:
            # 엔트로피 간단 체크
            non_zero = sum(1 for b in resource_data[:100] if b != 0)
            if non_zero > 60:
                res_type = 'sounds'
                res_subtype = 'pcm'
            else:
                res_type = 'scripts'
                res_subtype = 'bytecode'
        else:
            res_type = 'unknown'
            res_subtype = 'data'

        resources.append({
            'indices': indices,
            'offset': offset,
            'size': size,
            'type': res_type,
            'subtype': res_subtype,
            'data': resource_data
        })

    return resources, width, height


def process_all_rooms():
    """모든 Room 처리"""
    decoded_dir = Path('decoded')
    decoded_dir.mkdir(exist_ok=True)

    all_rooms = {}

    # LFL 파일 찾기 (01-99)
    for room_num in range(1, 100):
        lfl_file = Path(f'{room_num:02d}.LFL')
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
        room_dir = decoded_dir / f'room_{room_num:02d}'
        room_dir.mkdir(exist_ok=True)

        # 모든 리소스 추출
        resources, room_width, room_height = extract_all_resources(decrypted)
        print(f'   리소스: {len(resources)}개 발견')

        room_info = {
            'room_number': room_num,
            'width': room_width,
            'height': room_height,
            'resources': []
        }

        # 각 리소스 처리
        for res in resources:
            res_type = res['type']
            res_subtype = res['subtype']

            # 타입별 디렉토리
            type_dir = room_dir / res_type
            type_dir.mkdir(exist_ok=True)

            # 파일명
            if res['indices'][0] == 0:
                # 배경 이미지 - 재구성
                filename = 'background.bin'
                try:
                    reconstructed, img_width, img_height, num_strips = extract_room_image(decrypted)
                    if reconstructed:
                        filepath = type_dir / filename
                        filepath.write_bytes(reconstructed)
                        print(f'   ✅ [{res["indices"][0]}] {res_type}/{filename} - {len(reconstructed)} bytes (재구성됨: {img_width}×{img_height}, {num_strips} strips)')

                        room_info['resources'].append({
                            'id': res['indices'][0],
                            'type': res_type,
                            'subtype': res_subtype,
                            'filename': filename,
                            'path': f'room_{room_num:02d}/{res_type}/{filename}',
                            'size': len(reconstructed),
                            'original_size': res['size'],
                            'width': img_width,
                            'height': img_height,
                            'strips': num_strips,
                            'reconstructed': True
                        })
                        continue
                except Exception as e:
                    print(f'   ⚠️  배경 이미지 재구성 실패: {e}')

            # 일반 리소스 (원본 그대로 또는 미지원 타입)
            idx_str = '_'.join(str(idx) for idx in res['indices'])
            filename = f'res_{idx_str:0>3s}.bin'

            filepath = type_dir / filename
            filepath.write_bytes(res['data'])

            print(f'   📦 [{idx_str}] {res_type}/{filename} - {res["size"]} bytes')

            room_info['resources'].append({
                'id': res['indices'][0],
                'indices': res['indices'],
                'type': res_type,
                'subtype': res_subtype,
                'filename': filename,
                'path': f'room_{room_num:02d}/{res_type}/{filename}',
                'size': res['size'],
                'reconstructed': False
            })

        all_rooms[f'{room_num:02d}'] = room_info

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
    print('🎮 LOOM 모든 리소스 디코딩 시작')
    print('=' * 70)

    # 모든 Room 처리
    all_rooms = process_all_rooms()

    # resources.json 생성
    print('\n📊 resources.json 생성 중...')
    resources_data = create_resources_json(all_rooms, Path('decoded/resources.json'))

    # 결과 출력
    print('\n' + '=' * 70)
    print('✅ 디코딩 완료!')
    print(f'   총 Room: {resources_data["total_rooms"]}개')
    print(f'   총 리소스: {resources_data["total_resources"]}개')
    print(f'      🖼️  배경 이미지: {resources_data["background_images"]}개 (재구성됨)')
    print(f'      🎨 오브젝트/그래픽: {resources_data["graphics"]}개')
    print(f'      🔊 사운드: {resources_data["sounds"]}개')
    print(f'      📜 스크립트: {resources_data["scripts"]}개')
    print(f'      ❓ 미분류: {resources_data["unknown"]}개')
    print(f'\n   출력 디렉토리: decoded/')
    print(f'   리소스 맵: decoded/resources.json')


if __name__ == '__main__':
    main()
