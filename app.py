from flask import Flask, request, jsonify, session
from flask_cors import CORS
from config import Config
from models import db, User, Story, Poem
from werkzeug.exceptions import BadRequest

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
# CORS(app, supports_credentials=True)
CORS(
    app,
    supports_credentials=True,
    # resources={r"/api/*"},
    expose_headers=["X-User-Id", "X-Role", "X-Is-Logged-In"],
    allow_headers=["Content-Type", "X-User-Id", "X-Role", "X-Is-Logged-In"]
)

app.secret_key = '1e0f8ec42d90b9bce555c440b39a7f2bd8a7c7102844d42b416c2aa9aa44963b'  # Needed for session management

# def get_current_user():
#     user_id = session.get('user_id')
#     if not user_id:
#         return None
#     return user_id
#     # Helper to get user_id from frontend session storage (sent via request headers)
    
def get_current_user():
    """Read the user’s ID out of a custom request header."""
    user_id = request.headers.get("X-User-Id")
    try:
        return int(user_id) if user_id else None
    except ValueError:
        return None
    
def get_current_role():
    """Read the user’s role out of a custom request header."""
    role = request.headers.get("X-Role")
    return role if role else None

# ========== Routes ==========

# Authentication check route
@app.route('/api/auth-check', methods=['GET'])
def auth_check():
    user_id = get_current_user()
    if not user_id:
        return jsonify({'authenticated': False}), 401

    user = User.query.get(user_id)
    if not user or not user.is_active or (user.role=='Writer' and not user.is_approved):
        return jsonify({'authenticated': False}), 403

    return jsonify({
        'authenticated': True,
        'user_id': user.id,
        'role': user.role,
        'is_active': user.is_active,
        'is_approved': user.is_approved
    })



# Register route to create a new user
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or 'email' not in data or 'roles' not in data:
        return jsonify({'message': 'Missing required fields'}), 400

    # Check if a user with the same email and role already exists
    existing_user = User.query.filter_by(email=data['email'], role=data['roles']).first()
    if existing_user:
        return jsonify({'message': f"User already registered with role '{data['roles']}' using this email."}), 400

    user = User(
        full_name=data['full_name'],
        email=data['email'],
        mobile=data['mobile'],
        role=data['roles']
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': f"User registered successfully as {data['roles']}."}), 201



# Login route to authenticate users
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'email' not in data or 'roles' not in data or 'password' not in data:
        raise BadRequest("Missing 'email', 'roles', or 'password' in the request body.")

    user = User.query.filter_by(email=data['email'], role=data['roles']).first()
    if user and user.check_password(data['password']):
        session['user_id'] = user.id
        return jsonify({'message': 'Login successful','user_id': user.id}), 200

    return jsonify({'message': 'Invalid credentials'}), 401


# Logout route to clear session
@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out'})


# Create a new story
@app.route('/api/story', methods=['POST'])
def create_story():
    user_id = get_current_user()
    if not user_id:
        return jsonify({'message': 'Authentication required'}), 401

    if request.is_json:
        data = request.get_json()
        pdf_url = ''
    else:
        data = request.form
        pdf_file = request.files.get('pdf')
        pdf_url = ''  # Save the file logic here

    price = data.get('price', 0.00)
    status = data.get('status', 'published')
    tags = data.get('tags', '')  # 🆕 Get tags from payload

    story = Story(
        WRITTEN_BY=user_id,
        NAME=data['name'],
        LANGUAGE=data['language'],
        FONT=data['font'],
        PDF_URL=pdf_url,
        STORY=data['story'],
        STATUS=status,
        PRICE=price,
        TAGS=tags  # 🆕 Set tags
    )
    db.session.add(story)
    db.session.commit()
    return jsonify({'message': 'Story created successfully'})


# Get a specific story by ID
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
        'price': float(story.PRICE),
        'tags': story.TAGS,  # 🆕 Include tags
        'created_on': story.CREATED_ON.isoformat() if story.CREATED_ON else None,
        'updated_on': story.UPDATED_ON.isoformat() if story.UPDATED_ON else None
    })


# Get all stories
@app.route('/api/stories', methods=['GET'])
def get_all_stories():
    stories = Story.query.all()
    return jsonify([{
        'id': story.STORY_ID,
        'authorId': story.WRITTEN_BY,
        'name': story.NAME,
        'language': story.LANGUAGE,
        'font': story.FONT,
        'pdf_url': story.PDF_URL,
        'story': story.STORY,
        'status': story.STATUS,
        'price': float(story.PRICE),
        'tags': story.TAGS,  # 🆕 Include tags
        'created_on': story.CREATED_ON.isoformat() if story.CREATED_ON else None,
        'updated_on': story.UPDATED_ON.isoformat() if story.UPDATED_ON else None
    } for story in stories])


# Create a new poem
@app.route('/api/poem', methods=['POST'])
def create_poem():
    user_id = get_current_user()
    if not user_id:
        return jsonify({'message': 'Authentication required'}), 401

    data = request.json
    price = data.get('price', 0.00)
    status = data.get('status', 'published')
    tags = data.get('tags', '')  # 🆕 Get tags

    poem = Poem(
        WRITTEN_BY=user_id,
        NAME=data['name'],
        LANGUAGE=data['language'],
        FONT=data['font'],
        PDF_URL=data.get('pdf_url', ''),
        STORY=data['story'],
        STATUS=status,
        PRICE=price,
        TAGS=tags  # 🆕 Set tags
    )
    db.session.add(poem)
    db.session.commit()
    return jsonify({'message': 'Poem created successfully'})


# Get a specific poem by ID
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
        'price': float(poem.PRICE),
        'tags': poem.TAGS,  # 🆕 Include tags
        'created_on': poem.CREATED_ON.isoformat() if poem.CREATED_ON else None,
        'updated_on': poem.UPDATED_ON.isoformat() if poem.UPDATED_ON else None
    })


# Get all poems
@app.route('/api/poems', methods=['GET'])
def get_all_poems():
    poems = Poem.query.all()
    return jsonify([{
        'id': poem.STORY_ID,
        'authorId': poem.WRITTEN_BY,
        'name': poem.NAME,
        'language': poem.LANGUAGE,
        'font': poem.FONT,
        'pdf_url': poem.PDF_URL,
        'story': poem.STORY,
        'status': poem.STATUS,
        'price': float(poem.PRICE),
        'tags': poem.TAGS,  # 🆕 Include tags
        'created_on': poem.CREATED_ON.isoformat() if poem.CREATED_ON else None,
        'updated_on': poem.UPDATED_ON.isoformat() if poem.UPDATED_ON else None
    } for poem in poems])


# Forgot Password
@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.form
    return jsonify({'message': f"Reset link sent to {data['email']} (mock response)"})


# Activate or Deactivate a user
@app.route('/api/user/<int:user_id>/status', methods=['PATCH'])
def toggle_user_status(user_id):
    data = request.get_json()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    user.is_active = data.get('is_active', user.is_active)
    db.session.commit()
    return jsonify({'message': f"User {'activated' if user.is_active else 'deactivated'} successfully"})


# Approve or Reject a user
@app.route('/api/user/<int:user_id>/approval', methods=['PATCH'])
def set_user_approval(user_id):
    data = request.get_json()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    user.is_approved = data.get('is_approved', user.is_approved)
    db.session.commit()
    return jsonify({'message': f"User {'approved' if user.is_approved else 'rejected'} successfully"})


# View all users (optionally filter by role or approval status)
@app.route('/api/users', methods=['GET'])
def view_users():
    role = request.args.get('role')
    approved = request.args.get('approved')

    query = User.query
    if role:
        query = query.filter_by(role=role)
    if approved is not None:
        query = query.filter_by(is_approved=(approved.lower() == 'true'))

    users = query.all()
    return jsonify([{
        'id': user.id,
        'full_name': user.full_name,
        'email': user.email,
        'mobile': user.mobile,
        'role': user.role,
        'is_active': user.is_active,
        'is_approved': user.is_approved,
        'created_on': user.created_on,
        'updated_on': user.updated_on,
    } for user in users])


# Edit user information
@app.route('/api/user/<int:user_id>', methods=['PUT'])
def edit_user(user_id):
    data = request.get_json()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    user.full_name = data.get('full_name', user.full_name)
    user.email = data.get('email', user.email)
    user.mobile = data.get('mobile', user.mobile)
    user.role = data.get('role', user.role)
    if 'password' in data:
        user.set_password(data['password'])

    db.session.commit()
    return jsonify({'message': 'User updated successfully'})


# View all draft stories (no auth required for Admin, but required for others)
@app.route('/api/story/drafts', methods=['GET'])
def view_draft_stories():
    user_id = get_current_user()  # Returns None if no auth
    # Optionally, you could also check for role if needed:
    # role = request.args.get('role')

    if user_id:
        drafts = Story.query.filter_by(WRITTEN_BY=user_id, STATUS='draft').all()
    else:
        return jsonify({'message': 'Authentication required'}), 401

    return jsonify([{
        'id': story.STORY_ID,
        'name': story.NAME,
        'tags': story.TAGS,  # 🆕 Include tags
        'language': story.LANGUAGE,
        'font': story.FONT,
        'pdf_url': story.PDF_URL,
        'story': story.STORY,
        'price': float(story.PRICE),
        'created_on': story.CREATED_ON.isoformat() if story.CREATED_ON else None,
        'updated_on': story.UPDATED_ON.isoformat() if story.UPDATED_ON else None
    } for story in drafts])

# Edit a draft story
@app.route('/api/story/<int:id>', methods=['PUT'])
def edit_draft_story(id):
    user_id = get_current_user()
    role = get_current_role()
    if not user_id:
        return jsonify({'message': 'Authentication required'}), 401

    story = Story.query.get(id)
    if not story:
        return jsonify({'message': 'Draft story not found or access denied'}), 404
    
    # Allow only the author or Admin to edit
    if story.WRITTEN_BY != user_id and role != 'Admin':
        print(f"User {user_id} attempted to edit story with role {role} and id {id} without permission.")
        return jsonify({'message': 'Access denied'}), 403
    
    if story.STATUS != 'draft':
        return jsonify({'message': 'Only draft stories can be edited'}), 400

    data = request.json
    story.NAME = data.get('name', story.NAME)
    story.LANGUAGE = data.get('language', story.LANGUAGE)
    story.FONT = data.get('font', story.FONT)
    story.PDF_URL = data.get('pdf_url', story.PDF_URL)
    story.STORY = data.get('story', story.STORY)
    story.PRICE = data.get('price', story.PRICE)
    
    db.session.commit()
    return jsonify({'message': 'Draft story updated successfully'})


# Delete a draft story
@app.route('/api/story/<int:id>', methods=['DELETE'])
def delete_draft_story(id):
    user_id = get_current_user()
    role = get_current_role()
    
    if not user_id:
        return jsonify({'message': 'Authentication required'}), 401

    story = Story.query.get(id)
    if not story:
        return jsonify({'message': 'Draft story not found'}), 404
    
    if story.STATUS != 'draft':
        return jsonify({'message': 'Only draft stories can be deleted'}), 400

    # Allow Admins to delete any draft, otherwise only the author
    if role != 'Admin' and story.WRITTEN_BY != user_id:
        return jsonify({'message': 'Access denied'}), 403

    db.session.delete(story)
    db.session.commit()
    return jsonify({'message': 'Draft story deleted successfully'})

# Delete a published story
@app.route('/api/story/<int:id>/published', methods=['DELETE'])
def delete_published_story(id):
    user_id = get_current_user()
    role = get_current_role()

    if not user_id:
        return jsonify({'message': 'Authentication required'}), 401

    story = Story.query.get(id)
    if not story:
        return jsonify({'message': 'Story not found'}), 404

    if story.STATUS != 'published':
        return jsonify({'message': 'Only published stories can be deleted'}), 400

    # Only Admins can delete published stories
    if role != 'Admin':
        return jsonify({'message': 'Access denied - Only Admins can delete published stories'}), 403

    db.session.delete(story)
    db.session.commit()
    return jsonify({'message': 'Published story deleted successfully'})

# Approve (publish) a draft story
@app.route('/api/story/<int:id>/approve', methods=['POST'])
def approve_story(id):
    user_id = get_current_user()
    role = get_current_role()
    if not user_id:
        return jsonify({'message': 'Authentication required'}), 401

    # Get the current user (to check if they're an admin)
    if not user_id or role != 'Admin':  # Ensure only admins can approve
        return jsonify({'message': 'Unauthorized - Admin access required'}), 403

    story = Story.query.get(id)
    if not story:
        return jsonify({'message': 'Story not found'}), 404
    if story.STATUS != 'pending':
        return jsonify({'message': 'Only pending stories can be approved'}), 400

    data = request.json
    story.STATUS = 'published'
    story.PRICE = data.get('price', story.PRICE)
    story.UPDATED_ON = db.func.now()
    db.session.commit()
    return jsonify({'message': 'Story published successfully'})


# View all draft poems (no auth required for Admin, but required for others)
@app.route('/api/poem/drafts', methods=['GET'])
def view_draft_poems():
    user_id = get_current_user()  # Returns None if no auth
    
    # Allow access without auth ONLY if Admin (user_id=5)
    if user_id == 5:
        drafts = Poem.query.filter_by(STATUS='draft').all()  # Admin sees ALL drafts
    else:
        if not user_id:
            return jsonify({'message': 'Authentication required'}), 401
        drafts = Poem.query.filter_by(WRITTEN_BY=user_id, STATUS='draft').all()  # Users see only their drafts

    return jsonify([{
        'id': poem.STORY_ID,
        'author_id': poem.WRITTEN_BY,
        'name': poem.NAME,
        'tags': poem.TAGS,  # 🆕 Include tags
        'language': poem.LANGUAGE,
        'font': poem.FONT,
        'pdf_url': poem.PDF_URL,
        'story': poem.STORY,
        'price': float(poem.PRICE),
        'created_on': poem.CREATED_ON.isoformat() if poem.CREATED_ON else None,
        'updated_on': poem.UPDATED_ON.isoformat() if poem.UPDATED_ON else None
    } for poem in drafts])


# Edit a draft poem
@app.route('/api/poem/<int:id>', methods=['PUT'])
def edit_draft_poem(id):
    user_id = get_current_user()
    if not user_id:
        return jsonify({'message': 'Authentication required'}), 401

    poem = Poem.query.get(id)
    if not poem or poem.WRITTEN_BY != user_id or poem.STATUS != 'draft':
        return jsonify({'message': 'Draft poem not found or access denied'}), 404

    data = request.json
    poem.NAME = data.get('name', poem.NAME)
    poem.LANGUAGE = data.get('language', poem.LANGUAGE)
    poem.FONT = data.get('font', poem.FONT)
    poem.PDF_URL = data.get('pdf_url', poem.PDF_URL)
    poem.STORY = data.get('story', poem.STORY)
    poem.PRICE = data.get('price', poem.PRICE)
    db.session.commit()
    return jsonify({'message': 'Draft poem updated successfully'})


# Delete a draft poem
@app.route('/api/poem/<int:id>', methods=['DELETE'])
def delete_draft_poem(id):
    user = get_current_user()
    if not user:
        return jsonify({'message': 'Authentication required'}), 401

    current_user = User.query.get(user)
    poem = Poem.query.get(id)
    if not poem or poem.STATUS != 'draft':
        return jsonify({'message': 'Draft poem not found'}), 404

    # Allow Admins to delete any draft, otherwise only the author
    if current_user.role != 'Admin' and poem.WRITTEN_BY != user:
        return jsonify({'message': 'Access denied'}), 403

    db.session.delete(poem)
    db.session.commit()
    return jsonify({'message': 'Draft poem deleted successfully'})

# Delete a published poem
@app.route('/api/poem/<int:id>/published', methods=['DELETE'])
def delete_published_poem(id):
    user_id = get_current_user()
    role = get_current_role()

    if not user_id:
        return jsonify({'message': 'Authentication required'}), 401

    poem = Poem.query.get(id)
    if not poem:
        return jsonify({'message': 'Poem not found'}), 404

    if poem.STATUS != 'published':
        return jsonify({'message': 'Only published poems can be deleted'}), 400

    # Only Admins can delete published poems
    if role != 'Admin':
        return jsonify({'message': 'Access denied - Only Admins can delete published poems'}), 403

    db.session.delete(poem)
    db.session.commit()
    return jsonify({'message': 'Published poem deleted successfully'})

# Approve (publish) a draft poem
@app.route('/api/poem/<int:id>/approve', methods=['POST'])
def approve_poem(id):
    user_id = get_current_user()
    role = get_current_role()
    if not user_id:
        return jsonify({'message': 'Authentication required'}), 401

    if role != 'Admin':
        return jsonify({'message': 'Unauthorized - Admin access required'}), 403

    poem = Poem.query.get(id)
    
    if not poem:
        return jsonify({'message': 'Poem not found'}), 404
    
    if poem.STATUS != 'pending':
        return jsonify({'message': 'Only pending poems can be approved'}), 400

    data = request.json
    poem.PRICE = data.get('price', poem.PRICE)
    poem.STATUS = 'published'
    db.session.commit()
    return jsonify({'message': 'Poem published successfully'})


# Admin route to create a new user
@app.route('/api/admin/create-user', methods=['POST'])
def admin_create_user():
    # Check if the requester is an admin
    user_id = get_current_user()
    if not user_id:
        return jsonify({'message': 'Authentication required'}), 401
    
    current_user = User.query.get(user_id)
    if not current_user or current_user.role != 'Admin':
        return jsonify({'message': 'Unauthorized - Admin access required'}), 403

    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({'message': 'Missing required fields'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already exists'}), 400

    # Map the user type from the form to your role values
    role_mapping = {
        'Reader': 'Reader',
        'Writer': 'Writer'
    }
    
    role = role_mapping.get(data.get('user_type'))
    if not role:
        return jsonify({'message': 'Invalid user type'}), 400

    user = User(
        full_name=data['full_name'],
        email=data['email'],
        mobile=data['mobile'],
        role=role,
        is_active=True,
        is_approved=True  # Auto-approve admin-created users
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'message': 'User created successfully',
        'user_id': user.id
    }), 201


# Get all stories by user ID
@app.route('/api/stories/user/<int:user_id>', methods=['GET'])
def get_stories_by_user(user_id):
    stories = Story.query.filter_by(WRITTEN_BY=user_id).all()
    return jsonify([{
        'id': story.STORY_ID,
        'name': story.NAME,
        'tags': story.TAGS,  # 🆕 Include tags
        'language': story.LANGUAGE,
        'font': story.FONT,
        'pdf_url': story.PDF_URL,
        'story': story.STORY,
        'status': story.STATUS,
        'price': float(story.PRICE),
        'created_on': story.CREATED_ON.isoformat() if story.CREATED_ON else None,
        'updated_on': story.UPDATED_ON.isoformat() if story.UPDATED_ON else None
    } for story in stories])

# Get all poems by user ID
@app.route('/api/poems/user/<int:user_id>', methods=['GET'])
def get_poems_by_user(user_id):
    poems = Poem.query.filter_by(WRITTEN_BY=user_id).all()
    return jsonify([{
        'id': poem.STORY_ID,
        'name': poem.NAME,
        'tags': poem.TAGS,  # 🆕 Include tags
        'language': poem.LANGUAGE,
        'font': poem.FONT,
        'pdf_url': poem.PDF_URL,
        'story': poem.STORY,
        'status': poem.STATUS,
        'price': float(poem.PRICE),
        'created_on': poem.CREATED_ON.isoformat() if poem.CREATED_ON else None,
        'updated_on': poem.UPDATED_ON.isoformat() if poem.UPDATED_ON else None
    } for poem in poems])

# Reject (unpublish) a published poem - set status back to 'pending'
@app.route('/api/poem/<int:id>/reject', methods=['POST'])
def reject_poem(id):
    user_id = get_current_user()
    role = get_current_role()

    if not user_id:
        return jsonify({'message': 'Authentication required'}), 401

    if role != 'Admin':
        return jsonify({'message': 'Unauthorized - Admin access required'}), 403

    poem = Poem.query.get(id)
    if not poem:
        return jsonify({'message': 'Poem not found'}), 404

    if poem.STATUS != 'published':
        return jsonify({'message': 'Only published poems can be rejected'}), 400

    poem.STATUS = 'pending'
    poem.UPDATED_ON = db.func.now()
    db.session.commit()

    return jsonify({'message': 'Poem status set to pending (rejected)'})

# Reject (unpublish) a published story - set status back to 'pending'
@app.route('/api/story/<int:id>/reject', methods=['POST'])
def reject_story(id):
    user_id = get_current_user()
    role = get_current_role()

    if not user_id:
        return jsonify({'message': 'Authentication required'}), 401

    if role != 'Admin':
        return jsonify({'message': 'Unauthorized - Admin access required'}), 403

    story = Story.query.get(id)
    if not story:
        return jsonify({'message': 'Story not found'}), 404

    if story.STATUS != 'published':
        return jsonify({'message': 'Only published stories can be rejected'}), 400

    story.STATUS = 'pending'
    story.UPDATED_ON = db.func.now()
    db.session.commit()

    return jsonify({'message': 'Story status set to pending (rejected)'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
