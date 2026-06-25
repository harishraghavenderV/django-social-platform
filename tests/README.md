# ConnectSphere Tests Directory

To align with standard Django layout conventions, ConnectSphere's test suites are placed inside each individual application folder (e.g., `users/tests.py`, `posts/tests.py`, `api/tests.py`, etc.). This keeps unit tests close to the models, views, and controllers they verify.

## Running Tests

To run the entire test suite across all apps, run:
```powershell
python manage.py test
```

## App Test Locations
- **Users**: `users/tests.py`
- **Posts**: `posts/tests.py`
- **Friends**: `friends/tests.py`
- **Notifications**: `notifications/tests.py`
- **REST API**: `api/tests.py`
- **Messaging**: `messaging/tests.py`
- **Stories**: `stories/tests.py`
- **Groups**: `groups/tests.py`
- **Reels**: `reels/tests.py`
- **Events**: `events/tests.py`
- **Moderation**: `moderation/tests.py`
