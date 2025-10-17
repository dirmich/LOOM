#!/usr/bin/env python3
"""
LFL 모든 리소스 추출 (수정)
"""
from pathlib import Path

def extract_resources(lfl_file):
    """모든 리소스 추출"""
    # XOR decrypt
    with open(lfl_file, 'rb') as f:
        encrypted = f.read()
    decrypted = bytes([b ^ 0xFF for b in encrypted])

    print(f"🎮 {lfl_file}")
    print(f"  크기: {len(decrypted)} bytes")

    # Room info
    width = decrypted[4] | (decrypted[5] << 8)
    height = decrypted[6] | (decrypted[7] << 8)
    print(f"  Room: {width}×{height}\n")

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
        resourceOffsets.append((i, offset))

    # 중복 제거 및 정렬
    unique_offsets = {}
    for idx, offset in resourceOffsets:
        if offset not in unique_offsets:
            unique_offsets[offset] = []
        unique_offsets[offset].append(idx)

    sorted_offsets = sorted(unique_offsets.items())

    # Analyze each unique resource
    output_dir = Path('resources') / Path(lfl_file).stem
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, (offset, indices) in enumerate(sorted_offsets):
        next_offset = sorted_offsets[i + 1][0] if i < len(sorted_offsets) - 1 else len(decrypted)
        size = next_offset - offset
        resource_data = decrypted[offset:next_offset]

        # 첫 20바이트
        header_hex = ' '.join(f'{b:02X}' for b in resource_data[:min(20, len(resource_data))])

        # Resource type 추측
        if indices[0] == 0:
            res_type = "SMAP (배경 이미지)"
        elif size > 10000:
            res_type = "큰 데이터 (스크립트/이미지/사운드?)"
        elif size > 1000:
            res_type = "중간 데이터 (오브젝트/코스튬?)"
        else:
            res_type = "작은 데이터 (메타데이터?)"

        idx_str = ','.join(str(idx) for idx in indices)
        print(f"  리소스 [{idx_str}] at 0x{offset:04X}:")
        print(f"    크기: {size:6} bytes | {res_type}")
        print(f"    헤더: {header_hex[:60]}")

        # 저장
        for idx in indices:
            output_file = output_dir / f'resource_{idx:02d}.bin'
            with open(output_file, 'wb') as f:
                f.write(resource_data)

    print(f"\n  ✅ 저장: resources/{Path(lfl_file).stem}/\n")

# Room 01-05만 분석
for i in range(1, 6):
    lfl = f'{i:02d}.LFL'
    if Path(lfl).exists():
        print("="*70)
        extract_resources(lfl)

print("="*70)
print("✅ 완료")
