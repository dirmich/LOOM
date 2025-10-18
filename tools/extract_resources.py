#!/usr/bin/env python3
"""
LOOM LFL 파일에서 리소스 추출
브라우저 뷰어에서 사용할 수 있도록 out/ 디렉토리에 추출
"""
import os
import struct
import json
import math
from pathlib import Path
from collections import Counter

def xor_decrypt(data):
    """XOR 0xFF 복호화"""
    return bytearray([b ^ 0xFF for b in data])

def calculate_entropy(data):
    """엔트로피 계산 (0.0 ~ 1.0)"""
    if len(data) == 0:
        return 0.0

    counter = Counter(data)
    entropy = 0.0
    for count in counter.values():
        p = count / len(data)
        if p > 0:
            entropy -= p * math.log2(p)

    # 0-8 범위를 0-1로 정규화
    max_entropy = 8.0
    return min(entropy / max_entropy, 1.0)

def classify_resource(data, entropy):
    """리소스 타입 분류"""
    size = len(data)

    # 엔트로피 기반 분류
    if entropy < 0.3:
        return 'scripts'  # 낮은 엔트로피 = 스크립트/텍스트
    elif size > 1000 and entropy > 0.7:
        return 'graphics'  # 큰 크기 + 높은 엔트로피 = 그래픽
    elif size < 2000 and entropy > 0.6:
        return 'sounds'    # 작은 크기 + 중간 엔트로피 = 사운드
    elif size < 100:
        return 'palettes'  # 매우 작음 = 팔레트
    else:
        return 'unknown'

def find_block_boundaries(data):
    """블록 경계 찾기 (휴리스틱)"""
    blocks = []
    i = 0

    while i < len(data) - 100:
        # 의미있는 데이터가 시작되는 지점 찾기
        # 연속된 0이 아닌 바이트가 많은 구간
        non_zero_count = sum(1 for b in data[i:i+50] if b != 0)

        if non_zero_count > 30:  # 50바이트 중 30개 이상이 non-zero
            # 블록 크기 추정
            block_end = i + 100

            # 다음 0 패턴이나 다른 블록 시작까지 읽기
            for j in range(i + 100, min(i + 60000, len(data))):
                # 연속된 0이 10개 이상이면 블록 끝으로 간주
                if all(data[k] == 0 for k in range(j, min(j + 10, len(data)))):
                    block_end = j
                    break

            block_size = block_end - i
            if block_size >= 100:  # 최소 100 bytes
                blocks.append((i, block_size))
                i = block_end
                continue

        i += 1

    return blocks

def extract_lfl_resources(lfl_path, output_base):
    """LFL 파일에서 리소스 추출"""
    lfl_num = Path(lfl_path).stem

    with open(lfl_path, 'rb') as f:
        encrypted_data = f.read()

    # XOR 복호화
    data = xor_decrypt(encrypted_data)

    print(f"\n📂 {lfl_path} 처리 중...")
    print(f"   파일 크기: {len(data):,} bytes")

    # 블록 경계 찾기
    blocks = find_block_boundaries(data)
    print(f"   발견된 블록: {len(blocks)}개")

    resources = []

    for idx, (offset, size) in enumerate(blocks, 1):
        block_data = bytes(data[offset:offset + size])

        # 엔트로피 계산
        entropy = calculate_entropy(block_data)

        # 타입 분류
        res_type = classify_resource(block_data, entropy)

        # 파일 저장
        filename = f"{lfl_num}_res{idx:03d}.bin"
        type_dir = output_base / res_type
        type_dir.mkdir(parents=True, exist_ok=True)

        filepath = type_dir / filename
        filepath.write_bytes(block_data)

        resources.append({
            'id': idx,
            'offset': offset,
            'size': size,
            'type': res_type,
            'entropy': f"{entropy:.3f}",
            'filename': filename,
            'path': f"{res_type}/{filename}"
        })

        print(f"   [{idx:3d}] {filename:20s} {size:8,} bytes  entropy={entropy:.3f}  type={res_type}")

    return resources

def create_summary(all_files_data, output_base):
    """summary.json 생성"""
    summary = {
        'game': 'LOOM',
        'version': 'SCUMM v3',
        'total_files': len(all_files_data),
        'total_resources': 0,
        'graphics': 0,
        'sounds': 0,
        'scripts': 0,
        'palettes': 0,
        'unknown': 0,
        'files': []
    }

    for file_num, resources in sorted(all_files_data.items()):
        type_counts = {
            'graphics': 0,
            'sounds': 0,
            'scripts': 0,
            'palettes': 0,
            'unknown': 0
        }

        for res in resources:
            type_counts[res['type']] += 1

        file_info = {
            'file': file_num,
            'total': len(resources),
            'graphics': type_counts['graphics'],
            'sounds': type_counts['sounds'],
            'scripts': type_counts['scripts'],
            'palettes': type_counts['palettes'],
            'unknown': type_counts['unknown'],
            'resources': resources
        }

        summary['files'].append(file_info)
        summary['total_resources'] += len(resources)
        summary['graphics'] += type_counts['graphics']
        summary['sounds'] += type_counts['sounds']
        summary['scripts'] += type_counts['scripts']
        summary['palettes'] += type_counts['palettes']
        summary['unknown'] += type_counts['unknown']

    # JSON 저장
    summary_path = output_base / '_summary.json'
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    return summary

def main():
    print("🎮 LOOM 리소스 추출기")
    print("=" * 60)

    # 출력 디렉토리
    output_base = Path('out')

    # 기존 out 디렉토리 확인
    if output_base.exists():
        print(f"\n⚠️  기존 out/ 디렉토리 발견")
        response = input("   삭제하고 다시 추출할까요? (y/n): ").strip().lower()
        if response == 'y':
            import shutil
            shutil.rmtree(output_base)
            print("   ✅ 기존 디렉토리 삭제됨")
        else:
            print("   ❌ 추출 취소")
            return

    output_base.mkdir(exist_ok=True)

    # LFL 파일 찾기
    lfl_files = sorted(Path('.').glob('*.LFL'))

    if not lfl_files:
        print("\n❌ LFL 파일을 찾을 수 없습니다!")
        print("   현재 디렉토리에 *.LFL 파일이 있는지 확인하세요.")
        return

    print(f"\n📁 {len(lfl_files)}개 LFL 파일 발견")

    # 각 LFL 파일 처리
    all_files_data = {}

    for lfl_file in lfl_files:
        resources = extract_lfl_resources(lfl_file, output_base)
        all_files_data[lfl_file.stem] = resources

    # Summary 생성
    print(f"\n📊 Summary 생성 중...")
    summary = create_summary(all_files_data, output_base)

    # 결과 출력
    print("\n" + "=" * 60)
    print("✅ 추출 완료!")
    print(f"   총 파일: {summary['total_files']}개")
    print(f"   총 리소스: {summary['total_resources']}개")
    print(f"      🖼️  그래픽: {summary['graphics']}개")
    print(f"      🔊 사운드: {summary['sounds']}개")
    print(f"      📜 스크립트: {summary['scripts']}개")
    print(f"      🎨 팔레트: {summary['palettes']}개")
    print(f"      ❓ 미분류: {summary['unknown']}개")
    print(f"\n   출력 디렉토리: {output_base.absolute()}")
    print(f"   Summary: {output_base / '_summary.json'}")
    print("\n🚀 이제 'cd tools && bun run serve'로 서버를 실행하세요!")

if __name__ == '__main__':
    main()
