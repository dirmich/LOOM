#!/usr/bin/env python3
"""
LFL 모든 리소스 추출
"""
from pathlib import Path

def analyze_resource(data, offset, next_offset, idx):
    """리소스 분석"""
    size = next_offset - offset
    resource_data = data[offset:next_offset]

    # 첫 20바이트
    header_hex = ' '.join(f'{b:02X}' for b in resource_data[:min(20, len(resource_data))])

    # ASCII 문자 확인
    ascii_chars = ''
    for b in resource_data[:20]:
        if 32 <= b < 127:
            ascii_chars += chr(b)
        else:
            ascii_chars += '.'

    print(f"\n📦 리소스 {idx}:")
    print(f"  Offset: 0x{offset:04X}")
    print(f"  크기: {size} bytes (0x{size:04X})")
    print(f"  헤더: {header_hex}")
    print(f"  ASCII: {ascii_chars}")

    # 패턴 감지
    if idx == 0:
        print(f"  타입: SMAP (배경 이미지) ✅")
    elif size < 100:
        print(f"  타입: 작은 데이터 (메타데이터?)")
    elif resource_data[:4] == bytes([0x00] * 4):
        print(f"  타입: 0으로 시작 (빈 리소스?)")
    else:
        # 데이터 패턴 분석
        zero_count = sum(1 for b in resource_data[:100] if b == 0)
        if zero_count > 50:
            print(f"  타입: Sparse 데이터 (코드/스크립트?)")
        else:
            print(f"  타입: Dense 데이터 (이미지/사운드?)")

    return resource_data

def extract_resources(lfl_file):
    """모든 리소스 추출"""
    # XOR decrypt
    with open(lfl_file, 'rb') as f:
        encrypted = f.read()
    decrypted = bytes([b ^ 0xFF for b in encrypted])

    print(f"🎮 {lfl_file} 리소스 분석")
    print(f"  파일 크기: {len(decrypted)} bytes")

    # Room info
    width = decrypted[4] | (decrypted[5] << 8)
    height = decrypted[6] | (decrypted[7] << 8)
    print(f"  Room 크기: {width}×{height}")

    # Resource table
    resourceTableStart = 0x0A
    resourceOffsets = []
    for i in range(20):
        pos = resourceTableStart + i * 2
        if pos + 1 >= len(decrypted):
            break
        offset = decrypted[pos] | (decrypted[pos + 1] << 8)
        if offset == 0:
            break
        resourceOffsets.append(offset)

    print(f"  리소스 개수: {len(resourceOffsets)}")

    # Analyze each resource
    resources = []
    for i, offset in enumerate(resourceOffsets):
        next_offset = resourceOffsets[i + 1] if i < len(resourceOffsets) - 1 else len(decrypted)
        resource_data = analyze_resource(decrypted, offset, next_offset, i)
        resources.append(resource_data)

        # 리소스 파일로 저장
        output_dir = Path('resources') / Path(lfl_file).stem
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f'resource_{i:02d}.bin'
        with open(output_file, 'wb') as f:
            f.write(resource_data)

    print(f"\n✅ 리소스 추출 완료: resources/{Path(lfl_file).stem}/")
    return resources

# Room 01-10 분석
for i in range(1, 11):
    lfl = f'{i:02d}.LFL'
    if not Path(lfl).exists():
        continue

    print("\n" + "="*60)
    extract_resources(lfl)
    print()

print("="*60)
print("✅ 모든 리소스 추출 완료")
