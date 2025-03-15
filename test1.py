from img_processor import ExamProcessor
from gtts import gTTS
import os

processor = ExamProcessor()

for ans in processor.main("math/image1.png"):
    print("generated:" + ans)
    tts = gTTS(text=ans, lang='en')
    tts.save("answer.mp3")