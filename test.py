from img_processor import ExamProcessor
import os
import base64

if __name__ == "__main__":
    processor = ExamProcessor()
    for i in range(5, 8):
        input("按 Enter 繼續...")
        processor.main(f"physics/image{i}.png")