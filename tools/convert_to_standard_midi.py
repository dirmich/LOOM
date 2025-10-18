#!/usr/bin/env python3
"""
LOOM 사운드 리소스를 표준 MIDI 파일(.mid)로 변환
Roland MT-32 raw 데이터 → Standard MIDI File Format
"""
import struct
from pathlib import Path


def read_sound_resource(path):
    """사운드 리소스 읽기"""
    with open(path, 'rb') as f:
        data = f.read()

    if len(data) == 0:
        return None, "Empty file"

    return data, None


def create_standard_midi(roland_data):
    """Roland raw 데이터를 표준 MIDI 파일로 변환"""
    midi = bytearray()

    # MThd 헤더 (14 bytes)
    midi.extend(b'MThd')                      # Chunk type
    midi.extend(struct.pack('>I', 6))         # Header length (always 6)
    midi.extend(struct.pack('>H', 0))         # Format 0 (single track)
    midi.extend(struct.pack('>H', 1))         # Number of tracks (1)
    midi.extend(struct.pack('>H', 480))       # Ticks per quarter note

    # MTrk 헤더
    # Roland 데이터 + End of Track (3 bytes)
    track_data = bytearray()
    track_data.extend(roland_data)            # Roland raw MIDI events
    track_data.extend(b'\x00\xFF\x2F\x00')    # Delta time 0 + End of Track

    midi.extend(b'MTrk')                      # Track chunk type
    midi.extend(struct.pack('>I', len(track_data)))  # Track length
    midi.extend(track_data)                   # Track data

    return bytes(midi)


def convert_sound_to_standard_midi(input_path, output_path):
    """사운드 리소스를 표준 MIDI 파일로 변환"""
    roland_data, error = read_sound_resource(input_path)

    if error:
        return False, error

    if len(roland_data) == 0:
        return False, "Empty data"

    # 표준 MIDI 파일 생성
    midi_data = create_standard_midi(roland_data)

    # .mid 파일로 저장
    mid_path = output_path.with_suffix('.mid')
    with open(mid_path, 'wb') as f:
        f.write(midi_data)

    return True, mid_path


def process_all_sounds():
    """모든 사운드 파일을 표준 MIDI로 변환"""
    decoded_dir = Path('decoded2')
    output_dir = Path('sounds_standard_midi')
    output_dir.mkdir(exist_ok=True)

    print('🎵 LOOM 사운드 → 표준 MIDI 변환')
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
    }

    # 각 파일 처리
    for sound_file in sound_files:
        # Room 번호와 리소스 ID 추출
        parts = sound_file.stem.split('_')
        room_num = parts[0]
        res_id = parts[1]

        # 출력 경로
        output_name = f'{room_num}_{res_id}'
        output_path = output_dir / output_name

        # 변환
        success, result = convert_sound_to_standard_midi(sound_file, output_path)

        if success:
            stats['success'] += 1

            # 진행 상황 (50개마다)
            if stats['success'] % 50 == 0:
                print(f'   ✅ {stats["success"]}개 완료...')
        else:
            stats['failed'] += 1

    # 결과 출력
    print('\n' + '=' * 70)
    print('✅ 변환 완료!')
    print(f'   총 파일: {stats["total"]}개')
    print(f'   성공: {stats["success"]}개 ({stats["success"]*100//stats["total"] if stats["total"] > 0 else 0}%)')
    print(f'   실패: {stats["failed"]}개')
    print(f'\n   출력: {output_dir.absolute()}/')
    print(f'   포맷: Standard MIDI File (.mid)')

    print('\n' + '=' * 70)
    print('\n💡 참고:')
    print('   .mid 파일은 표준 MIDI 파일입니다.')
    print('   일반 MIDI 플레이어에서 열 수 있습니다.')
    print('   ⚠️  Roland MT-32 음원이 필요합니다:')
    print('   1. Roland MT-32 하드웨어')
    print('   2. Munt (MT-32 에뮬레이터)')
    print('   3. FluidSynth + MT-32 SoundFont')
    print('   4. ScummVM (권장 - 자동으로 MT-32 처리)')


if __name__ == '__main__':
    process_all_sounds()
