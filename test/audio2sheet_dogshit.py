import librosa
import soundfile as sf
import torch
import numpy as np
from demucs.pretrained import get_model
from demucs.apply import apply_model
from scipy.signal import lfilter
import crepe
import pretty_midi
from music21 import converter, environment

# Step 1: Exponential smoothing filter
def exponential_smoothing_filter(signal, alpha=0.3):
    b = [alpha]
    a = [1, -(1 - alpha)]
    return lfilter(b, a, signal, axis=-1)

# Step 2: Spectral subtraction denoising
def denoise_audio(y, sr, n_fft=2048, hop_length=512, alpha=0.3, 
                  sigmoid_steepness=10, sigmoid_threshold=0.5,
                  mask_smoothing=0.2, prop_decrease=1.0):
    D = librosa.stft(y, n_fft=n_fft, hop_length=hop_length)
    magnitude, phase = np.abs(D), np.angle(D)
    smoothed_mag = exponential_smoothing_filter(magnitude, alpha=alpha)
    diff = (magnitude - smoothed_mag) / (magnitude + smoothed_mag + 1e-10)
    mask = 1 / (1 + np.exp(-sigmoid_steepness * (diff - sigmoid_threshold)))
    smoothed_mask = exponential_smoothing_filter(mask, alpha=mask_smoothing)
    if prop_decrease < 1.0:
        smoothed_mask = prop_decrease * smoothed_mask + (1 - prop_decrease) * (1 - smoothed_mask)
    denoised_stft = smoothed_mask * magnitude * np.exp(1j * phase)
    denoised = librosa.istft(denoised_stft, hop_length=hop_length, length=len(y))
    return denoised

# Step 3: Hybrid denoising with Demucs and spectral subtraction
def hybrid_denoise(input_path, output_path, stem="other"):
    # Load audio in stereo as Demucs expects 2 channels
    audio, sr = librosa.load(input_path, sr=None, mono=False)
    if audio.ndim == 1:
        # If input is mono, duplicate to stereo
        audio = np.stack([audio, audio], axis=0)
    # Shape: (channels, length) -> (batch, channels, length)
    audio_tensor = torch.from_numpy(audio).float().unsqueeze(0)
    model = get_model(name="htdemucs")
    model.cpu()
    with torch.no_grad():
        stems = apply_model(model, audio_tensor, device='cpu')
    stem_map = {0: 'drums', 1: 'bass', 2: 'other', 3: 'vocals'}
    target_idx = [k for k, v in stem_map.items() if v == stem][0]
    # Get the isolated stem (channels, length)
    isolated_audio = stems[0][target_idx].cpu().numpy()
    # Convert to mono for denoising
    if isolated_audio.ndim == 2:
        isolated_audio = np.mean(isolated_audio, axis=0)
    denoised = denoise_audio(isolated_audio, sr, n_fft=2048, alpha=0.2, sigmoid_threshold=0.4)
    sf.write(output_path, denoised, sr)
    return output_path, sr

# Step 4: Convert audio to MIDI using CREPE
def audio_to_midi(audio_path, midi_output_path):
    # CREPE expects 16kHz mono audio
    y, sr = librosa.load(audio_path, sr=16000, mono=True)
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
    return midi_output_path

# Step 5: Convert MIDI to music sheet using Music21
def midi_to_sheet(midi_path, sheet_output_path):
    us = environment.UserSettings()
    us['musescoreDirectPNGPath'] = '/usr/bin/mscore'
    score = converter.parse(midi_path)
    score.write('musicxml', fp=sheet_output_path)
    return sheet_output_path

# Main pipeline
def audio_to_sheet_pipeline(input_audio, output_sheet, stem="other"):
    denoised_audio, sr = hybrid_denoise(input_audio, "denoised_output.wav", stem)
    midi_path = audio_to_midi(denoised_audio, "output.mid")
    sheet_path = midi_to_sheet(midi_path, output_sheet)
    print(f"Music sheet saved to {sheet_path}")

# Example usage
if __name__ == "__main__":
    audio_to_sheet_pipeline("sounds/input/2.wav", "test2.xml", stem="other")