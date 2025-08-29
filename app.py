from datetime import datetime
from sqlite3 import IntegrityError
from flask import Flask, json, request, jsonify, session
from flask_cors import CORS
from config import Config
from models import AudioStory, db, User, Story, Poem, Admin, HelpSupport
from werkzeug.exceptions import BadRequest
from werkzeug.utils import secure_filename
from sqlalchemy import func, desc
import os



app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static'
app.config.from_object(Config)
db.init_app(app)
# CORS(app, supports_credentials=True)
CORS(
    app,
    supports_credentials=True,
    # resources={r"/api/*"},
    expose_headers=["X-User-Id", "X-Role", "X-Is-Logged-In"],
    allow_headers=["Content-Type", "X-User-Id", "X-Role", "X-Is-Logged-In", "X-Admin-Id"]
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
    user_id = session.get('user_id')
    if user_id:
        return int(user_id)
    header_user_id = request.headers.get("X-User-Id")
    try:
        return int(header_user_id) if header_user_id else None
    except (ValueError, TypeError):
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

    # Validate required fields
    required_fields = ['full_name', 'email', 'mobile', 'password', 'roles']
    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    if missing_fields:
        return jsonify({'message': f"Missing required fields: {', '.join(missing_fields)}"}), 400

    role = data['roles'].lower()
    if role not in ['reader', 'writer']:
        return jsonify({'message': "Role must be 'reader' or 'writer'."}), 400

    # Check if a user with the same email and role already exists
    existing_user = User.query.filter_by(email=data['email'], role=role).first()
    if existing_user:
        return jsonify({'message': f"User already registered with role '{role}' using this email."}), 400

    # Set active flag: Readers active by default, others inactive
    is_active = True if role == 'reader' else False

    user = User(
        full_name=data['full_name'],
        email=data['email'],
        mobile=data['mobile'],
        role=role,
        is_active=is_active
    )
    user.set_password(data['password'])

    try:
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': f"User registered successfully as {role}."}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': "Database error: possible duplicate entry."}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f"An error occurred: {str(e)}"}), 500



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


# Login route to authenticate admins
@app.route('/admin-login', methods=['POST'])
def admin_login():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        raise BadRequest("Missing 'email' or 'password' in the request body.")

    admin = Admin.query.filter_by(email=data['email']).first()
    if admin and admin.check_password(data['password']):
        session['admin_id'] = admin.id
        return jsonify({
            'message': 'Login successful',
            'admin_id': admin.id,
            'role': admin.role  # 👈 Add role
        }), 200

    return jsonify({'message': 'Invalid credentials'}), 401

# Get current admin profile (convenience endpoint - uses session or header)
@app.route('/api/admin/profile', methods=['GET'])
def get_current_admin_profile():
    admin_id = session.get('admin_id')
    header_admin = request.headers.get('X-Admin-Id')
    if header_admin and header_admin.isdigit():
        admin_id = int(header_admin)

    if not admin_id:
        return jsonify({'message': 'Authentication required'}), 401

    admin = Admin.query.get(admin_id)
    if not admin:
        return jsonify({'message': 'Admin not found'}), 404

    return jsonify({
        'id': admin.id,
        'full_name': admin.full_name,
        'email': admin.email,
        'mobile': admin.mobile,
        'role': admin.role,
        'created_on': admin.created_on.isoformat() if admin.created_on else None,
        'updated_on': admin.updated_on.isoformat() if admin.updated_on else None
    }), 200


# Update admin profile
@app.route('/api/admin/<int:admin_id>', methods=['PUT'])
def update_admin(admin_id):
    data = request.get_json()
    if not data:
        return jsonify({'message': 'Missing JSON body'}), 400

    # Auth: only the admin themselves or super_admin can update
    requester_id = session.get('admin_id')
    header_admin = request.headers.get('X-Admin-Id')
    if header_admin and header_admin.isdigit():
        requester_id = int(header_admin)

    requester = Admin.query.get(requester_id) if requester_id else None
    if requester_id != admin_id and (not requester or requester.role != 'super_admin'):
        return jsonify({'message': 'Access denied'}), 403

    admin = Admin.query.get(admin_id)
    if not admin:
        return jsonify({'message': 'Admin not found'}), 404

    admin.full_name = data.get('full_name', admin.full_name)
    admin.email = data.get('email', admin.email)
    admin.mobile = data.get('mobile', admin.mobile)

    # Commit changes
    db.session.commit()

    # Return a JSON response confirming update
    return jsonify({
        'message': 'Profile updated successfully',
        'admin': {
            'id': admin.id,
            'full_name': admin.full_name,
            'email': admin.email,
            'mobile': admin.mobile
        }
    }), 200

    # optionally allow role change only by super_admin
    # if 'role' in data and requester and requester.role == 'super_admin':
    #     admin.role = data['role']

    # db.session.commit()
    # return jsonify({'message': 'Profile updated successfully'}), 200


# Change password
@app.route('/api/admin/<int:admin_id>/change-password', methods=['POST'])
def admin_change_password(admin_id):
    data = request.get_json()
    if not data or 'current_password' not in data or 'new_password' not in data:
        return jsonify({'message': 'Missing required fields'}), 400

    # Auth (same logic)
    requester_id = session.get('admin_id')
    header_admin = request.headers.get('X-Admin-Id')
    if header_admin and header_admin.isdigit():
        requester_id = int(header_admin)

    if requester_id != admin_id:
        return jsonify({'message': 'Access denied'}), 403

    admin = Admin.query.get(admin_id)
    if not admin:
        return jsonify({'message': 'Admin not found'}), 404

    if not admin.check_password(data['current_password']):
        return jsonify({'message': 'Current password incorrect'}), 401

    admin.set_password(data['new_password'])
    db.session.commit()
    return jsonify({'message': 'Password changed successfully'}), 200

# Logout route to clear session
@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user_id', None)
    session.pop('admin_id', None)
    return jsonify({'message': 'Logged out'})


# Create a new sub-admin (only super_admin can do this)
@app.route('/api/admin/create-subadmin', methods=['POST'])
def create_subadmin():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing JSON body'}), 400

    # Auth: get requester id from session or header
    requester_id = session.get('admin_id')
    header_admin = request.headers.get('X-Admin-Id')
    if header_admin and header_admin.isdigit():
        requester_id = int(header_admin)

    if not requester_id:
        return jsonify({'message': 'Authentication required'}), 401

    requester = Admin.query.get(requester_id)
    if not requester or requester.role != 'super_admin':
        return jsonify({'message': 'Unauthorized - super_admin required'}), 403

    # Validate request payload
    required = ['full_name', 'email', 'mobile', 'password', 'language']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f"Missing fields: {', '.join(missing)}"}), 400

    email = data['email'].strip().lower()
    mobile = data['mobile'].strip()

    # Prevent duplicates
    if Admin.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 400
    if Admin.query.filter_by(mobile=mobile).first():
        return jsonify({'error': 'Mobile already exists'}), 400

    # Create sub-admin
    new_admin = Admin(
        full_name=data['full_name'].strip(),
        email=email,
        mobile=mobile,
        role='sub_admin',
        language=data.get('language'),
        status='Active'     # explicitly set Active
    )
    new_admin.set_password(data['password'])
    db.session.add(new_admin)
    db.session.commit()

    return jsonify({
        'message': 'Sub-admin created successfully',
        'admin_id': new_admin.id,
        'email': new_admin.email,
        'role': new_admin.role
    }), 201

# View a single sub-admin by ID (only super_admin)
@app.route('/api/admin/subadmin/<int:subadmin_id>', methods=['GET'])
def get_subadmin(subadmin_id):
    # Auth check
    requester_id = session.get('admin_id')
    header_admin = request.headers.get('X-Admin-Id')
    if header_admin and header_admin.isdigit():
        requester_id = int(header_admin)

    if not requester_id:
        return jsonify({'message': 'Authentication required'}), 401

    requester = Admin.query.get(requester_id)
    if not requester or requester.role != 'super_admin':
        return jsonify({'message': 'Unauthorized - super_admin required'}), 403

    # Fetch the sub-admin by id and check role
    subadmin = Admin.query.get(subadmin_id)
    if not subadmin or subadmin.role != 'sub_admin':
        return jsonify({'message': 'Sub-admin not found'}), 404

    # Return sub-admin info (omit password hash)
    return jsonify({
        'id': subadmin.id,
        'full_name': subadmin.full_name,
        'email': subadmin.email,
        'mobile': subadmin.mobile,
        'role': subadmin.role,
        'language': subadmin.language
    }), 200


# Update a single sub-admin by ID (only super_admin)
@app.route('/api/admin/subadmin/<int:subadmin_id>', methods=['PUT'])
def update_subadmin(subadmin_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing JSON body'}), 400

    # Auth check
    requester_id = session.get('admin_id')
    header_admin = request.headers.get('X-Admin-Id')
    if header_admin and header_admin.isdigit():
        requester_id = int(header_admin)

    if not requester_id:
        return jsonify({'message': 'Authentication required'}), 401

    requester = Admin.query.get(requester_id)
    if not requester or requester.role != 'super_admin':
        return jsonify({'message': 'Unauthorized - super_admin required'}), 403

    subadmin = Admin.query.get(subadmin_id)
    if not subadmin or subadmin.role != 'sub_admin':
        return jsonify({'message': 'Sub-admin not found'}), 404

    # Update allowed fields - do not allow role change here
    if 'full_name' in data:
        subadmin.full_name = data['full_name'].strip()
    if 'email' in data:
        new_email = data['email'].strip().lower()
        # Check if new email exists on other admins
        if Admin.query.filter(Admin.email == new_email, Admin.id != subadmin.id).first():
            return jsonify({'error': 'Email already exists'}), 400
        subadmin.email = new_email
    if 'mobile' in data:
        new_mobile = data['mobile'].strip()
        # Check if new mobile exists on other admins
        if Admin.query.filter(Admin.mobile == new_mobile, Admin.id != subadmin.id).first():
            return jsonify({'error': 'Mobile already exists'}), 400
        subadmin.mobile = new_mobile
    if 'language' in data:
        subadmin.language = data['language']

    # Password update (optional)
    if 'password' in data and data['password'].strip():
        subadmin.set_password(data['password'].strip())

    db.session.commit()

    return jsonify({
        'message': 'Sub-admin updated successfully',
        'admin_id': subadmin.id,
        'email': subadmin.email,
        'role': subadmin.role
    }), 200

# Get all sub-admins (super_admin only)
@app.route('/api/admin/subadmins', methods=['GET'])
def get_all_subadmins():
    # Auth: allow session admin_id or X-Admin-Id header
    admin_id = session.get('admin_id')
    header_admin = request.headers.get('X-Admin-Id')
    if header_admin and header_admin.isdigit():
        admin_id = int(header_admin)

    if not admin_id:
        return jsonify({'message': 'Authentication required'}), 401

    requester = Admin.query.get(admin_id)
    if not requester:
        return jsonify({'message': 'Requester admin not found'}), 404

    # Only super_admin allowed to list sub-admins — change if you want different rules
    if requester.role != 'super_admin':
        return jsonify({'message': 'Unauthorized - super_admin required'}), 403

    subadmins = Admin.query.filter_by(role='sub_admin').order_by(Admin.created_on.desc()).all()

    result = []
    for i, a in enumerate(subadmins, start=1):
        result.append({
            'serial': (a.id - 1),
            'id': a.id,
            'full_name': a.full_name,
            'email': a.email,
            'mobile': a.mobile,
            'language': a.language,
            'status': a.status,
            'role': a.role,
            'created_on': a.created_on.isoformat() if a.created_on else None,
            'updated_on': a.updated_on.isoformat() if a.updated_on else None
        })

    return jsonify({'data': result}), 200

# Toggle admin status (activate/deactivate)
@app.route('/api/admin/<int:admin_id>/status', methods=['PATCH'])
def update_admin_status(admin_id):
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'error': 'Missing "status" field'}), 400

    # Auth: only super_admin should be allowed to change status (or the admin itself)
    requester_id = session.get('admin_id')
    header_admin = request.headers.get('X-Admin-Id')
    if header_admin and header_admin.isdigit():
        requester_id = int(header_admin)

    if not requester_id:
        return jsonify({'message': 'Authentication required'}), 401

    requester = Admin.query.get(requester_id)
    if not requester or requester.role != 'super_admin':
        return jsonify({'message': 'Unauthorized - super_admin required'}), 403

    admin = Admin.query.get(admin_id)
    if not admin:
        return jsonify({'message': 'Admin not found'}), 404

    new_status = data['status'].strip()
    if new_status not in ('Active', 'Inactive'):
        return jsonify({'error': 'Invalid status. Use "Active" or "Inactive".'}), 400

    admin.status = new_status
    db.session.commit()
    return jsonify({'message': f'Admin status updated to {new_status}'}), 200


# Create a new story
@app.route('/api/story', methods=['POST'])
def create_story():
    user_id = get_current_user()
    if not user_id:
        return jsonify({'message': 'Authentication required'}), 401

    # Common variables
    pdf_url = ''
    story_text = ''
    tags = ''

    # If request is JSON (from API client)
    if request.is_json:
        data = request.get_json()
        story_input_method = data.get('storyInput', 'text')
        tags = ','.join(data.get('tags', [])) if isinstance(data.get('tags'), list) else data.get('tags', '')

        if story_input_method == 'pdf':
            pdf_url = data.get('pdf_url', '')
        else:
            story_text = data.get('story', '')

    # If request is from HTML Form
    else:
        data = request.form
        story_input_method = data.get('storyInput', 'text')
        tags = data.get('tags', '')

        if story_input_method == 'pdf' and 'pdf' in request.files:
            pdf_file = request.files['pdf']
            if pdf_file.filename != '':
                filename = secure_filename(pdf_file.filename)
                pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                pdf_file.save(pdf_path)
                pdf_url = f'/uploads/{filename}'
        else:
            story_text = data.get('story', '')

    # Price and status
    price = float(data.get('price', 0.00))
    status = data.get('status', 'draft')  # default to draft

    # Create Story object
    story = Story(
        WRITTEN_BY=user_id,
        NAME=data.get('name'),
        LANGUAGE=data.get('language'),
        FONT=data.get('font'),
        PDF_URL=pdf_url,
        STORY=story_text,
        STATUS=status,
        PRICE=price,
        TAGS=tags
    )
    db.session.add(story)
    db.session.commit()

    return jsonify({'message': 'Story created successfully'})



# Get all published stories (publicly accessible)
@app.route('/api/public/stories', methods=['GET'])
def get_all_published_stories():
    # Fetch only published stories, ordered by latest update
    stories = Story.query.filter_by(STATUS='published').order_by(Story.UPDATED_ON.desc()).all()

    response = []
    for story in stories:
        response.append({
            'id': story.STORY_ID,
            'authorId': story.WRITTEN_BY,
            'name': story.NAME,
            'language': story.LANGUAGE,
            'font': story.FONT,
            'pdf_url': story.PDF_URL,
            'story': story.STORY,
            'status': story.STATUS,
            'price': float(story.PRICE) if story.PRICE else 0.00,
            'tags': story.TAGS,
            'created_on': story.CREATED_ON.strftime('%Y-%m-%d %H:%M:%S') if story.CREATED_ON else None,
            'updated_on': story.UPDATED_ON.strftime('%Y-%m-%d %H:%M:%S') if story.UPDATED_ON else None
        })

    return jsonify(response)


# Get all published poems (publicly accessible)
@app.route('/api/public/poems', methods=['GET'])
def get_all_published_poems():
    # Fetch only published poems, ordered by latest update
    poems = Poem.query.filter_by(STATUS='published').order_by(Poem.UPDATED_ON.desc()).all()

    response = []
    for poem in poems:
        response.append({
            'id': poem.STORY_ID,
            'authorId': poem.WRITTEN_BY,
            'name': poem.NAME,
            'tags': poem.TAGS,
            'language': poem.LANGUAGE,
            'font': poem.FONT,
            'status': poem.STATUS,
            'updated_on': poem.UPDATED_ON.strftime('%Y-%m-%d %H:%M:%S') if poem.UPDATED_ON else None
        })
    return jsonify(response)


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


# Get all stories (for the logged-in writer)
@app.route('/api/stories', methods=['GET'])
def get_all_stories():
    user_id = get_current_user()
    if not user_id:
        return jsonify({'message': 'Authentication required'}), 401

    # Get only stories written by this user, ordered by latest update
    stories = Story.query.filter_by(WRITTEN_BY=user_id).order_by(Story.UPDATED_ON.desc()).all()

    response = []
    for idx, story in enumerate(stories, start=1):
        response.append({
            'serial': idx,  # For table display
            'id': story.STORY_ID,
            'authorId': story.WRITTEN_BY,
            'name': story.NAME,
            'language': story.LANGUAGE,
            'font': story.FONT,
            'pdf_url': story.PDF_URL,
            'story': story.STORY,
            'status': story.STATUS,
            'price': float(story.PRICE) if story.PRICE else 0.00,
            'tags': story.TAGS,
            'created_on': story.CREATED_ON.strftime('%Y-%m-%d %H:%M:%S') if story.CREATED_ON else None,
            'updated_on': story.UPDATED_ON.strftime('%Y-%m-%d %H:%M:%S') if story.UPDATED_ON else None
        })

    return jsonify(response)



# Create a new poem
@app.route('/api/poem', methods=['POST'])
def create_poem():
    user_id = get_current_user()
    if not user_id:
        return jsonify({'message': 'Authentication required'}), 401

    pdf_url = ''
    poem_text = ''
    tags = ''

    # Handle JSON request
    if request.is_json:
        data = request.get_json()
        poem_input_method = data.get('poemInput', 'text')
        tags = ','.join(data.get('tags', [])) if isinstance(data.get('tags'), list) else data.get('tags', '')

        if poem_input_method == 'pdf':
            pdf_url = data.get('pdf_url', '')
        else:
            poem_text = data.get('story', '')

        price = float(data.get('price', 0.00))
        status = data.get('status', 'draft')
        name = data.get('name')
        language = data.get('language')
        font = data.get('font')

    # Handle HTML Form request
    else:
        data = request.form
        poem_input_method = data.get('poemInput', 'text')
        tags = data.get('tags', '')

        if poem_input_method == 'pdf' and 'pdf' in request.files:
            pdf_file = request.files['pdf']
            if pdf_file.filename != '':
                filename = secure_filename(pdf_file.filename)
                pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                pdf_file.save(pdf_path)
                pdf_url = f'/uploads/{filename}'
        else:
            poem_text = data.get('story', '')

        price = float(data.get('price', 0.00))
        status = data.get('status', 'draft')
        name = data.get('name')
        language = data.get('language')
        font = data.get('font')

    # Create Poem object
    poem = Poem(
        WRITTEN_BY=user_id,
        NAME=name,
        LANGUAGE=language,
        FONT=font,
        PDF_URL=pdf_url,
        STORY=poem_text,
        STATUS=status,
        PRICE=price,
        TAGS=tags
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


# Get all poems (for the logged-in writer)
@app.route('/api/poems', methods=['GET'])
def get_all_poems():
    user_id = get_current_user()
    if not user_id:
        return jsonify({'message': 'Authentication required'}), 401

    # Fetch only this user's poems, latest first
    poems = Poem.query.filter_by(WRITTEN_BY=user_id).order_by(Poem.UPDATED_ON.desc()).all()

    response = []
    for idx, poem in enumerate(poems, start=1):
        response.append({
            'serial': idx,  # Table "Serial" column
            'id': poem.STORY_ID,
            'authorId': poem.WRITTEN_BY,
            'name': poem.NAME,
            'tags': poem.TAGS,
            'language': poem.LANGUAGE,
            'font': poem.FONT,
            'status': poem.STATUS,
            'updated_on': poem.UPDATED_ON.strftime('%Y-%m-%d %H:%M:%S') if poem.UPDATED_ON else None
        })

    return jsonify(response)


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


# 📌 1. Get all Help & Support requests (for DataTable)
@app.route('/api/help-support', methods=['GET'])
def get_all_help_support():
    requests = HelpSupport.query.all()
    table_data = []
    for r in requests:
        table_data.append([
            r.id,
            r.support_type or "",
            r.user.full_name if r.user else "",
            r.user.role if r.user else "",
            r.created_on.strftime("%Y-%m-%d") if r.created_on else "",
            r.status or "",
            r.updated_on.strftime("%Y-%m-%d") if r.updated_on else "",
        ])
    return jsonify({"data": table_data})


# 📌 2. View a single Help & Support request
@app.route('/api/help-support/<int:request_id>', methods=['GET'])
def view_help_support(request_id):
    r = HelpSupport.query.get_or_404(request_id)
    return jsonify({
        "id": r.id,
        "support_type": r.support_type,
        "user_name": r.user.full_name if r.user else None,
        "user_type": r.user.role if r.user else None,
        "created_on": r.created_on.strftime("%Y-%m-%d"),
        "status": r.status,
        "updated_on": r.updated_on.strftime("%Y-%m-%d"),
        "admin_note": r.admin_note
    })


# 📌 3. Resolve a Help & Support request
@app.route('/api/help-support/<int:request_id>/resolve', methods=['POST'])
def resolve_help_support(request_id):
    r = HelpSupport.query.get_or_404(request_id)
    note = request.json.get("note", "").strip()
    if not note:
        return jsonify({"error": "Note is required"}), 400

    r.status = "Resolved"
    r.admin_note = note
    r.updated_on = datetime.utcnow()
    db.session.commit()

    return jsonify({"message": "Support request resolved successfully"})


# 📌 4. Reject a Help & Support request
@app.route('/api/help-support/<int:request_id>/reject', methods=['POST'])
def reject_help_support(request_id):
    r = HelpSupport.query.get_or_404(request_id)
    note = request.json.get("note", "").strip()
    if not note:
        return jsonify({"error": "Note is required"}), 400

    r.status = "Rejected"
    r.admin_note = note
    r.updated_on = datetime.utcnow()
    db.session.commit()

    return jsonify({"message": "Support request rejected successfully"})

@app.route('/api/help-support', methods=['POST'])
def create_help_support():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON data"}), 400

    support_type = data.get("support_type", "").strip()
    user_id = data.get("user_id")
    admin_note = data.get("admin_note", "").strip()  # <-- new optional field

    if not support_type:
        return jsonify({"error": "Support type is required"}), 400
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Invalid user ID"}), 404

    new_request = HelpSupport(
        support_type=support_type,
        user_id=user_id,
        status="Pending",
        admin_note=admin_note if admin_note else None,
        created_on=datetime.utcnow(),
        updated_on=datetime.utcnow()
    )
    db.session.add(new_request)
    db.session.commit()

    return jsonify({"message": "Help & Support request created successfully"}), 201

UPLOAD_AUDIO_FOLDER = "static/audio"
ALLOWED_AUDIO_EXTENSIONS = {"mp3", "wav", "m4a"}

app.config["UPLOAD_AUDIO_FOLDER"] = UPLOAD_AUDIO_FOLDER

def allowed_audio_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_AUDIO_EXTENSIONS


@app.route('/api/admin/audio', methods=['POST'])
def create_audio_story():
    # ✅ Get admin_id directly from request headers
    admin_id = request.headers.get("X-Admin-Id")
    if not admin_id:
        return jsonify({"message": "Authentication required"}), 401

    try:
        admin_id = int(admin_id)
    except ValueError:
        return jsonify({"message": "Invalid Admin ID"}), 400

    data = request.form.to_dict()
    audio_url = ""

    # Handle audio file upload
    audio_file = request.files.get("audio")
    if audio_file and allowed_audio_file(audio_file.filename):
        filename = secure_filename(audio_file.filename)
        os.makedirs(app.config["UPLOAD_AUDIO_FOLDER"], exist_ok=True)
        audio_path = os.path.join(app.config["UPLOAD_AUDIO_FOLDER"], filename)
        audio_file.save(audio_path)

        # Serve from static/audio
        audio_url = f"/static/audio/{filename}"

    # Process Tagify tags
    if "tags" in data:
        try:
            tag_data = json.loads(data["tags"])
            if isinstance(tag_data, list):
                data["tags"] = ",".join([t["value"] for t in tag_data])
        except Exception:
            pass

    # Identify linked story/poem if applicable
    link_type = data.get("statusDropdown")  # "storyAvailable", "poemAvailable", "storyPoemNA"
    linked_story_id = data.get("storyDropdown") if link_type == "storyAvailable" else None
    linked_poem_id = data.get("poemDropdown") if link_type == "poemAvailable" else None

    # ✅ Default every new audio to "draft"
    status = data.get("status", "draft")

    # Save to DB
    audio_story = AudioStory(
        CREATED_BY=admin_id,
        NAME=data.get("name") or data.get("exampleInputName1"),
        LANGUAGE=data.get("language") or data.get("exampleSelectLanguage"),
        LINK_TYPE=link_type,
        LINKED_STORY_ID=linked_story_id,
        LINKED_POEM_ID=linked_poem_id,
        AUDIO_URL=audio_url,
        TAGS=data.get("tags", ""),
        STATUS=status
    )

    db.session.add(audio_story)
    db.session.commit()

    return jsonify({"message": "Audio story created successfully"})


@app.route('/api/admin/audio/<int:audio_id>/approve', methods=['PUT'])
def approve_audio_story(audio_id):
    admin_id = request.headers.get("X-Admin-Id")  # ✅ get admin ID from headers
    if not admin_id:
        return jsonify({"message": "Authentication required"}), 401
    try:
        admin_id = int(admin_id)
    except ValueError:
        return jsonify({"message": "Invalid Admin ID"}), 400

    audio_story = AudioStory.query.get(audio_id)
    if not audio_story:
        return jsonify({"message": "Audio story not found"}), 404

    audio_story.STATUS = "published"
    db.session.commit()

    return jsonify({"message": "Audio story approved and published successfully"})


@app.route('/api/admin/audio/<int:audio_id>/reject', methods=['PUT'])
def reject_audio_story(audio_id):
    admin_id = request.headers.get("X-Admin-Id")  # ✅ get admin ID from headers
    if not admin_id:
        return jsonify({"message": "Authentication required"}), 401
    try:
        admin_id = int(admin_id)
    except ValueError:
        return jsonify({"message": "Invalid Admin ID"}), 400

    audio_story = AudioStory.query.get(audio_id)
    if not audio_story:
        return jsonify({"message": "Audio story not found"}), 404

    audio_story.STATUS = "rejected"
    db.session.commit()

    return jsonify({"message": "Audio story has been rejected"})


@app.route('/api/admin/drafted_audio', methods=['GET'])
def get_admin_drafted_audio():
    # Query only drafted audio stories sorted by creation date descending
    audios = AudioStory.query.filter_by(STATUS='draft').order_by(AudioStory.CREATED_ON.desc()).all()
    audio_list = []
    serial = 1

    for audio in audios:
        # Convert tags comma string to a list
        tags_list = []
        if audio.TAGS:
            tags_list = [t.strip() for t in audio.TAGS.split(',') if t.strip()]

        # Resolve linked story or poem name if needed (assuming relationships or querying)
        linked_name = ""
        if audio.LINK_TYPE == "storyAvailable" and audio.LINKED_STORY_ID:
            story = Story.query.get(audio.LINKED_STORY_ID)
            linked_name = story.NAME if story else ""
        elif audio.LINK_TYPE == "poemAvailable" and audio.LINKED_POEM_ID:
            # Assuming a Poem model exists similarly to Story
            poem = Poem.query.get(audio.LINKED_POEM_ID)
            linked_name = poem.NAME if poem else ""

        created_on_display = audio.CREATED_ON.strftime('%d-%m-%Y %H:%M') if audio.CREATED_ON else ""
        updated_on_display = audio.UPDATED_ON.strftime('%d-%m-%Y %H:%M') if audio.UPDATED_ON else ""

        audio_list.append({
            'serial': serial,
            'id': audio.AUDIO_ID,
            'name': audio.NAME,
            'tags': tags_list,
            'language': audio.LANGUAGE,
            'linked_name': linked_name,
            'created_on': created_on_display,
            'updated_on': updated_on_display,
            # 'actions' field can be handled client-side based on ID
        })

        serial += 1

    return jsonify(audio_list)

@app.route('/api/admin/all_audio', methods=['GET'])
def get_admin_all_audio():
    audios = AudioStory.query.order_by(AudioStory.UPDATED_ON.desc()).all()
    audio_list = []
    serial = 1

    for audio in audios:
        # Convert tags string to list
        tags_list = []
        if audio.TAGS:
            tags_list = [t.strip() for t in audio.TAGS.split(',') if t.strip()]

        # Resolve linked story or poem name if applicable
        linked_name = ""
        if audio.LINK_TYPE == "storyAvailable" and audio.LINKED_STORY_ID:
            story = Story.query.get(audio.LINKED_STORY_ID)
            linked_name = story.NAME if story else ""
        elif audio.LINK_TYPE == "poemAvailable" and audio.LINKED_POEM_ID:
            poem = Poem.query.get(audio.LINKED_POEM_ID)
            linked_name = poem.NAME if poem else ""

        updated_on_display = audio.UPDATED_ON.strftime('%d-%m-%Y %H:%M') if audio.UPDATED_ON else ""

        audio_list.append({
            'serial': serial,
            'id': audio.AUDIO_ID,
            'name': audio.NAME,
            'tags': tags_list,
            'language': audio.LANGUAGE,
            'linked_name': linked_name,
            'status': audio.STATUS,
            'updated_on': updated_on_display
            # 'audio_url': audio.AUDIO_URL
            # 'actions' handled on frontend with 'id'
        })
        serial += 1

    return jsonify(audio_list)

@app.route('/api/public/audio', methods=['GET'])
def get_all_published_audio():
    audios = AudioStory.query.order_by(AudioStory.UPDATED_ON.desc()).all()
    audio_list = []
    serial = 1

    for audio in audios:
        # Convert tags string to list
        tags_list = []
        if audio.TAGS:
            tags_list = [t.strip() for t in audio.TAGS.split(',') if t.strip()]

        # Resolve linked story or poem name if applicable
        linked_name = ""
        if audio.LINK_TYPE == "storyAvailable" and audio.LINKED_STORY_ID:
            story = Story.query.get(audio.LINKED_STORY_ID)
            linked_name = story.NAME if story else ""
        elif audio.LINK_TYPE == "poemAvailable" and audio.LINKED_POEM_ID:
            poem = Poem.query.get(audio.LINKED_POEM_ID)
            linked_name = poem.NAME if poem else ""

        updated_on_display = audio.UPDATED_ON.strftime('%d-%m-%Y %H:%M') if audio.UPDATED_ON else ""

        audio_list.append({
            'serial': serial,
            'id': audio.AUDIO_ID,
            'name': audio.NAME,
            'tags': tags_list,
            'language': audio.LANGUAGE,
            'linked_name': linked_name,
            'status': audio.STATUS,
            'updated_on': updated_on_display,
            'audio_url': audio.AUDIO_URL
            # 'actions' handled on frontend with 'id'
        })
        serial += 1

    return jsonify(audio_list)

@app.route("/api/authors", methods=["GET"])
def get_authors():
    try:
        search = request.args.get("search", "").strip()
        filter_by = request.args.get("filter", "all")

        query = User.query.filter_by(role="Writer", is_active=True, is_approved=True)

        #  Search filter
        if search:
            query = query.filter(
                (User.full_name.ilike(f"%{search}%")) |
                (User.email.ilike(f"%{search}%"))  # or if you store genre/keywords in TAGS, join Poem/Story
            )

        #  Filter options
        if filter_by == "recent":
            query = query.order_by(User.created_on.desc())
        elif filter_by == "popular":
            # Example: popularity = number of stories + poems
            query = query.outerjoin(Story, Story.WRITTEN_BY == User.id) \
                         .outerjoin(Poem, Poem.WRITTEN_BY == User.id) \
                         .group_by(User.id) \
                         .order_by(desc(func.count(Story.STORY_ID) + func.count(Poem.STORY_ID)))
        elif filter_by in ["english", "bengali", "hindi"]:
            # Assuming language stored in stories/poems
            query = query.join(Story, Story.WRITTEN_BY == User.id) \
                         .filter(Story.LANGUAGE.ilike(filter_by))
        elif filter_by == "story":
            query = query.join(Story, Story.WRITTEN_BY == User.id)
        elif filter_by == "poem":
            query = query.join(Poem, Poem.WRITTEN_BY == User.id)

        authors = query.all()

        result = []
        for author in authors:
            story_count = Story.query.filter_by(WRITTEN_BY=author.id).count()
            poem_count = Poem.query.filter_by(WRITTEN_BY=author.id).count()
            audio_count = AudioStory.query.filter_by(CREATED_BY=author.id).count()

            result.append({
                "id": author.id,
                "full_name": author.full_name,
                "email": author.email,
                "stories": story_count,
                "poems": poem_count,
                "audios": audio_count,
                "created_on": author.created_on.strftime("%Y-%m-%d"),
                # "profile_image": author.profile_image if author.profile_image else "default.jpg",  # Add this line
            })

        return jsonify({"authors": result, "total": len(result)}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/author-stats", methods=["GET"])
def author_stats():
    try:
        total_authors = User.query.filter_by(role="Writer", is_active=True, is_approved=True).count()
        total_stories = Story.query.count()
        total_poems = Poem.query.count()
        total_audio = AudioStory.query.count()

        return jsonify({
            "total_authors": total_authors,
            "total_stories": total_stories,
            "total_poems": total_poems,
            "total_audio": total_audio
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

#  API to fetch Writer details by id

@app.route('/api/writer/<int:user_id>', methods=['GET'])
def get_writer(user_id):
    try:
        # Fetch user by id & role = Writer
        writer = User.query.filter_by(id=user_id, role='Writer').first()

        if not writer:
            return jsonify({"error": "Writer not found"}), 404

        # Return writer details (exclude password)
        return jsonify({
            "id": writer.id,
            "full_name": writer.full_name,
            "email": writer.email,
            "mobile": writer.mobile,
            "role": writer.role,
            "is_active": writer.is_active,
            "is_approved": writer.is_approved,
            "created_on": writer.created_on.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_on": writer.updated_on.strftime("%Y-%m-%d %H:%M:%S")
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)