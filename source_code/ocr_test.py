import win32com.client
from PIL import ImageGrab
import tkinter as tk
from tkinter import ttk

class OCRTest:
    def __init__(self, root):
        self.root = root
        self.ocr_engine = None
        self.setup_ui()

    def setup_ui(self):
        frame = ttk.Frame(self.root)
        frame.pack(padx=10, pady=10)

        test_button = ttk.Button(frame, text="Test OCR", command=self.test_ocr)
        test_button.pack(pady=5)

        self.result_label = ttk.Label(frame, text="")
        self.result_label.pack(pady=5)

    def test_ocr(self):
        try:
            self.ocr_engine = win32com.client.Dispatch("Windows.Media.Ocr.OcrEngine")
            screenshot = ImageGrab.grab(bbox=(100, 100, 400, 400))  # Adjust the region as needed
            screenshot.save("temp.png")  # Save temporarily for OCR
            ocr_result = self.ocr_engine.Recognize("temp.png")
            self.result_label.config(text=f"OCR Result: {ocr_result.Text}")
        except Exception as e:
            self.result_label.config(text=f"OCR Test Failed: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Windows OCR Test")
    app = OCRTest(root)
    root.mainloop()