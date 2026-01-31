import os
import librosa
import soundfile as sf
import numpy as np
import torch
from demucs.pretrained import get_model
from demucs.apply import apply_model
import crepe
import pretty_midi
from music21 import converter, environment

def setup_environment():
    """Initialize music21 environment with MuseScore"""
    env = environment.UserSettings()
    env['musescoreDirectPNGPath'] = '/usr/bin/mscore'  # Update this path if needed
    env['musicxmlPath'] = '/usr/bin/mscore'

def denoise_with_demucs(input_path, output_path, stem="other"):
    """Denoise audio using Demucs and return the cleaned audio path"""
    audio, sr = librosa.load(input_path, sr=None, mono=False)
    if audio.ndim == 1:
        audio = np.stack([audio, audio], axis=0)
    audio_tensor = torch.from_numpy(audio).float().unsqueeze(0)
    model = get_model(name="htdemucs")
    model.cpu()
    with torch.no_grad():
        stems = apply_model(model, audio_tensor, device='cpu')
    stem_map = {0: 'drums', 1: 'bass', 2: 'other', 3: 'vocals'}
    target_idx = [k for k, v in stem_map.items() if v == stem][0]
    isolated_audio = stems[0][target_idx].cpu().numpy()
    if isolated_audio.ndim == 2:
        isolated_audio = np.mean(isolated_audio, axis=0)
    sf.write(output_path, isolated_audio, sr)
    return output_path

def audio_to_midi(audio_path, midi_output_path):
    """Convert audio to MIDI using CREPE (monophonic)"""
    y, sr = librosa.load(audio_path, sr=16000, mono=True)
    time, frequency, confidence, activation = crepe.predict(y, sr, viterbi=True)
    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)
    for t, f, c in zip(time, frequency, confidence):
        if c > 0.5 and f > 0:
            note_number = int(pretty_midi.hz_to_note_number(f))
            start = t
            end = t + 0.05
            note = pretty_midi.Note(velocity=100, pitch=note_number, start=start, end=end)
            instrument.notes.append(note)
    midi.instruments.append(instrument)
    midi.write(midi_output_path)
    return midi_output_path

def enhance_midi(midi_path, audio_path):
    """Add velocity mapping and improve note durations"""
    midi_data = pretty_midi.PrettyMIDI(midi_path)
    y, sr = librosa.load(audio_path, sr=None, mono=True)
    for instrument in midi_data.instruments:
        for note in instrument.notes:
            start_sample = int(note.start * sr)
            end_sample = int(note.end * sr)
            note_audio = y[start_sample:end_sample]
            if len(note_audio) > 0:
                rms = np.sqrt(np.mean(note_audio**2))
                note.velocity = int(np.interp(rms, [0, 0.1], [20, 127]))
            note.end = round(note.end * 4) / 4
    midi_data.write(midi_path)
    return midi_path

def midi_to_sheet(midi_path, output_path):
    """Convert MIDI to quantized sheet music"""
    score = converter.parse(midi_path)
    score = score.quantize(quarterLengthDivisors=[4], processOffsets=True)
    score = score.stripTies()
    score = score.makeNotation()
    score.write('musicxml', fp=output_path)
    return output_path

def audio_to_sheet_pipeline(input_path, output_path, cleanup=True):
    """Full pipeline from audio to sheet music"""
    setup_environment()
    temp_audio = "temp_denoised.wav"
    temp_midi = "temp.mid"
    try:
        # Step 1: Denoise with Demucs
        denoised_audio = denoise_with_demucs(input_path, temp_audio, stem="other")
        # Step 2: Convert to MIDI with CREPE
        midi_path = audio_to_midi(denoised_audio, temp_midi)
        # Step 3: Enhance MIDI with velocity and timing
        enhance_midi(midi_path, denoised_audio)
        # Step 4: Convert to quantized sheet music
        midi_to_sheet(midi_path, output_path)
        print(f"Successfully generated sheet music at {output_path}")
    finally:
        if cleanup:
            for path in [temp_audio, temp_midi]:
                if os.path.exists(path):
                    os.remove(path)

if __name__ == "__main__":
    # Example usage
    input_audio = "sounds/input/797903__josefpres__piano-loops-188-octave-up-short-loop-120-bpm.wav"
    output_sheet = "sheet_music.xml"
    audio_to_sheet_pipeline(
        input_audio,
        output_sheet,
        cleanup=True  # Set to False to keep intermediate files
    )