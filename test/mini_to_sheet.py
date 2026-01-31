from music21 import converter, environment

us = environment.UserSettings()
us['musescoreDirectPNGPath'] = '/usr/bin/mscore'
# Or 'mscore3', 'mscore4', etc. on Linux
# On Windows: 'C:\\Program Files\\MuseScore 4\\bin\\MuseScore4.exe'
# On Mac: '/Applications/MuseScore 4.app/Contents/MacOS/mscore'

# Loading MIDI file
midi_file = "midi/Undertale_-_Megalovania.mid"
score = converter.parse(midi_file)

# it will open MuseScore
score.show()

# if needed can be open in MusicXML or PDF

# Save as MusicXML
score.write('musicxml', fp='output_sheet.xml')

# Save as PDF (requires MuseScore to export PDF)
score.write('lily.pdf', fp='output_sheet.pdf')  # Or use 'musicxml.pdf'