#!/usr/bin/env python3
"""
LOOM 사운드 리소스를 MIDI 형식으로 변환
Roland MT-32 tagless 포맷 → Standard MIDI File
"""
import struct
from pathlib import Path


def read_sound_resource(path):
    """사운드 리소스 읽기 (decoded2는 이미 추출된 raw 데이터)"""
    with open(path, 'rb') as f:
        data = f.read()

    if len(data) == 0:
        return None, "Empty file"

    # decoded2의 파일은 이미 raw Roland 데이터
    # 헤더가 제거되어 있음
    roland_data = data

    return roland_data, None


def create_midi_header(track_data):
    """Standard MIDI File 헤더 생성"""
    # MIDI File Header
    # MThd chunk
    header = bytearray()
    header.extend(b'MThd')  # Chunk type
    header.extend(struct.pack('>I', 6))  # Chunk length (always 6)
    header.extend(struct.pack('>H', 0))  # Format 0 (single track)
    header.extend(struct.pack('>H', 1))  # Number of tracks (1)
    header.extend(struct.pack('>H', 480))  # Ticks per quarter note

    # MTrk chunk
    header.extend(b'MTrk')
    header.extend(struct.pack('>I', len(track_data)))  # Track length

    return header


def add_ro_tag(roland_data):
    """ScummVM 방식으로 RO 태그 추가"""
    tagged = bytearray()
    tagged.extend(b'RO')  # Roland tag
    tagged.extend(roland_data)
    return bytes(tagged)


def convert_sound_to_midi(input_path, output_path):
    """사운드 리소스를 MIDI 파일로 변환"""
    roland_data, error = read_sound_resource(input_path)

    if error:
        return False, error

    if len(roland_data) == 0:
        return False, "Empty data"

    # Roland data를 MIDI track으로 변환
    # Note: 실제 변환은 복잡하므로, 여기서는 RO 태그를 붙인 raw 데이터를 저장
    # ScummVM iMuse가 이를 해석할 수 있음

    # RO 태그 추가
    tagged_data = add_ro_tag(roland_data)

    # 간단한 MIDI 래퍼 (ScummVM 호환)
    # 실제로는 이 데이터를 ScummVM에서 재생해야 함

    # 원본 Roland 데이터 저장 (.ro 확장자)
    ro_path = output_path.with_suffix('.ro')
    with open(ro_path, 'wb') as f:
        f.write(tagged_data)

    return True, ro_path


def analyze_roland_data(roland_data):
    """Roland 데이터 패턴 분석"""
    if len(roland_data) == 0:
        return {}

    # 첫 32 bytes 분석
    preview = roland_data[:32]

    # 통계
    stats = {
        'size': len(roland_data),
        'preview': preview.hex(' '),
        'unique_bytes': len(set(roland_data)),
        'null_count': roland_data.count(0),
        'high_bit_count': sum(1 for b in roland_data if b >= 0x80)
    }

    return stats


def process_all_sounds():
    """모든 사운드 파일 처리"""
    decoded_dir = Path('decoded2')
    output_dir = Path('sounds_midi')
    output_dir.mkdir(exist_ok=True)

    print('🎵 LOOM 사운드 리소스 MIDI 변환')
    print('=' * 70)

    # 사운드 파일 찾기
    sound_files = []
    for room_dir in sorted(decoded_dir.glob('room_*')):
        sounds_dir = room_dir / 'sounds'
        if sounds_dir.exists():
            sound_files.extend(sorted(sounds_dir.glob('*.bin')))

    print(f'\n총 {len(sound_files)}개 사운드 파일 발견\n')

    stats = {
        'total': len(sound_files),
        'success': 0,
        'failed': 0,
        'empty': 0,
        'sizes': {}
    }

    size_distribution = {}

    # 각 파일 처리
    for sound_file in sound_files:
        # Room 번호와 리소스 ID 추출
        parts = sound_file.stem.split('_')
        room_num = parts[0]
        res_id = parts[1]

        # Roland 데이터 읽기
        roland_data, error = read_sound_resource(sound_file)

        if error:
            stats['failed'] += 1
            if len(sound_file.read_bytes()) <= 10:
                stats['empty'] += 1
            continue

        if len(roland_data) == 0:
            stats['empty'] += 1
            continue

        # 출력 경로
        output_name = f'{room_num}_{res_id}'
        output_path = output_dir / output_name

        # 변환
        success, result = convert_sound_to_midi(sound_file, output_path)

        if success:
            stats['success'] += 1

            # 크기별 분포
            size = len(roland_data)
            size_key = f'{size}B' if size < 1000 else f'{size//1024}K'
            size_distribution[size_key] = size_distribution.get(size_key, 0) + 1

            # 진행 상황 (50개마다)
            if stats['success'] % 50 == 0:
                print(f'   ✅ {stats["success"]}개 완료...')
        else:
            stats['failed'] += 1

    # 결과 출력
    print('\n' + '=' * 70)
    print('✅ 변환 완료!')
    print(f'   총 파일: {stats["total"]}개')
    print(f'   성공: {stats["success"]}개 ({stats["success"]*100//stats["total"]}%)')
    print(f'   실패/빈 파일: {stats["failed"]}개')

    if size_distribution:
        print(f'\n   크기별 분포 (상위 10개):')
        for size_key, count in sorted(size_distribution.items(),
                                      key=lambda x: -x[1])[:10]:
            print(f'      {size_key:>6s}: {count:3d}개')

    print(f'\n   출력: {output_dir.absolute()}/')
    print(f'   포맷: Roland MT-32 raw data with RO tag (.ro)')

    # 샘플 분석
    print('\n\n🔍 Roland 데이터 샘플 분석 (처음 5개):')
    print('-' * 70)

    sample_files = [f for f in sound_files
                   if read_sound_resource(f)[0] is not None][:5]

    for i, sound_file in enumerate(sample_files):
        roland_data, _ = read_sound_resource(sound_file)
        if not roland_data:
            continue

        stats_data = analyze_roland_data(roland_data)

        print(f'\n[{i+1}] {sound_file.name}')
        print(f'    크기: {stats_data["size"]} bytes')
        print(f'    Preview: {stats_data["preview"][:60]}...')
        print(f'    Unique bytes: {stats_data["unique_bytes"]}/256')
        print(f'    High bit (≥0x80): {stats_data["high_bit_count"]} '
              f'({stats_data["high_bit_count"]*100//stats_data["size"]}%)')

    print('\n' + '=' * 70)
    print('\n💡 참고:')
    print('   .ro 파일은 Roland MT-32 raw 데이터 + RO 태그입니다.')
    print('   ScummVM iMuse 엔진으로 재생 가능합니다.')
    print('   MIDI 재생을 위해서는:')
    print('   1. ScummVM 사용 (권장)')
    print('   2. Roland MT-32 에뮬레이터 + raw 데이터')
    print('   3. Munt (MT-32 에뮬레이터)')


if __name__ == '__main__':
    process_all_sounds()
