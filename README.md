# ConnectSphere — Social Media Platform (Django)

A fully-featured social media platform built with Django, Django REST Framework, SQLite, and Bootstrap 5.

## Features

- **User Authentication**: Sign up, log in, log out.
- **User Profiles**: Manage bio, location, website, profile pictures, and cover photos.
- **Feed**: Read posts from followed users and yourself, sorted chronologically.
- **Interactions**: Create text posts with optional media uploads, comment, and like posts dynamically.
- **Social Connections**: Send, accept, or decline friend requests. Follow/unfollow users.
- **Notifications**: Get real-time notifications for likes, comments, friend requests, accepts, and follows.
- **REST API**: Integrated DRF endpoints for posts, user profiles, and notifications.

## Installation & Setup

1. Activate the virtual environment:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Run database migrations:
   ```powershell
   python manage.py migrate
   ```
4. Start development server:
   ```powershell
   python manage.py runserver
   ```
5. Open your browser and go to http://127.0.0.1:8000/
