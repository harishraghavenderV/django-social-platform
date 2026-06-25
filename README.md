# ConnectSphere — Social Media Platform (Django)

A fully-featured social media platform built with Django, Django Channels (WebSockets), Django REST Framework, SQLite, and a responsive frontend styled in the **Sahara Warm Minimalism** aesthetic with Tailwind CSS.

For comprehensive setup details, code structure, deployment guides, user manuals, technical algorithms, and visual screenshots, refer to the main documentation:

👉 **[ConnectSphere Documentation (docs/DOCUMENTATION.md)](docs/DOCUMENTATION.md)**

---

## Quick Start (Local Run)

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
5. **Navigate** to `http://127.0.0.1:8000/` in your browser.

## Container Setup (Docker)

To run the entire platform (Web Server + Redis backend Channel Layer) in Docker:
```bash
docker-compose up --build
```
This launches ConnectSphere on `http://localhost:8000/`.

## Running the Tests

To execute the test suite containing all 68 unit/integration cases:
```bash
python manage.py test
```
