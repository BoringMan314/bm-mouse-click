import math
import wave
import struct


def main():
    sample_rate = 44100
    duration = 0.06
    freq = 1400.0
    total = int(sample_rate * duration)
    frames = []
    for i in range(total):
        env = 1.0 - (i / total)
        v = int(32767 * 0.35 * env * math.sin(2 * math.pi * freq * (i / sample_rate)))
        frames.append(struct.pack("<h", v))
    with wave.open("switch.wav", "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"".join(frames))
    print("generated switch.wav")


if __name__ == "__main__":
    main()
