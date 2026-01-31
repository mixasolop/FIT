# Melody to Notes Approximation with FIT Analysis

import librosa
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import get_window
from collections import Counter

# 1. Load audio file
def load_audio(filename, sr=22050):
    y, sr = librosa.load(filename, sr=sr)
    return y, sr

# 2. Time-Frequency representation (CQT is better for musical notes)
def compute_cqt(y, sr, hop_length=512, bins_per_octave=12*4):
    C = librosa.cqt(y, sr=sr, hop_length=hop_length, bins_per_octave=bins_per_octave)
    freqs = librosa.cqt_frequencies(C.shape[0], fmin=librosa.note_to_hz('C1'), bins_per_octave=bins_per_octave)
    return np.abs(C), freqs

# 3. Approximate each time slice using top-K frequencies (nonlinear approximation)
def nonlinear_approximation(cqt_mag, freqs, K):
    approx = np.zeros_like(cqt_mag)
    for t in range(cqt_mag.shape[1]):
        top_k = np.argsort(cqt_mag[:, t])[-K:]
        approx[top_k, t] = cqt_mag[top_k, t]
    return approx

# 4. Entropy of selected notes
def compute_entropy(approx_cqt):
    note_indices = np.nonzero(approx_cqt)
    note_counts = Counter(note_indices[0])
    total = sum(note_counts.values())
    probs = np.array([count / total for count in note_counts.values()])
    entropy = -np.sum(probs * np.log2(probs))
    return entropy

# 5. Distortion (difference between original and approximated magnitude)
def compute_distortion(original_cqt, approx_cqt):
    return np.mean((original_cqt - approx_cqt) ** 2)

# 6. Plotting
def plot_rate_distortion(K_values, distortions, entropies):
    plt.figure()
    plt.plot(K_values, distortions, label='Distortion')
    plt.plot(K_values, entropies, label='Entropy (Rate)')
    plt.xlabel('K (Number of notes per frame)')
    plt.ylabel('Value')
    plt.title('Rate-Distortion Trade-off')
    plt.legend()
    plt.grid()
    plt.show()

# Example usage
if __name__ == '__main__':
    y, sr = load_audio('melody.wav')
    cqt_mag, freqs = compute_cqt(y, sr)

    K_values = [1, 2, 4, 8, 16]
    distortions = []
    entropies = []

    for K in K_values:
        approx = nonlinear_approximation(cqt_mag, freqs, K)
        distortion = compute_distortion(cqt_mag, approx)
        entropy = compute_entropy(approx)
        distortions.append(distortion)
        entropies.append(entropy)

    plot_rate_distortion(K_values, distortions, entropies)