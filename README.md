
# GoddoPoddo Backend

This is the backend for the GoddoPoddo application, built with Flask.

## Setup

1. Create a virtual environment (recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:

   ### Development mode
   ```
   python app.py
   ```

   ### Production mode (using WSGI with Gunicorn)
   ```
   gunicorn --bind 0.0.0.0:5000 wsgi:app
   ```

## Project Structure
```
goddo_poddo_backend
├─ 📁__pycache__
│  ├─ 📄app.cpython-312.pyc
│  ├─ 📄config.cpython-312.pyc
│  └─ 📄models.cpython-312.pyc
├─ 📄app.py
├─ 📄config.py
├─ 📄forms.py
├─ 📄models.py
├─ 📄requirements.txt
└─ 📄wsgi.py
```

## API Endpoints

- `/register` - Register a new user
- `/login` - User login
- `/logout` - User logout
- `/api/story` - Create a new story
- `/api/story/<id>` - Get a specific story
- `/api/stories` - Get all stories
- `/api/poem` - Create a new poem
- `/api/poem/<id>` - Get a specific poem
- `/api/poems` - Get all poems
- `/forgot-password` - Password reset functionality