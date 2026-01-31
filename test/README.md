# Information about the source codes in this dicrectory
the codes here are mainly exprerimental. Vibe coding at its finest.

## denosing_gpt.py
Code written by chat. Still not tested.

## mini_to_sheet.py
Convert a MIDI file into a music sheet. The sheet can be showed using musescore or another music notation software.

## note_approximation.py
Given by Alex's GPT.

## denosing_v1.py
The first solution for denosing
### How it actually works ???:
1. Input: Takes a noisy WAV file. It can be a mp3 file, but recommed to convert it first.
2. STFT Analysis: It breaks and split the audio into freuency components using short-time fourier transform.
3. Noise Estimation:
    - Smooths the magnitude spectrum over tiem to estimate noise.
    - Compares the original signal to the smoothed version to identify noise.
4. Soft Making:
    - Applies a sigmoid function to create a "soft" mask (0–1 values) that preserves signal and suppresses noise.
    - Smooths the mask to avoid artifacts.
5. Reconstruction: Converts the masked STFT back to clean audio.

### Parameters
Explained in the code, but key ones are:
| Parameter           | Effect                                                                 |
|---------------------|-----------------------------------------------------------------------|
| `n_fft`             | FFT size (2048 for speech, 4096 for music).                           |
| `alpha`             | How aggressively to smooth noise estimates (0.1–0.3).                 |
| `sigmoid_threshold` | Lower values remove more noise but may cut into desired signal.       |
| `prop_decrease`     | 1.0 = full denoising, 0.5 = partial.                                  |

## Limitations:
- Best works on stationary noise (hiss, hum, wind)
- Struggle with non-stationary noise (e.g., voices, sudden bursts)
- For music: Use `n_fft=4096` and gentle settings (`alpha=0.1`, `prop_decrease=0.8`).

## How to use it:
1. Make sure that you have all installed dependecies.
2. First in the code change the dicrectory so this point on the sound file that you want to denoised. Here (line 63):
```
y, sr = librosa.load("sounds/input/2.wav", sr=None)
```
Note: the input file should be .wav (alternativly it can be .mp3)

3. Then change the directory of the output, if needed (line 79):
```
sf.write("piano2.wav", denoised, sr)
```

## crepe_audio2midi.py
audio2midi that use crepe

## audio_to_sheet_dogshit.py
first try with full implementation

## audio_to_sheet2.py
second try with full implemetation


