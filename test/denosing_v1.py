import numpy as np
import librosa
import soundfile as sf
from scipy.signal import lfilter

def exponential_smoothing_filter(signal, alpha=0.3):
    """Apply exponential smoothing filter along time axis"""
    b = [alpha]
    a = [1, -(1 - alpha)]
    return lfilter(b, a, signal, axis=-1)

def denoise_audio(y, sr, n_fft=2048, hop_length=512, alpha=0.3, 
                 sigmoid_steepness=10, sigmoid_threshold=0.5,
                 mask_smoothing=0.2, prop_decrease=1.0):
    """
    Denoise audio using spectral subtraction with adaptive soft masking
    
    Parameters:
    y (np.ndarray): Noisy audio signal
    sr (int): Sample rate
    n_fft (int): FFT size
    hop_length (int): Hop length for STFT
    alpha (float): Smoothing factor for exponential filter (0-1)
    sigmoid_steepness (float): Steepness of sigmoid function
    sigmoid_threshold (float): Threshold for sigmoid function
    mask_smoothing (float): Smoothing factor for mask
    prop_decrease (float): Proportion of noise to decrease (0-1)
    
    Returns:
    denoised (np.ndarray): Denoised audio signal
    """
    # Compute STFT
    D = librosa.stft(y, n_fft=n_fft, hop_length=hop_length)
    magnitude, phase = np.abs(D), np.angle(D)

    # 1. Smooth magnitude spectrum over time
    smoothed_mag = exponential_smoothing_filter(magnitude, alpha=alpha)

    # 2. Compute normalized difference
    diff = (magnitude - smoothed_mag) / (magnitude + smoothed_mag + 1e-10)
    
    # 3. Apply sigmoid to create soft mask
    mask = 1 / (1 + np.exp(-sigmoid_steepness * (diff - sigmoid_threshold)))
    
    # 4. Smooth the mask
    smoothed_mask = exponential_smoothing_filter(mask, alpha=mask_smoothing)
    
    # 5. Blend mask using proportion decrease
    if prop_decrease < 1.0:
        smoothed_mask = prop_decrease * smoothed_mask + (1 - prop_decrease) * (1 - smoothed_mask)
    
    # 6. Apply mask to complex STFT
    denoised_stft = smoothed_mask * magnitude * np.exp(1j * phase)
    
    # 7. Reconstruct audio
    denoised = librosa.istft(denoised_stft, hop_length=hop_length, length=len(y))
    
    return denoised

# Example usage
if __name__ == "__main__":
    # Load noisy audio
    y, sr = librosa.load("sounds/input/2.wav", sr=None)
    
    # Denoise parameters (tune these based on your audio)
    params = {
        'n_fft': 2048,
        'hop_length': 512,
        'alpha': 0.2,          # Stronger smoothing = 0.1-0.3
        'sigmoid_steepness': 8,
        'sigmoid_threshold': 0.4,
        'mask_smoothing': 0.1,
        'prop_decrease': 1.0    # 1.0 = full noise reduction
    }
    
    denoised = denoise_audio(y, sr, **params)
    
    # Save result
    sf.write("piano2.wav", denoised, sr)