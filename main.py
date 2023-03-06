"""
    A python script to apply a lofi walkie-talkie/radio effect to audio files in a directory.

    > Put your audio files inside the 'audio' folder.
    > Adjust the constants (if file formats are different).
    > Run the script.
    > Results should appear in the 'processed' folder.
"""

## Imports
import pydub
from pydub import AudioSegment, silence
from pydub.generators import WhiteNoise
import os

## Constants
ACCEPTED_FILE_TYPE = 'mp3'
EXPORTED_FILE_TYPE = 'mp3'

COMPRESS_FILES = False
REDUCE_PITCH = True

dir_path = os.path.join(os.getcwd(), 'audio')
results_path = os.path.join(os.getcwd(), 'processed')

def change_pitch(audio, value):
    """Change the pitch of an audio segment. (only use for reduction)"""
    
    # Keep track of the old frame rate for future reference (when compensating speed).
    old_frame_rate = audio.frame_rate
    audio = audio._spawn(audio.raw_data, overrides={
        "frame_rate": int(audio.frame_rate * value)
    })
    
    # Reducing the ptich also affects the speed, so we need to compensate for that.
    new_frame_rate = audio.frame_rate
    ratio = old_frame_rate / new_frame_rate
    audio = audio.speedup(ratio)
    
    return audio

def trim_silences(audio, threshold = -50):
    """Strip period of silence from beginning and end of the audio segment."""
    
    nonsilent_ranges = silence.detect_nonsilent(audio, min_silence_len=100, silence_thresh=threshold)
    trimmed_audio = audio[nonsilent_ranges[0][0]:nonsilent_ranges[-1][1]]
    return trimmed_audio
    
def walkie_talkie(voice):
    """Add a low-fi walkie-talkie/radio filter to the audio."""
    
    # Add a high-pass to the voice and amplify it by 11dB
    voice_recording = voice.high_pass_filter(1015) + 11
    
    # Short 300ms static burst that comes before and after the voice.
    static = WhiteNoise().to_audio_segment(duration=300) - 10
    
    # Short 350ms silence to put between the effects.
    silence = AudioSegment.silent(duration=350)
    
    # Stitch it together
    voice_recording = static + silence + voice_recording + silence + static
    
    # Generate white noise to use as the static effect for the background
    # Reduce the gain on it by 18dB so that it does not overpower the voice.
    background_static = WhiteNoise().to_audio_segment(duration=len(voice_recording)) - 18
    
    # Apply the static effect to the voice recording.
    voice_with_static = voice_recording.overlay(background_static, loop=True)
    
    # Apply a second high-pass filter to better simulate a walkie-talkie.
    filtered_voice = voice_with_static.high_pass_filter(1015)
    
    # Add a walkie-talkie "over" beep sound effect.
    beep_sfx = trim_silences(AudioSegment.from_mp3("sfx/beep.mp3"), -40)
    final = filtered_voice + beep_sfx
    return final

def compress(audio, ratio):
    """Compress the audio size at cost of quality."""
    
    sound = audio.set_frame_rate(int(audio.frame_rate / ratio)) # / 2 for 50%, / 4 is okay

# Create a new directory to store processed files.
if not os.path.exists(results_path):
    os.makedirs(results_path)

# Loop through all audio files in the directory of the ACCEPTED_FILE_TYPE
for filename in os.listdir(dir_path):
    if filename.endswith('.' + ACCEPTED_FILE_TYPE):
    
        # Load the file using pydub.
        voice_recording = AudioSegment.from_file(os.path.join(dir_path, filename), format=ACCEPTED_FILE_TYPE)
        
        # Trim any silence from the beginning and end of the voice recording.
        voice_recording = trim_silences(voice_recording, -40)
        
        # Reduce the pitch by 15% to sound deeper.
        if REDUCE_PITCH:
            voice_recording = change_pitch(voice_recording, 0.85) # (100 - 15 = 85)
        
        # Add the radio effect to get the final audio.
        final = walkie_talkie(voice_recording)
        
        if COMPRESS_FILES:
            final = compress(final)
        
        # Export the file to the new directory
        path = os.path.join(results_path, filename)
        final.export(path, format=EXPORTED_FILE_TYPE)
        
        print("Processed file: ", path)
        print()
