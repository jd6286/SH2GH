import sys
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox
from PyQt5.QtGui import QPixmap

from pix2pix import sketch_to_image
# from image_to_3d_model import image_to_3d_model
# from music_generation import generate_music

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Sketch to 3D Model and Music Generator')
        
        layout = QVBoxLayout()

        self.sketch_label = QLabel('Upload Sketch:')
        layout.addWidget(self.sketch_label)
        
        self.upload_button = QPushButton('Upload Sketch')
        self.upload_button.clicked.connect(self.upload_sketch)
        layout.addWidget(self.upload_button)

        self.keyword_label = QLabel('Enter Keywords:')
        layout.addWidget(self.keyword_label)
        
        self.keyword_input = QLineEdit(self)
        layout.addWidget(self.keyword_input)
        
        self.generate_button = QPushButton('Generate')
        self.generate_button.clicked.connect(self.generate_content)
        layout.addWidget(self.generate_button)
        
        self.image_label = QLabel('Generated Image:')
        layout.addWidget(self.image_label)
        
        self.result_image = QLabel()
        layout.addWidget(self.result_image)
        
        self.model_label = QLabel('3D Model Path:')
        layout.addWidget(self.model_label)
        
        self.music_label = QLabel('Generated Music Path:')
        layout.addWidget(self.music_label)

        self.setLayout(layout)
        
    def upload_sketch(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "", "Images (*.png *.xpm *.jpg)", options=options)
        if file_name:
            self.sketch_path = file_name
            self.sketch_label.setText(f'Sketch: {file_name}')
        
    def generate_content(self):
        if not hasattr(self, 'sketch_path'):
            QMessageBox.warning(self, 'Warning', 'Please upload a sketch first!')
            return
        
        keyword = self.keyword_input.text()
        if not keyword:
            QMessageBox.warning(self, 'Warning', 'Please enter a keyword!')
            return
        
        # Step 1: Generate Image from Sketch
        generated_image = sketch_to_image(self.sketch_path, keyword)
        self.display_image("output/sketch_to_image.jpg")
        # self.display_image(generated_image)
        
        # Step 2: Remove background and create 3D model
        # model_3d = image_to_3d_model(generated_image)
        # self.model_label.setText(f'3D Model Path: {model_3d}')
        
        # Step 3: Generate music based on keywords
        # music = generate_music(keyword)
        # self.music_label.setText(f'Generated Music Path: {music}')
        
    def display_image(self, image_path):
        pixmap = QPixmap(image_path)
        self.result_image.setPixmap(pixmap.scaled(200, 200))

if __name__ == '__main__':
    # 윈도우 표시
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())