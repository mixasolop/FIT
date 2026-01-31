import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt

# Load audio file
y, sr = librosa.load("input.wav", sr=None)

# Compute STFT (Fourier Transform)
D = librosa.stft(y)  # Convert to frequency domain
magnitude, phase = librosa.magphase(D)  # Separate magnitude and phase

# Noise Reduction: Apply threshold to remove low-energy noise
threshold = np.percentile(magnitude, 10)  # Adjust as needed
magnitude[magnitude < threshold] = 0  # Zero out small magnitude values

# Reconstruct the signal using Inverse STFT
D_clean = magnitude * phase  # Restore phase information
y_clean = librosa.istft(D_clean)

# Plot and save cleaned audio
librosa.display.waveshow(y_clean, sr=sr)
plt.title("Denoised Audio")
plt.show()
