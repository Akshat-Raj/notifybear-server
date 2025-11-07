# Name Server of Notifybear

## Setup Instruction
1. Clone Repo
```bash
git clone https://github.com/swarnpsingh/notifybear-server.git
```

2. Goto directory
```bash
cd notifybear-server
```

3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. Set up `.env` file

```bash
DJANGO_KEY=your_secret_key_here
```

5. Apply Migrations
```bash
python manage.py migrate
```

6. Create Super User (optional, but helps monitoring manually)
```bash
python manage.py createsuperuser
```

7. Run
```bash
python manage.py runserver
```

## Endpoints

1. Login
```bash
http://127.0.0.1:8000/accounts/login
```
2. Signup
```bash
http://127.0.0.1:8000/accounts/signup
```
3. Me (Gets logged in user's data)
```bash
http://127.0.0.1:8000/accounts/me
```
4. Get Notifications
```bash
http://127.0.0.1:8000/notifications/get
```
5. Post Notifications
```bash
http://127.0.0.1:8000/notifications/upload
```
6. Admin page
```bash
http://127.0.0.1:8000/admin/
``` 