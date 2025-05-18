from flask import Flask, request, jsonify, session
from flask_cors import CORS
from config import Config
from models import db, User, Story, Poem
from werkzeug.exceptions import BadRequest

app = Flask(__name__)  # Corrected from **name**
app.config.from_object(Config)
app.secret_key = 'your-secret-key'  # Needed for session management

CORS(app, supports_credentials=True)  # Enable CORS and support cookies (session)

db.init_app(app)

# ========== Routes ==========

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({'message': 'Missing required fields'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already exists'}), 400

    user = User(
        full_name=data['full_name'],
        email=data['email'],
        mobile=data['mobile'],
        role=data['roles']
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'})


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'email' not in data or 'roles' not in data or 'password' not in data:
        raise BadRequest("Missing 'email', 'roles', or 'password' in the request body.")

    user = User.query.filter_by(email=data['email'], role=data['roles']).first()
    if user and user.check_password(data['password']):
        session['user_id'] = user.id
        return jsonify({'message': 'Login successful'}), 200

    return jsonify({'message': 'Invalid credentials'}), 401


@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out'})


@app.route('/api/story', methods=['POST'])
def create_story():
    if 'user_id' not in session:
        return jsonify({'message': 'Authentication required'}), 401

    data = request.json
    price = data.get('price', 0.00)
    status = data.get('status', 'published')

    story = Story(
        WRITTEN_BY=session['user_id'],
        NAME=data['name'],
        LANGUAGE=data['language'],
        FONT=data['font'],
        PDF_URL=data.get('pdf_url', ''),
        STORY=data['story'],
        STATUS=status,
        PRICE=price
    )
    db.session.add(story)
    db.session.commit()
    return jsonify({'message': 'Story created successfully'})


@app.route('/api/story/<int:id>', methods=['GET'])
def get_story(id):
    story = Story.query.get(id)
    if not story:
        return jsonify({'message': 'Story not found'}), 404

    return jsonify({
        'id': story.STORY_ID,
        'name': story.NAME,
        'language': story.LANGUAGE,
        'font': story.FONT,
        'pdf_url': story.PDF_URL,
        'story': story.STORY,
        'status': story.STATUS,
        'price': float(story.PRICE)
    })


@app.route('/api/stories', methods=['GET'])
def get_all_stories():
    stories = Story.query.all()
    return jsonify([{
        'id': story.STORY_ID,
        'name': story.NAME,
        'language': story.LANGUAGE,
        'font': story.FONT,
        'pdf_url': story.PDF_URL,
        'story': story.STORY,
        'status': story.STATUS,
        'price': float(story.PRICE)
    } for story in stories])


@app.route('/api/poem', methods=['POST'])
def create_poem():
    if 'user_id' not in session:
        return jsonify({'message': 'Authentication required'}), 401

    data = request.json
    price = data.get('price', 0.00)
    status = data.get('status', 'published')

    poem = Poem(
        WRITTEN_BY=session['user_id'],
        NAME=data['name'],
        LANGUAGE=data['language'],
        FONT=data['font'],
        PDF_URL=data.get('pdf_url', ''),
        STORY=data['story'],
        STATUS=status,
        PRICE=price
    )
    db.session.add(poem)
    db.session.commit()
    return jsonify({'message': 'Poem created successfully'})


@app.route('/api/poem/<int:id>', methods=['GET'])
def get_poem(id):
    poem = Poem.query.get(id)
    if not poem:
        return jsonify({'message': 'Poem not found'}), 404

    return jsonify({
        'id': poem.STORY_ID,
        'name': poem.NAME,
        'language': poem.LANGUAGE,
        'font': poem.FONT,
        'pdf_url': poem.PDF_URL,
        'story': poem.STORY,
        'status': poem.STATUS,
        'price': float(poem.PRICE)
    })


@app.route('/api/poems', methods=['GET'])
def get_all_poems():
    poems = Poem.query.all()
    return jsonify([{
        'id': poem.STORY_ID,
        'name': poem.NAME,
        'language': poem.LANGUAGE,
        'font': poem.FONT,
        'pdf_url': poem.PDF_URL,
        'story': poem.STORY,
        'status': poem.STATUS,
        'price': float(poem.PRICE)
    } for poem in poems])


@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.form
    return jsonify({'message': f"Reset link sent to {data['email']} (mock response)"})


# ========== App Start ==========

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
