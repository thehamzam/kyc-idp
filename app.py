"""Flask app for KYC document extraction - POC."""
import os
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
from models import UploadedFile
from fireworks_client import extract_document, check_api, ExtractionError
from auth import auth_bp, login_required
from db import init_db, create_submission, get_submissions_by_user, get_submission_by_id, delete_submission

load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

app.register_blueprint(auth_bp)
init_db()


@app.route('/')
@login_required
def index():
    return render_template('index.html', username=session.get('username'))


@app.route('/upload', methods=['POST'])
@login_required
def upload():
    """Handle single document upload."""
    if 'file' not in request.files or request.files['file'].filename == '':
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    uploaded = UploadedFile(filename=file.filename, content_type=file.content_type or 'application/octet-stream', data=file.read())
    
    valid, error = uploaded.validate()
    if not valid:
        return jsonify({'success': False, 'error': error}), 400
    
    try:
        result = extract_document(uploaded.data, uploaded.content_type)
        user_id = session.get('user_id')
        if user_id:
            create_submission(user_id, uploaded.filename, uploaded.content_type, result.to_dict(), uploaded.to_data_url())
        return jsonify({'success': True, 'data': result.to_dict(), 'image_data': uploaded.to_data_url()})
    except ExtractionError as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/upload-bulk', methods=['POST'])
@login_required
def upload_bulk():
    """Handle bulk document upload."""
    if 'files[]' not in request.files:
        return jsonify({'success': False, 'error': 'No files uploaded'}), 400
    
    files = request.files.getlist('files[]')
    if not files or all(f.filename == '' for f in files):
        return jsonify({'success': False, 'error': 'No files selected'}), 400
    
    user_id = session.get('user_id')
    results = []
    
    for file in files:
        if file.filename == '':
            continue
        results.append(process_file(file, user_id))
    
    succeeded = sum(1 for r in results if r['success'])
    return jsonify({
        'success': True,
        'results': results,
        'summary': {'total': len(results), 'succeeded': succeeded, 'failed': len(results) - succeeded}
    })


def process_file(file, user_id):
    """Process single file for extraction."""
    try:
        uploaded = UploadedFile(filename=file.filename, content_type=file.content_type or 'application/octet-stream', data=file.read())
        valid, error = uploaded.validate()
        if not valid:
            return {'filename': file.filename, 'success': False, 'error': error}
        
        result = extract_document(uploaded.data, uploaded.content_type)
        submission = None
        if user_id:
            submission = create_submission(user_id, uploaded.filename, uploaded.content_type, result.to_dict(), uploaded.to_data_url())
        return {'filename': file.filename, 'success': True, 'data': result.to_dict(), 'submission_id': submission.id if submission else None}
    except Exception as e:
        return {'filename': file.filename, 'success': False, 'error': str(e)}


@app.route('/submissions')
@login_required
def list_submissions():
    submissions = get_submissions_by_user(session.get('user_id'))
    return jsonify({'success': True, 'submissions': [s.to_list_item() for s in submissions]})


@app.route('/submissions/<int:id>')
@login_required
def get_submission(id):
    submission = get_submission_by_id(id, session.get('user_id'))
    if not submission:
        return jsonify({'success': False, 'error': 'Not found'}), 404
    return jsonify({'success': True, 'submission': submission.to_dict()})


@app.route('/submissions/<int:id>', methods=['DELETE'])
@login_required
def remove_submission(id):
    if not delete_submission(id, session.get('user_id')):
        return jsonify({'success': False, 'error': 'Not found'}), 404
    return jsonify({'success': True})


@app.route('/health')
def health():
    ok, msg = check_api()
    return jsonify({'status': 'healthy' if ok else 'degraded', 'api_configured': ok, 'message': msg})


if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    ok, msg = check_api()
    if not ok:
        print(f"WARNING: {msg}")
    print(f"Starting server on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') == 'development')
