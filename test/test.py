import os
import sys
import librosa
import soundfile as sf
import torch
import numpy as np
import noisereduce as nr
from demucs.pretrained import get_model
from demucs.apply import apply_model
from basic_pitch.inference import predict_and_save
from basic_pitch import ICASSP_2022_MODEL_PATH
from scipy.signal import wiener, medfilt
from music21 import converter, environment
import shutil
import glob

def cleanup_temp_files(pattern):
    """Clean up temporary files matching the pattern"""
    files = glob.glob(pattern)
    for file in files:
        try:
            os.remove(file)
            print(f"Removed existing file: {file}")
        except OSError:
            pass

def denoise_audio(input_path, output_path):
    """Denoise audio using noise reduction and Wiener filtering"""
    audio, sr = librosa.load(input_path, sr=None, mono=False)
    audio = medfilt(audio, kernel_size=3)
    original_audio = audio.copy()

    audio = nr.reduce_noise(
        y=audio,
        sr=sr,
        stationary=False,
        prop_decrease=0.6,
        n_fft=1024,
        win_length=512
    )

    noise_level = np.var(audio - original_audio) * 0.5
    clean_audio = wiener(audio, mysize=3, noise=noise_level)

    clean_audio = np.clip(clean_audio, -1.0, 1.0)
    if np.max(np.abs(clean_audio)) > 0:
        clean_audio = clean_audio * (np.max(np.abs(original_audio)) / np.max(np.abs(clean_audio)))
    
    sf.write(output_path, clean_audio, sr)
    print(f"Denoised audio saved: {output_path}")

    return output_path

def demucs_separate(input_path, output_path, stem="other"):
    """Separate audio stems using Demucs"""
    audio, sr = librosa.load(input_path, sr=None, mono=False)
    if audio.ndim == 1:
        audio = np.stack([audio, audio], axis=0)

    audio_tensor = torch.from_numpy(audio).float().unsqueeze(0)
    
    model = get_model(name="htdemucs")
    device = 'cpu'
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
    print(f"Separated audio saved: {output_path}")

    return output_path

def audio_to_midi_basic_pitch(audio_path, midi_output_path):
    """Convert audio to MIDI using basic-pitch"""
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    cleanup_pattern = f"{base_name}*basic_pitch*.mid"
    cleanup_temp_files(cleanup_pattern)
    cleanup_temp_files("*.mid")
    
    output_dir = os.path.dirname(midi_output_path) or "."
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Predicting MIDI for {audio_path}...")
    
    try:
        predict_and_save(
            [audio_path],
            output_directory=output_dir,
            save_midi=True,
            save_notes=False,
            save_model_outputs=False,
            sonify_midi=False,
            model_or_model_path=ICASSP_2022_MODEL_PATH
        )
        
        expected_midi = os.path.join(output_dir, f"{base_name}_basic_pitch.mid")
        
        if os.path.exists(expected_midi):
            if expected_midi != midi_output_path:
                shutil.move(expected_midi, midi_output_path)
            print(f"MIDI saved to {midi_output_path}")
        else:
            midi_files = glob.glob(os.path.join(output_dir, "*.mid"))
            if midi_files:
                shutil.move(midi_files[0], midi_output_path)
                print(f"MIDI saved to {midi_output_path}")
            else:
                raise FileNotFoundError("No MIDI file was generated")
                
    except Exception as e:
        print(f"Error in MIDI conversion: {e}")
        raise
    
    return midi_output_path

def midi_to_pdf(midi_path, pdf_path):
    """Convert MIDI to PDF using music21 and LilyPond"""
    try:
        env = environment.Environment()
        env['lilypondPath'] = '/usr/bin/lilypond'
        
        print(f"Converting MIDI to PDF: {midi_path}")
        score = converter.parse(midi_path)
        
        output_dir = os.path.dirname(pdf_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        pdf_path = os.path.splitext(pdf_path)[0] + '.pdf'
        score.write('lilypond.pdf', fp=pdf_path)
        
        print(f"PDF saved to {pdf_path}")
        return pdf_path
        
    except Exception as e:
        print(f"Error converting MIDI to PDF: {e}")
        print("Make sure LilyPond is installed and accessible")
        return midi_path

def convert_to_wav(input_path):
    """Convert audio file to WAV format"""
    audio, sr = librosa.load(input_path, sr=None)
    wav_path = os.path.splitext(input_path)[0] + '.wav'
    sf.write(wav_path, audio, sr)
    print(f"Converted to WAV: {wav_path}")
    return wav_path

def audio_to_sheet_pipeline(input_audio, output_path, stem="other"):
    """
    Complete audio-to-sheet music pipeline
    """
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)

    if not input_audio.lower().endswith('.wav'):
        print("Converting input to WAV format...")
        input_audio = convert_to_wav(input_audio)
    
    base_name = os.path.splitext(os.path.basename(input_audio))[0]

    print("Step 1: Denoising audio...")
    denoised_path = os.path.join(temp_dir, f"{base_name}_denoised.wav")
    denoise_audio(input_audio, denoised_path)

    print("Step 2: Separating audio stems...")
    separated_path = os.path.join(temp_dir, f"{base_name}_separated.wav")
    demucs_separate(denoised_path, separated_path, stem=stem)

    print("Step 3: Converting to MIDI...")
    midi_path = os.path.splitext(output_path)[0] + '.mid'
    audio_to_midi_basic_pitch(separated_path, midi_path)
    
    print("Step 4: Converting to PDF...")
    try:
        pdf_path = midi_to_pdf(midi_path, output_path)
        return pdf_path
    except Exception as e:
        print(f"PDF conversion failed: {e}")
        print(f"MIDI file available at: {midi_path}")
        return midi_path

def main():
    if len(sys.argv) < 3:
        print("Usage: python main.py <input_audio> <output_path> [stem]")
        print("stem options: drums, bass, other, vocals (default: other)")
        sys.exit(1)
    
    input_audio = sys.argv[1]
    output_path = sys.argv[2]
    stem = sys.argv[3] if len(sys.argv) > 3 else "other"
    
    if not os.path.exists(input_audio):
        print(f"Error: Input file '{input_audio}' not found")
        sys.exit(1)
    
    try:
        result_path = audio_to_sheet_pipeline(input_audio, output_path, stem=stem)
        print(f"Processing complete. Result saved to: {result_path}")
    except Exception as e:
        print(f"Error during processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()