"""
Procedural 8-bit Chiptune Sound Generator for Gravity Station.
Generates authentic retro sound effects and background chiptune music in memory using math and struct.
"""

import math
import struct
import random
import pygame

SAMPLE_RATE = 44100

def _pack_samples(samples):
    # Clamp and pack to 16-bit signed PCM
    clamped = [max(-32767, min(32767, int(s))) for s in samples]
    return struct.pack(f"<{len(clamped)}h", *clamped)

def generate_jump_sound():
    duration = 0.15
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        freq = 220 + 700 * (t / duration)  # 220Hz -> 920Hz sweep
        phase = t * freq
        val = 1.0 if (phase % 1.0) < 0.5 else -1.0  # Square wave
        envelope = 1.0 - (t / duration)
        samples.append(val * envelope * 12000)
    return pygame.mixer.Sound(buffer=_pack_samples(samples))

def generate_flip_sound():
    duration = 0.22
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        # Sci-Fi gravity warp sweep (sinusoidal frequency mod)
        freq = 300 + 400 * math.sin(math.pi * t / duration)
        phase = t * freq
        val = 1.0 if (phase % 1.0) < 0.4 else -0.8
        envelope = math.sin(math.pi * t / duration)
        samples.append(val * envelope * 14000)
    return pygame.mixer.Sound(buffer=_pack_samples(samples))

def generate_switch_sound():
    duration = 0.08
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        freq = 880 if t < 0.04 else 1320
        phase = t * freq
        val = 1.0 if (phase % 1.0) < 0.5 else -1.0
        envelope = 1.0 - (t / duration)
        samples.append(val * envelope * 10000)
    return pygame.mixer.Sound(buffer=_pack_samples(samples))

def generate_door_sound():
    duration = 0.35
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    notes = [523.25, 659.25, 783.99, 1046.50]  # C5, E5, G5, C6
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        note_idx = min(len(notes) - 1, int(t / (duration / len(notes))))
        freq = notes[note_idx]
        local_t = t % (duration / len(notes))
        phase = t * freq
        val = 1.0 if (phase % 1.0) < 0.3 else -1.0
        env = 1.0 - (local_t / (duration / len(notes)))
        samples.append(val * env * 9000)
    return pygame.mixer.Sound(buffer=_pack_samples(samples))

def generate_death_sound():
    duration = 0.35
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    noise_val = 0
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        if random.random() < 0.3:
            noise_val = random.uniform(-1.0, 1.0)
        envelope = (1.0 - (t / duration)) ** 1.5
        samples.append(noise_val * envelope * 18000)
    return pygame.mixer.Sound(buffer=_pack_samples(samples))

def generate_victory_sound():
    duration = 0.6
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    # Major triad fanfare: C5, E5, G5, C6
    melody = [(523.25, 0.12), (659.25, 0.12), (783.99, 0.12), (1046.50, 0.24)]
    curr_time = 0.0
    for freq, note_dur in melody:
        note_samples = int(SAMPLE_RATE * note_dur)
        for i in range(note_samples):
            t = i / SAMPLE_RATE
            phase = t * freq
            val = 1.0 if (phase % 1.0) < 0.5 else -1.0
            env = max(0.0, 1.0 - (t / note_dur) * 0.8)
            samples.append(val * env * 11000)
    return pygame.mixer.Sound(buffer=_pack_samples(samples))

def generate_crate_push_sound():
    duration = 0.12
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        freq = 90 + random.uniform(-20, 20)
        phase = t * freq
        val = 1.0 if (phase % 1.0) < 0.5 else -1.0
        samples.append(val * (1.0 - t / duration) * 7000)
    return pygame.mixer.Sound(buffer=_pack_samples(samples))

def generate_chiptune_bgm():
    """Generates a pleasant 16-second retro space chiptune loop."""
    bpm = 130
    beat_dur = 60.0 / bpm
    total_beats = 32
    duration = total_beats * beat_dur
    num_samples = int(SAMPLE_RATE * duration)
    samples = [0.0] * num_samples

    # Bassline notes (MIDI notes converted to Hz)
    def midi_to_hz(n):
        return 440.0 * (2.0 ** ((n - 69) / 12.0))

    # Bass progression (A minor style sci-fi: Am, F, C, G)
    bass_prog = [57, 57, 57, 60,  53, 53, 53, 55,  48, 48, 48, 52,  55, 55, 55, 53] # 2 beats each
    lead_melody = [
        69, 72, 76, 72, 74, 76, 74, 72,
        65, 69, 72, 69, 71, 72, 71, 69,
        60, 64, 67, 64, 67, 71, 67, 64,
        67, 71, 74, 71, 74, 76, 74, 71
    ]

    for b in range(total_beats):
        b_start = int(b * beat_dur * SAMPLE_RATE)
        b_len = int(beat_dur * SAMPLE_RATE)

        # Lead note
        lead_pitch = midi_to_hz(lead_melody[b % len(lead_melody)])
        # Bass note
        bass_pitch = midi_to_hz(bass_prog[(b // 2) % len(bass_prog)])

        for i in range(b_len):
            idx = b_start + i
            if idx >= num_samples:
                break
            t = i / SAMPLE_RATE

            # Lead square wave (duty cycle 25%)
            lead_val = (1.0 if ((t * lead_pitch) % 1.0) < 0.25 else -1.0) * max(0.0, 1.0 - (t / beat_dur) * 0.9)
            # Bass triangle wave
            bass_phase = (t * bass_pitch) % 1.0
            bass_val = (4.0 * abs(bass_phase - 0.5) - 1.0) * 0.9

            # Hi-hat on every 8th note
            hat_val = 0.0
            if (i % int(b_len / 2)) < int(SAMPLE_RATE * 0.03):
                hat_val = random.uniform(-0.5, 0.5) * 0.3

            samples[idx] += (lead_val * 0.22 + bass_val * 0.35 + hat_val) * 10000

    return pygame.mixer.Sound(buffer=_pack_samples(samples))

class SoundManager:
    def __init__(self):
        self.enabled = True
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=1024)
            self.jump = generate_jump_sound()
            self.flip = generate_flip_sound()
            self.switch = generate_switch_sound()
            self.door = generate_door_sound()
            self.death = generate_death_sound()
            self.win = generate_victory_sound()
            self.push = generate_crate_push_sound()
            self.bgm = generate_chiptune_bgm()
            self.bgm_channel = pygame.mixer.Channel(0)
            self.bgm_playing = False
        except Exception as e:
            print("Audio initialization warning:", e)
            self.enabled = False

    def play(self, sound_name):
        if not self.enabled:
            return
        sound_map = {
            "jump": self.jump,
            "flip": self.flip,
            "switch": self.switch,
            "door": self.door,
            "death": self.death,
            "win": self.win,
            "push": self.push
        }
        if sound_name in sound_map:
            try:
                sound_map[sound_name].play()
            except Exception:
                pass

    def start_music(self):
        if self.enabled and not self.bgm_playing:
            try:
                self.bgm_channel.play(self.bgm, loops=-1)
                self.bgm_channel.set_volume(0.35)
                self.bgm_playing = True
            except Exception:
                pass

    def stop_music(self):
        try:
            self.bgm_channel.pause()
            self.bgm_playing = False
        except Exception:
            pass

    def start_music(self):
        if self.enabled:
            try:
                if not self.bgm_playing:
                    self.bgm_channel.unpause()
                    if not self.bgm_channel.get_busy():
                        self.bgm_channel.play(self.bgm, loops=-1)
                    self.bgm_channel.set_volume(0.35)
                    self.bgm_playing = True
            except Exception:
                pass

    def toggle(self):
        self.enabled = not self.enabled
        if not self.enabled:
            self.stop_music()
        else:
            self.start_music()
        return self.enabled
