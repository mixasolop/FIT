import crepe
import librosa
import numpy as np
import pretty_midi

def crepe_audio_to_midi(audio_path, midi_output_path):
    y, sr = librosa.load(audio_path, sr=16000, mono=True)
    # CREPE expects 16kHz audio
    time, frequency, confidence, activation = crepe.predict(y, sr, viterbi=True)
    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)
    # Convert frequency to MIDI notes
    for t, f, c in zip(time, frequency, confidence):
        if c > 0.5 and f > 0:
            note_number = int(pretty_midi.hz_to_note_number(f))
            start = t
            end = t + 0.05  # 50ms note duration
            note = pretty_midi.Note(velocity=100, pitch=note_number, start=start, end=end)
            instrument.notes.append(note)
    midi.instruments.append(instrument)
    midi.write(midi_output_path)