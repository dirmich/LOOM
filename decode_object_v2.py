#!/usr/bin/env python3
"""
SCUMM v3 오브젝트 이미지 디코딩 v2
배경 이미지와 유사한 Strip Offset Table 기반 구조
"""
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


def decode_object_with_strips(obim_data, height=32):
    """
    Strip offset table 기반 오브젝트 디코딩

    구조 (추정):
    - GF_SMALL_HEADER: [0-7]: 8-byte header
    - [8+]: Strip offset table (LE 16-bit per strip)
    - Strip data
    """
    print(f'\n🔍 OBIM 분석 (v2 - Strip Table):')
    print(f'   크기: {len(obim_data)} bytes')

    # GF_SMALL_HEADER: 8바이트 스킵
    header_size = 8
    offset_table_start = header_size

    # Strip offset 읽기
    strip_offsets = []
    ptr = offset_table_start

    # 최대 40개 strip 시도 (320px / 8 = 40)
    for i in range(40):
        if ptr + 1 >= len(obim_data):
            break

        strip_offset = obim_data[ptr] | (obim_data[ptr + 1] << 8)

        # Offset이 0이거나 파일 범위를 벗어나면 끝
        if strip_offset == 0 or strip_offset >= len(obim_data):
            break

        # 너무 작은 offset은 테이블 끝
        if i > 0 and strip_offset <= strip_offsets[-1]:
            break

        strip_offsets.append(strip_offset)
        ptr += 2

    if len(strip_offsets) == 0:
        print(f'   ⚠️  Strip offset table 없음')
        return None, None, None

    num_strips = len(strip_offsets)
    width = num_strips * 8

    print(f'   Strip 개수: {num_strips}')
    print(f'   추정 크기: {width}×{height}px')
    print(f'   Strip offsets: {[f"0x{o:04X}" for o in strip_offsets[:5]]}...')

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

    return width, height, bytes(pixels)


def save_as_png(pixels, width, height, output_path):
    """PNG로 저장"""
    img = Image.new('RGB', (width, height))
    rgb_data = []

    for pixel in pixels:
        r, g, b = EGA_PALETTE[pixel & 0x0F]
        rgb_data.extend([r, g, b])

    img.putdata(list(zip(rgb_data[0::3], rgb_data[1::3], rgb_data[2::3])))
    img.save(output_path)
    return True


def test_multiple_objects():
    """여러 오브젝트 테스트"""
    lfl_path = Path('01.LFL')
    with open(lfl_path, 'rb') as f:
        encrypted = f.read()
    data = xor_decrypt(encrypted)

    output_dir = Path('test_objects_v2')
    output_dir.mkdir(exist_ok=True)

    # 테스트할 오브젝트들 (크기가 다양한 것들)
    test_objects = [
        (0, 0x18DE, 109, 32),    # Object 0 - 작음
        (1, 0x194B, 120, 32),    # Object 1
        (9, 0x1DB1, 141, 32),    # Object 9
        (52, 0x3233, 4250, 64),  # Object 52 - 큼
    ]

    print('🎮 SCUMM v3 오브젝트 디코딩 v2 테스트')
    print('=' * 70)

    for obj_id, offset, size, height in test_objects:
        obim_data = data[offset:offset + size]

        print(f'\n📦 Object {obj_id}')
        print(f'   OBIM: 0x{offset:04X}, {size} bytes')

        result = decode_object_with_strips(obim_data, height=height)
        if result[0] is None:
            print(f'   ❌ 디코딩 실패')
            continue

        width, height, pixels = result

        # PNG 저장
        output_path = output_dir / f'object_{obj_id:02d}.png'
        save_as_png(pixels, width, height, output_path)

        print(f'   ✅ 저장: {output_path.name} ({width}×{height}px)')

    print('\n' + '=' * 70)
    print(f'✅ 완료! 출력: {output_dir}/')


if __name__ == '__main__':
    test_multiple_objects()
