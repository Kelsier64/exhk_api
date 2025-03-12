from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import uuid
from img_processor import ExamProcessor
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'imgs'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        new_filename = f"{uuid.uuid4().hex}{os.path.splitext(filename)[1]}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
        processor.main(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
        return jsonify({'message': 'File successfully uploaded', 'filename': new_filename}), 200
    else:
        return jsonify({'error': 'File type not allowed'}), 400

if __name__ == '__main__':
    processor = ExamProcessor()
    app.run(debug=True)