from flask import Flask, request, jsonify, send_file
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/file_sharing'
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pptx', 'docx', 'xlsx'}

mongo = PyMongo(app)
jwt = JWTManager(app)

# Define a helper function to check file extension
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Add user registration logic here (including encryption)
    # You can use PyMongo to interact with MongoDB to insert the user data
    
    return jsonify({'message': 'User registered successfully'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Add user authentication logic here
    # If authentication is successful, generate an access token
    access_token = create_access_token(identity=username)
    
    return jsonify({'access_token': access_token})

@app.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'})

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        user_id = get_jwt_identity()
        
        # Save the file to the server or cloud storage (e.g., AWS S3)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # Insert the file metadata into MongoDB
        mongo.db.files.insert_one({'filename': filename, 'user_id': user_id})
        
        return jsonify({'message': 'File uploaded successfully'})
    else:
        return jsonify({'message': 'File upload failed. Invalid file type'})

@app.route('/download/<filename>', methods=['GET'])
@jwt_required()
def download_file(filename):
    user_id = get_jwt_identity()
    
    # Check if the user has permission to download this file
    file = mongo.db.files.find_one({'filename': filename, 'user_id': user_id})
    if not file:
        return jsonify({'message': 'File not found or permission denied'})
    
    # Serve the file for download (adjust the path accordingly)
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

@app.route('/list_files', methods=['GET'])
@jwt_required()
def list_files():
    user_id = get_jwt_identity()
    
    # Retrieve a list of uploaded files for the authenticated user
    files = mongo.db.files.find({'user_id': user_id})
    file_list = [file['filename'] for file in files]
    
    return jsonify({'files': file_list})

if __name__ == '__main__':
    app.run(debug=True)
