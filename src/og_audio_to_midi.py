import os
# os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
# os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

import sys
import librosa
import soundfile as sf
import torch
import numpy as np
from demucs.pretrained import get_model
from demucs.apply import apply_model
from basic_pitch.inference import predict_and_save

def demucs_denoise(input_path, output_path, stem="other"):
    audio, sr = librosa.load(input_path, sr=None, mono=False)
    if audio.ndim == 1:
        audio = np.stack([audio, audio], axis=0)
    audio_tensor = torch.from_numpy(audio).float().unsqueeze(0)
    model = get_model(name="htdemucs")
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model.to(device)
    audio_tensor = audio_tensor.to(device)
    with torch.no_grad():
        stems = apply_model(model, audio_tensor, device=device)
    stem_map = {0: 'drums', 1: 'bass', 2: 'other', 3: 'vocals'}
    target_idx = [k for k, v in stem_map.items() if v == stem][0]
    isolated_audio = stems[0][target_idx].cpu().numpy()
    if isolated_audio.ndim == 2:
        isolated_audio = np.mean(isolated_audio, axis=0)
    sf.write(output_path, isolated_audio, sr)
    return output_path

def audio_to_midi_basic_pitch(audio_path, midi_output_path):
    from basic_pitch import ICASSP_2022_MODEL_PATH
    predict_and_save(
        [audio_path],
        output_directory=".",
        save_midi=True,
        save_notes=False,
        save_model_outputs=False,
        sonify_midi=False,
        model_or_model_path=ICASSP_2022_MODEL_PATH
    )
    base = os.path.splitext(os.path.basename(audio_path))[0]
    generated_midi = f"{base}.mid"
    if generated_midi != midi_output_path:
        os.rename(generated_midi, midi_output_path)
    print(f"MIDI saved to {midi_output_path}")
    return midi_output_path

def audio_to_sheet_pipeline(input_audio, output_midi, stem="other"):
    denoised_audio = demucs_denoise(input_audio, sys.argv[1], stem)
    midi_path = audio_to_midi_basic_pitch(denoised_audio, output_midi)
    print(f"Done. MIDI file: {midi_path}")

if __name__ == "__main__":
    audio_to_sheet_pipeline(sys.argv[1], sys.argv[2], stem="other")