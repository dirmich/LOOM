#!/usr/bin/env python3
"""
전체 SCUMM v3 오브젝트 PNG 변환
"""
import json
from pathlib import Path

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️  PIL 필요: pip3 install Pillow")
    exit(1)


# EGA 16색 팔레트
EGA_PALETTE = [
    (0x00, 0x00, 0x00),  # 0: Black
    (0x00, 0x00, 0xAA),  # 1: Blue
    (0x00, 0xAA, 0x00),  # 2: Green
    (0x00, 0xAA, 0xAA),  # 3: Cyan
    (0xAA, 0x00, 0x00),  # 4: Red
    (0xAA, 0x00, 0xAA),  # 5: Magenta
    (0xAA, 0x55, 0x00),  # 6: Brown
    (0xAA, 0xAA, 0xAA),  # 7: Light Gray
    (0x55, 0x55, 0x55),  # 8: Dark Gray
    (0x55, 0x55, 0xFF),  # 9: Light Blue
    (0x55, 0xFF, 0x55),  # 10: Light Green
    (0x55, 0xFF, 0xFF),  # 11: Light Cyan
    (0xFF, 0x55, 0x55),  # 12: Light Red
    (0xFF, 0x55, 0xFF),  # 13: Light Magenta
    (0xFF, 0xFF, 0x55),  # 14: Yellow
    (0xFF, 0xFF, 0xFF),  # 15: White
]


def xor_decrypt(data):
    """XOR 0xFF 복호화"""
    return bytearray([b ^ 0xFF for b in data])


def decode_strip_ega(data, pixels, strip_x, width, height):
    """ScummVM drawStripEGA 구현"""
    if len(data) == 0:
        return

    dst = [[0 for _ in range(8)] for _ in range(height)]

    color = 0
    run = 0
    x = 0
    y = 0
    offset = 0

    while x < 8 and offset < len(data):
        color = data[offset]
        offset += 1

        if color & 0x80:  # RLE mode
            run = color & 0x3F

            if color & 0x40:  # Two-color dithering
                if offset >= len(data):
                    break
                color = data[offset]
                offset += 1

                if run == 0:
                    if offset >= len(data):
                        break
                    run = data[offset]
                    offset += 1

                for z in range(run):
                    if x >= 8:
                        break
                    if y < height:
                        pixel_color = (color & 0xF) if (z & 1) else (color >> 4)
                        dst[y][x] = pixel_color

                    y += 1
                    if y >= height:
                        y = 0
                        x += 1

            else:  # Repeat previous pixel
                if run == 0:
                    if offset >= len(data):
                        break
                    run = data[offset]
                    offset += 1

                for z in range(run):
                    if x >= 8:
                        break
                    if y < height:
                        if x > 0:
                            dst[y][x] = dst[y][x - 1]
                        else:
                            dst[y][x] = 0

                    y += 1
                    if y >= height:
                        y = 0
                        x += 1

        else:  # Single color run
            run = color >> 4
            if run == 0:
                if offset >= len(data):
                    break
                run = data[offset]
                offset += 1

            pixel_color = color & 0xF
            for z in range(run):
                if x >= 8:
                    break
                if y < height:
                    dst[y][x] = pixel_color

                y += 1
                if y >= height:
                    y = 0
                    x += 1

    # Copy to main buffer
    for row in range(height):
        for col in range(8):
            pixel_x = strip_x + col
            if pixel_x < width:
                pixel_index = row * width + pixel_x
                if pixel_index < len(pixels):
                    pixels[pixel_index] = dst[row][col]


def decode_object_with_strips(obim_data, default_height=32):
    """Strip offset table 기반 오브젝트 디코딩"""

    if len(obim_data) < 16:
        return None  # Too small

    # 빈 오브젝트 체크
    if len(obim_data) <= 20 and all(b == 0 for b in obim_data[:16]):
        return None

    # GF_SMALL_HEADER: 8바이트 헤더
    header_size = 8
    offset_table_start = header_size

    # Strip offset 읽기
    strip_offsets = []
    ptr = offset_table_start

    # 최대 80개 strip 시도 (640px / 8 = 80)
    for i in range(80):
        if ptr + 1 >= len(obim_data):
            break

        strip_offset = obim_data[ptr] | (obim_data[ptr + 1] << 8)

        # Offset이 0이거나 파일 범위를 벗어나면 끝
        if strip_offset == 0 or strip_offset >= len(obim_data):
            break

        # 감소하는 offset은 테이블 끝
        if i > 0 and strip_offset <= strip_offsets[-1]:
            break

        # 너무 작은 offset (헤더 범위 내)
        if strip_offset < header_size + 2:
            break

        strip_offsets.append(strip_offset)
        ptr += 2

    if len(strip_offsets) == 0:
        return None

    num_strips = len(strip_offsets)
    width = num_strips * 8

    # Height 추정: 크기 기반
    if len(obim_data) > 2000:
        height = 64
    elif len(obim_data) > 500:
        height = 48
    else:
        height = default_height

    # 이미지 디코딩
    pixels = bytearray(width * height)

    # 각 strip 디코딩
    for strip_idx in range(num_strips):
        strip_offset = strip_offsets[strip_idx]

        # Strip 끝 위치
        if strip_idx < num_strips - 1:
            strip_end = strip_offsets[strip_idx + 1]
        else:
            strip_end = len(obim_data)

        strip_data = obim_data[strip_offset:strip_end]

        if len(strip_data) > 0:
            decode_strip_ega(strip_data, pixels, strip_idx * 8, width, height)

    return {
        'width': width,
        'height': height,
        'pixels': bytes(pixels),
        'num_strips': num_strips
    }


def save_as_png(pixels, width, height, output_path):
    """PNG로 저장"""
    img = Image.new('RGB', (width, height))
    rgb_data = []

    for pixel in pixels:
        r, g, b = EGA_PALETTE[pixel & 0x0F]
        rgb_data.extend([r, g, b])

    img.putdata(list(zip(rgb_data[0::3], rgb_data[1::3], rgb_data[2::3])))
    img.save(output_path)


def process_all_objects():
    """전체 오브젝트 처리"""
    # objects_analysis.json 읽기
    with open('analyze/objects_analysis.json', 'r') as f:
        analysis = json.load(f)

    output_dir = Path('objects_png')
    output_dir.mkdir(exist_ok=True)

    print('🎮 전체 SCUMM v3 오브젝트 PNG 변환')
    print('=' * 70)

    stats = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'empty': 0
    }

    all_results = []

    # 각 Room 처리
    for room in analysis['rooms'][:5]:  # 처음 5개 Room만 (테스트)
        room_num = room['room']
        lfl_file = Path(f'{room_num}.LFL')

        if not lfl_file.exists():
            continue

        # LFL 읽기
        with open(lfl_file, 'rb') as f:
            encrypted = f.read()
        room_data = xor_decrypt(encrypted)

        print(f'\n📂 Room {room_num} ({len(room["objects"])}개 오브젝트)')

        room_output = output_dir / f'room_{room_num}'
        room_output.mkdir(exist_ok=True)

        # 각 오브젝트 처리
        for obj in room['objects']:
            stats['total'] += 1
            obj_id = obj['id']
            obim_offset = obj['obim_offset']
            obim_size = obj['obim_size']

            # 빈 오브젝트
            if obim_size == 0:
                stats['empty'] += 1
                continue

            obim_data = room_data[obim_offset:obim_offset + obim_size]

            # 디코딩
            result = decode_object_with_strips(obim_data)

            if result is None:
                stats['failed'] += 1
                continue

            # PNG 저장
            output_path = room_output / f'object_{obj_id:03d}.png'
            save_as_png(result['pixels'], result['width'], result['height'], output_path)

            stats['success'] += 1

            # 진행 상황 (10개마다)
            if stats['success'] % 10 == 0:
                print(f'   ✅ {stats["success"]}개 완료...')

            all_results.append({
                'room': room_num,
                'object_id': obj_id,
                'width': result['width'],
                'height': result['height'],
                'strips': result['num_strips'],
                'file': str(output_path)
            })

    # 결과 출력
    print('\n' + '=' * 70)
    print('✅ 변환 완료!')
    print(f'   총 오브젝트: {stats["total"]}개')
    print(f'   성공: {stats["success"]}개 ({stats["success"]*100//stats["total"] if stats["total"] > 0 else 0}%)')
    print(f'   실패: {stats["failed"]}개')
    print(f'   빈 오브젝트: {stats["empty"]}개')
    print(f'\n   출력: {output_dir.absolute()}/')

    # 결과 JSON 저장
    result_path = Path('analyze/objects_png_results.json')
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump({
            'stats': stats,
            'objects': all_results
        }, f, indent=2, ensure_ascii=False)

    print(f'   결과: {result_path}')


if __name__ == '__main__':
    process_all_objects()
