import os
import sys
from music21 import converter, environment, stream, meter, key, pitch
import subprocess
import platform

def find_musescore():
    """Find MuseScore executable"""
    system = platform.system().lower()
    
    # Common MuseScore paths for different systems
    possible_paths = []
    
    if system == "linux":
        possible_paths = [
            '/usr/bin/musescore3',
            '/usr/bin/musescore',
            '/usr/bin/mscore',
            '/snap/bin/musescore',
            '/usr/local/bin/musescore3',
            '/usr/local/bin/musescore',
            'musescore3',
            'musescore'
        ]
    elif system == "darwin":  # macOS
        possible_paths = [
            '/Applications/MuseScore 3.app/Contents/MacOS/mscore',
            '/Applications/MuseScore 4.app/Contents/MacOS/MuseScore4',
            '/opt/homebrew/bin/musescore3',
            '/usr/local/bin/musescore3',
            'musescore3',
            'musescore'
        ]
    elif system == "windows":
        possible_paths = [
            r'C:\Program Files\MuseScore 3\bin\MuseScore3.exe',
            r'C:\Program Files\MuseScore 4\bin\MuseScore4.exe',
            r'C:\Program Files (x86)\MuseScore 3\bin\MuseScore3.exe',
            'musescore3.exe',
            'musescore.exe'
        ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                # Test if MuseScore works
                result = subprocess.run([path, '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print(f"Found MuseScore at: {path}")
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        else:
            # Try if it's in PATH
            try:
                result = subprocess.run([path, '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print(f"Found MuseScore in PATH: {path}")
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
    
    return None

def setup_lilypond():
    """Setup LilyPond environment (fallback option)"""
    env = environment.Environment()
    
    # Common LilyPond paths
    possible_paths = [
        '/usr/bin/lilypond',
        '/usr/local/bin/lilypond',
        '/opt/homebrew/bin/lilypond',  # macOS M1
        'lilypond'  # if in PATH
    ]
    
    for path in possible_paths:
        if os.path.exists(path) or path == 'lilypond':
            try:
                # Test if lilypond works
                result = subprocess.run([path, '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    env['lilypondPath'] = path
                    print(f"Found LilyPond at: {path}")
                    return env
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
    
    return None

def clean_and_improve_score(score):
    """Clean up and improve the MIDI score for better PDF output"""
    try:
        # Add time signature if missing
        if not score.getElementsByClass(meter.TimeSignature):
            score.insert(0, meter.TimeSignature('4/4'))
        
        # Add key signature if missing
        if not score.getElementsByClass(key.KeySignature):
            # Try to analyze key
            try:
                analyzed_key = score.analyze('key')
                score.insert(0, analyzed_key)
            except:
                # Default to C major
                score.insert(0, key.KeySignature(0))
        
        # Remove very short notes (likely noise)
        for part in score.parts:
            notes_to_remove = []
            for note in part.flat.notes:
                if hasattr(note, 'duration') and note.duration.quarterLength < 0.125:  # Less than 32nd note
                    notes_to_remove.append(note)
            
            for note in notes_to_remove:
                part.remove(note)
        
        return score
    
    except Exception as e:
        print(f"Warning: Could not clean score: {e}")
        return score

def midi_to_pdf_musescore(midi_path, pdf_path):
    """Convert MIDI to PDF using MuseScore (preferred method)"""
    musescore_path = find_musescore()
    
    if not musescore_path:
        raise FileNotFoundError("MuseScore not found. Please install MuseScore first.")
    
    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(pdf_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Ensure PDF extension
        if not pdf_path.lower().endswith('.pdf'):
            pdf_path = pdf_path + '.pdf'
        
        print(f"Converting MIDI to PDF using MuseScore...")
        print(f"Input: {midi_path}")
        print(f"Output: {pdf_path}")
        
        # MuseScore command to convert MIDI to PDF
        cmd = [musescore_path, '-o', pdf_path, midi_path]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0 and os.path.exists(pdf_path):
            print(f"PDF successfully created: {pdf_path}")
            return pdf_path
        else:
            error_msg = f"MuseScore conversion failed. Return code: {result.returncode}"
            if result.stderr:
                error_msg += f"\nError: {result.stderr}"
            if result.stdout:
                error_msg += f"\nOutput: {result.stdout}"
            raise RuntimeError(error_msg)
    
    except subprocess.TimeoutExpired:
        raise RuntimeError("MuseScore conversion timed out")
    except Exception as e:
        raise RuntimeError(f"MuseScore conversion failed: {e}")

def midi_to_pdf_music21(midi_path, pdf_path):
    """Convert MIDI to PDF using music21 and LilyPond (fallback method)"""
    env = setup_lilypond()
    
    if not env:
        raise FileNotFoundError("LilyPond not found. Please install LilyPond first.")
    
    try:
        # Parse MIDI file
        print(f"Loading MIDI file with music21: {midi_path}")
        score = converter.parse(midi_path)
        
        if score is None:
            raise ValueError("Could not parse MIDI file")
        
        # Clean and improve the score
        print("Cleaning and improving score...")
        score = clean_and_improve_score(score)
        
        # Ensure output directory exists
        output_dir = os.path.dirname(pdf_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Ensure PDF extension
        if not pdf_path.lower().endswith('.pdf'):
            pdf_path = pdf_path + '.pdf'
        
        # Generate PDF
        print(f"Converting to PDF with LilyPond: {pdf_path}")
        score.write('lilypond.pdf', fp=pdf_path)
        
        if os.path.exists(pdf_path):
            print(f"PDF successfully saved to: {pdf_path}")
            return pdf_path
        else:
            raise FileNotFoundError("PDF was not created")
        
    except Exception as e:
        raise RuntimeError(f"music21/LilyPond conversion failed: {e}")

def midi_to_pdf(midi_path, pdf_path, method='auto'):
    """Convert MIDI to PDF using the best available method"""
    if method == 'auto':
        # Try MuseScore first, fallback to LilyPond
        try:
            return midi_to_pdf_musescore(midi_path, pdf_path)
        except Exception as e:
            print(f"MuseScore method failed: {e}")
            print("Trying LilyPond fallback...")
            return midi_to_pdf_music21(midi_path, pdf_path)
    elif method == 'musescore':
        return midi_to_pdf_musescore(midi_path, pdf_path)
    elif method == 'lilypond':
        return midi_to_pdf_music21(midi_path, pdf_path)
    else:
        raise ValueError("Method must be 'auto', 'musescore', or 'lilypond'")

def midi_to_musicxml(midi_path, xml_path):
    """Convert MIDI to MusicXML format (alternative to PDF)"""
    try:
        print(f"Converting MIDI to MusicXML: {midi_path}")
        score = converter.parse(midi_path)
        
        if score is None:
            raise ValueError("Could not parse MIDI file")
        
        # Clean the score
        score = clean_and_improve_score(score)
        
        # Ensure XML extension
        if not xml_path.lower().endswith('.xml'):
            xml_path = xml_path + '.xml'
        
        # Generate MusicXML
        score.write('musicxml', fp=xml_path)
        
        if os.path.exists(xml_path):
            print(f"MusicXML successfully saved to: {xml_path}")
            return xml_path
        else:
            raise FileNotFoundError("MusicXML was not created")
            
    except Exception as e:
        print(f"Error converting MIDI to MusicXML: {e}")
        raise

def main():
    if len(sys.argv) < 3:
        print("Usage: python midi_to_pdf.py <input_midi> <output_file> [format] [method]")
        print("Formats: pdf (default), xml")
        print("Methods: auto (default), musescore, lilypond")
        print("Examples:")
        print("  python midi_to_pdf.py song.mid sheet_music.pdf")
        print("  python midi_to_pdf.py song.mid sheet_music.pdf pdf musescore")
        print("  python midi_to_pdf.py song.mid sheet_music.xml xml")
        sys.exit(1)
    
    input_midi = sys.argv[1]
    output_file = sys.argv[2]
    output_format = sys.argv[3] if len(sys.argv) > 3 else "pdf"
    method = sys.argv[4] if len(sys.argv) > 4 else "auto"
    
    if not os.path.exists(input_midi):
        print(f"Error: Input MIDI file '{input_midi}' not found")
        sys.exit(1)
    
    try:
        if output_format.lower() == "xml":
            result_path = midi_to_musicxml(input_midi, output_file)
        else:
            result_path = midi_to_pdf(input_midi, output_file, method=method)
        
        print(f"Conversion complete. Result saved to: {result_path}")
        
    except Exception as e:
        print(f"Conversion failed: {e}")
        print("\nTroubleshooting:")
        print("1. Install MuseScore: https://musescore.org/")
        print("   - Ubuntu: sudo apt install musescore3")
        print("   - macOS: brew install --cask musescore")
        print("   - Windows: Download from musescore.org")
        print("2. Alternative: Install LilyPond as fallback")
        print("   - sudo apt install lilypond")
        sys.exit(1)

if __name__ == "__main__":
    main()