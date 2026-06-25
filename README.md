# ConnectSphere — Social Media Platform (Django)

ConnectSphere is a modern, feature-rich social media platform built for creators and developers. It is powered by **Django** on the backend and features a responsive frontend styled in the **Sahara Warm Minimalism** aesthetic using **Tailwind CSS**.

👉 **For the complete architecture details, API specs, and user manuals, see the main [ConnectSphere Documentation (docs/DOCUMENTATION.md)](docs/DOCUMENTATION.md)**

---

## 🛠️ Technology Stack & Libraries

### 1. Backend Core
* **Python 3.10+**: Core programming language.
* **Django (6.0+)**: Batteries-included web framework following the MTV (Model-Template-View) pattern.
* **Daphne**: ASGI server to support asynchronous WebSockets in production.
* **Django Channels (v4)**: Adds WebSocket support to handle asynchronous connections (real-time chat, typing states, and push alerts).
* **Django REST Framework (DRF)**: Powers the platform's RESTful endpoints.

### 2. Databases & Cache
* **SQLite**: Local developer filesystem database.
* **PostgreSQL / dj_database_url**: Configured for rapid production databases scaling.
* **Redis / channels_redis**: Used as the WebSocket channel layers backplane in multi-server environments.

### 3. Security & Authentication
* **Django-OTP / django-otp-totp**: Enforces two-factor authentication (2FA) via verification tokens.
* **Django Allauth**: Manages authentication sessions and handles OAuth logins (Google / GitHub).

### 4. Frontend & Styling
* **Tailwind CSS (v3/v4)**: Modern CSS-in-HTML utility frameworks to coordinate layouts.
* **Google Fonts**: *EB Garamond* (classy editorial headers) and *Manrope* (clean UI typography labels).
* **Material Symbols**: Smooth vector action icons.

---

## 🎨 Visual Showcase (Screenshots)

Below are actual layout screenshots verifying the Sahara minimalist design:

### 1. Discover / Explore Page
A beautiful 12-column bento board highlighting trending stories, daily prompts, trending tags, rising creators, and curated collections.
![Discover Page](docs/screenshots/discover_page.png)

### 2. Settings Dashboard — Account Tab
A tabbed, no-reload configuration suite for custom public profiles:
![Settings Profile Tab](docs/screenshots/settings_profile.png)

### 3. Settings Dashboard — Switcher Tab
Switch accounts instantly inside development environments:
![Settings Security Tab](docs/screenshots/settings_security.png)

### 4. Settings Dashboard — Saved Collections
A grid displaying bookmarked posts:
![Settings Saved Collections Tab](docs/screenshots/settings_saved.png)

### 5. Bookmarks Page
Clean list of bookmarked posts with asynchronous removal using the native Fetch API:
![Bookmarks Page](docs/screenshots/bookmarks_page.png)

---

## 🚀 Quick Start (Local Run)

1. **Activate the virtual environment**:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
2. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```
3. **Run database migrations**:
   ```powershell
   python manage.py migrate
   ```
4. **Start the development server**:
   ```powershell
   python manage.py runserver
   ```
5. **Open your browser** and navigate to `http://127.0.0.1:8000/`.

---

## 🐳 Container Setup (Docker)

Launch the entire ecosystem (Django web server container + Redis service broker container):
```bash
docker-compose up --build
```
This serves the application on `http://localhost:8000/`.

---

## 🧪 Running the Tests

Execute the testing suite containing all unit and integration cases:
```bash
python manage.py test
```
