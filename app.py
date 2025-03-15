from flask import Flask, request, jsonify
import os
from img_processor import ExamProcessor
from datetime import datetime



app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'imgs'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

processor = ExamProcessor()

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
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')  # generate timestamp
        new_filename = f"{timestamp}{os.path.splitext(file.filename)[1]}"  # create new filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
        processor.main(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
        return jsonify({'message': 'File successfully uploaded', 'filename': new_filename}), 200
    else:
        return jsonify({'error': 'File type not allowed'}), 400

@app.route('/reload', methods=['GET'])
def reload_processor():
    global processor
    processor = ExamProcessor()
    return jsonify({'message': 'Processor reloaded'}), 200

if __name__ == '__main__':
    app.run(debug=True)