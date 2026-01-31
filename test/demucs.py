import librosa
import soundfile as sf
import torch
import numpy as np
from demucs.pretrained import get_model
from demucs.apply import apply_model

# Denoising with Demucs only (no spectral subtraction, no exponential smoothing)
def demucs_denoise(input_path, output_path, stem="other"):
    # Load audio in stereo as Demucs expects 2 channels
    audio, sr = librosa.load(input_path, sr=None, mono=False)
    if audio.ndim == 1:
        # If input is mono, duplicate to stereo
        audio = np.stack([audio, audio], axis=0)
    # Shape: (channels, length) -> (batch, channels, length)
    audio_tensor = torch.from_numpy(audio).float().unsqueeze(0)
    model = get_model(name="htdemucs")
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model.to(device)
    audio_tensor = audio_tensor.to(device)
    with torch.no_grad():
        stems = apply_model(model, audio_tensor, device=device)
    stem_map = {0: 'drums', 1: 'bass', 2: 'other', 3: 'vocals'}
    target_idx = [k for k, v in stem_map.items() if v == stem][0]
    # Get the isolated stem (channels, length)
    isolated_audio = stems[0][target_idx].cpu().numpy()
    # Convert to mono for saving
    if isolated_audio.ndim == 2:
        isolated_audio = np.mean(isolated_audio, axis=0)
    sf.write(output_path, isolated_audio, sr)
    print(f"Cleaned audio saved to {output_path}")

# Example usage
if __name__ == "__main__":
    demucs_denoise("sounds/input/3.wav", "sounds/output/only_demucs_3.wav", stem="other")