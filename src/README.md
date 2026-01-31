# Audio to Sheet Music - Separate Scripts

## Files Structure
```
src/
├── audio_to_midi.py    # Convert audio to MIDI
├── midi_to_pdf.py      # Convert MIDI to PDF/MusicXML
└── requirements.txt    # Dependencies
```

## Usage Examples

### Step 1: Convert Audio to MIDI
```bash
# Basic usage
python src/audio_to_midi.py input.wav output.mid

# With stem separation (other = melodic instruments like piano)
python src/audio_to_midi.py input.wav output.mid other

# Extract vocals only
python src/audio_to_midi.py input.wav vocals.mid vocals

# Extract bass line
python src/audio_to_midi.py input.wav bass.mid bass


### Step 2: Convert MIDI to PDF
```bash
# Convert MIDI to PDF
python src/midi_to_pdf.py piano_loop.mid piano_sheet.pdf

# Convert MIDI to MusicXML (alternative format)
python src/midi_to_pdf.py piano_loop.mid piano_sheet.xml xml
```

### Complete Workflow Example
```bash
# Step 1: Audio to MIDI
python src/audio_to_midi.py sounds/input/797903__josefpres__piano-loops-188-octave-up-short-loop-120-bpm.wav piano_transcription.mid other

# Step 2: MIDI to PDF
python src/midi_to_pdf.py piano_transcription.mid piano_sheet_music.pdf
```

## Stem Options
- `drums` - Extract drum parts
- `bass` - Extract bass line
- `other` - Extract melodic instruments (piano, guitar, etc.)
- `vocals` - Extract vocal parts

## Output Formats
- `.mid` - MIDI file (playable, editable)
- `.pdf` - Sheet music PDF (requires LilyPond)
- `.xml` - MusicXML format (import into notation software)

## Advantages of Separate Scripts

1. **Easier Debugging** - If MIDI generation works but PDF fails, you know where the issue is
2. **Faster Iteration** - Re-generate PDFs without re-processing audio
3. **Multiple Formats** - Generate different sheet music formats from same MIDI
4. **Batch Processing** - Process multiple MIDI files to PDF at once
5. **Modular** - Use only the parts you need

## Troubleshooting

### If MIDI generation fails:
- Check if input audio file exists
- Ensure you have enough disk space in `temp/` folder
- Try with a shorter audio clip first

### If PDF generation fails:
- Install LilyPond: `sudo apt-get install lilypond`
- Try generating MusicXML instead: `python src/midi_to_pdf.py input.mid output.xml xml`
- Use the MIDI file directly in music software

## Dependencies
Make sure to install all requirements:
```bash
pip install -r requirements.txt
sudo apt-get install lilypond  # For PDF generation
```