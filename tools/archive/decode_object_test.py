#!/usr/bin/env python3
"""
SCUMM v3 오브젝트 이미지 디코딩 테스트
ScummVM gfx.cpp의 drawStripEGA() 구현
"""
from pathlib import Path

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️  PIL 필요: pip3 install Pillow")
    exit(1)


# EGA 16색 팔레트 (RGB)
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

    # 8×height 픽셀 스트립 버퍼
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


def decode_object_image(obim_data, width=None, height=None):
    """
    SCUMM v3 OBIM 디코딩

    OBIM 구조 (추정):
    - GF_SMALL_HEADER: [8-byte header] + strip data
    - GF_OLD_BUNDLE: [direct strip data]

    Strip 기반 이미지이므로 width는 8의 배수여야 함
    """
    print(f'\n🔍 OBIM 분석:')
    print(f'   크기: {len(obim_data)} bytes')

    # Hex dump 처음 64바이트
    print(f'   Hex (처음 64바이트):')
    for i in range(0, min(64, len(obim_data)), 16):
        chunk = obim_data[i:i+16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        print(f'   {i:04X}  {hex_str}')

    # Width/Height 추정
    # SCUMM v3는 오브젝트에 width/height 정보가 없을 수 있음
    # 기본값: 8x8 또는 16x16 추정
    if width is None:
        # Strip 개수 추정 (총 크기 / 평균 strip 크기)
        # 평균 strip: ~10-30 bytes
        estimated_strips = max(1, len(obim_data) // 20)
        width = estimated_strips * 8
        width = min(width, 64)  # 최대 64 pixels

    if height is None:
        # 기본 높이
        height = 32

    print(f'   추정 크기: {width}×{height}px')

    # 이미지 디코딩
    pixels = bytearray(width * height)

    # GF_SMALL_HEADER: 8바이트 스킵
    offset = 8 if len(obim_data) > 8 else 0

    # Strip별 디코딩
    num_strips = width // 8
    strip_data = obim_data[offset:]

    # 각 strip 디코딩 (단순화: 전체 데이터를 순차적으로 처리)
    for strip_idx in range(num_strips):
        if len(strip_data) == 0:
            break

        # Strip 크기 추정: 남은 데이터 / 남은 strips
        remaining_strips = num_strips - strip_idx
        strip_size = len(strip_data) // remaining_strips if remaining_strips > 0 else len(strip_data)
        strip_size = min(strip_size, len(strip_data))

        decode_strip_ega(strip_data[:strip_size], pixels, strip_idx * 8, width, height)

        strip_data = strip_data[strip_size:]

    return width, height, bytes(pixels)


def save_as_png(pixels, width, height, output_path):
    """PNG로 저장"""
    # RGB 이미지 생성
    img = Image.new('RGB', (width, height))
    rgb_data = []

    for pixel in pixels:
        r, g, b = EGA_PALETTE[pixel & 0x0F]
        rgb_data.extend([r, g, b])

    img.putdata(list(zip(rgb_data[0::3], rgb_data[1::3], rgb_data[2::3])))
    img.save(output_path)
    return True


def test_object_0():
    """01.LFL Object 0 테스트"""
    # LFL 파일 읽기
    lfl_path = Path('01.LFL')
    with open(lfl_path, 'rb') as f:
        encrypted = f.read()
    data = xor_decrypt(encrypted)

    # Object 0 OBIM 위치: 0x18DE, 크기: 109 bytes
    obim_offset = 0x18DE
    obim_size = 109

    obim_data = data[obim_offset:obim_offset + obim_size]

    print('🎮 SCUMM v3 오브젝트 디코딩 테스트')
    print('=' * 70)
    print(f'LFL: {lfl_path.name}')
    print(f'Object: 0')
    print(f'OBIM: 0x{obim_offset:04X}, {obim_size} bytes')

    # 디코딩
    width, height, pixels = decode_object_image(obim_data)

    # PNG 저장
    output_dir = Path('test_objects')
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / 'object_00.png'

    save_as_png(pixels, width, height, output_path)

    print(f'\n✅ 저장 완료!')
    print(f'   출력: {output_path}')
    print(f'   크기: {width}×{height}px')


if __name__ == '__main__':
    test_object_0()
