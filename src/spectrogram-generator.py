import os
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np

root_folder = os.path.abspath("./sounds")
output_folder = os.path.abspath("./spectrograms")
print("Root folder:", root_folder)
print("Output folder:", output_folder)

def wav_to_melspectrogram(file_path, output_path):
    y, sr = librosa.load(file_path)
    S = librosa.feature.melspectrogram(y=y, sr=sr)
    S_db = librosa.power_to_db(S, ref=np.max)
    plt.figure(figsize=(10, 4))
    librosa.display.specshow(S_db, sr=sr, x_axis='time', y_axis='mel')
    plt.colorbar(format='%+2.0f dB')
    plt.title(file_path)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def process_files():
    os.makedirs(output_folder, exist_ok=True)
    for root, dirs, files in os.walk(root_folder):
        for file in files:
            if file.endswith('.wav'):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(root, root_folder)
                output_dir = os.path.join(output_folder, rel_path)
                os.makedirs(output_dir, exist_ok=True)

                output_filename = os.path.splitext(file)[0] + '.png'
                output_path = os.path.join(output_dir, output_filename)

                print(f"Processing: {file_path} -> {output_path}")
                wav_to_melspectrogram(file_path, output_path)

process_files()
