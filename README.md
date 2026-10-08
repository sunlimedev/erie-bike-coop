# erie-bike-coop
Automating some work and data collection so people can do what they're best at.

### .env
```commandline
FLASK_SECRET_KEY=
SMTP_KEY=
SENDER=
RECIPIENT=
```

### gunicorn.service
```commandline
[Unit]
Description=Gunicorn WSGI Runner
After=network.target

[Service]
User=user
WorkingDirectory=/home/user
ExecStart=/home/user/venv/bin/gunicorn --workers 5 --bind 0.0.0.0:8000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```