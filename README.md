# erie-bike-coop
Automating some work and data collection so people can do what they're best at.

### Setup
- Installed and started`Tailscale`
- Installed `python3-venv`
- Create `venv`
- Updated `pip` to 26.2.2
- Installed `flask`, `flask-login`, `flask-wtf`, `python-dotenv`, `gunicorn`
- Config `nginx` + `gunicorn`

### .env
```commandline
FLASK_SECRET_KEY=
SMTP_KEY=
SENDER=
RECIPIENT=
ADMIN_PASSWORD=
```

### Configure Web Server -- `nginx` + `gunicorn`
Create the `gunicorn` UNIX socket
```
sudo nano /etc/systemd/system/gunicorn.socket
```
```
[Unit]
Description=gunicorn Socket

[Socket]
ListenStream=/run/gunicorn.sock
SocketUser=user
SocketGroup=www-data
SocketMode=0660

[Install]
WantedBy=sockets.target
```
Create the `systemd` service
```
sudo nano /etc/systemd/system/gunicorn.service
```
```
[Unit]
Description=Gunicorn WSGI Runner
Requires=gunicorn.socket
After=network.target

[Service]
Type=notify
NotifyAccess=main
User=user
Group=user
WorkingDirectory=/home/user
Environment="PATH=/home/user/venv/bin"
ExecStart=/home/user/venv/bin/gunicorn --workers 2 app:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```
Start the service now and on boot
```
sudo systemctl daemon-reload
sudo systemctl enable --now gunicorn.socket
sudo systemctl enable --now gunicorn.service
```
Verify socket setup
```
ls -la /run/gunicorn.sock

# Expected:
srw-rw---- 1 user www-data 0 ... /run/gunicorn.sock
```
```
sudo -u www-data curl --unix-socket /run/gunicorn.sock http://localhost/

# Expected: 
<!doctype html>
<html lang=en>
<title>Redirecting...</title>
<h1>Redirecting...</h1>
...
```
Create self-signed certificate
```
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -x509 -nodes -newkey rsa:4096 \
  -keyout /etc/nginx/ssl/key.pem \
  -out /etc/nginx/ssl/cert.pem \
  -days 36500 \
  -subj "/CN=localhost"
```
Secure certificate and key
```
sudo chmod 600 /etc/nginx/ssl/key.pem
sudo chown root:root /etc/nginx/ssl/*.pem
```
Create `nginx` configuration for `flask`
```
sudo nano /etc/nginx/sites-available/flask-app
```
```
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl default_server;
    listen [::]:443 ssl default_server;
    server_name _;

    ssl_certificate     /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    add_header X-Frame-Options "DENY" always;
    add_header Content-Security-Policy "frame-ancestors 'none';" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;
    add_header Referrer-Policy "same-origin" always;
    add_header Feature-Policy "geolocation 'self'; vibrate 'none'" always;

    client_max_body_size 4G;
    keepalive_timeout 5;

    location / {
        proxy_pass http://unix:/run/gunicorn.sock;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```
Enable the custom configuration and disable the default one
```
sudo ln -s /etc/nginx/sites-available/flask-app /etc/nginx/sites-enabled/flask-app
sudo rm /etc/nginx/sites-enabled/default
```
Verify the custom configuration is valid
```
sudo nginx -t

# Expected:
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```
Reboot
```
sudo reboot
```
Verify the security headers and proxying are correct
```
curl -k -I https://localhost/

# Expected:
HTTP/1.1 302 FOUND
Server: nginx
Date: Tue, 15 Sep 2026 13:06:24 GMT
Content-Type: text/html; charset=utf-8
Content-Length: 213
Connection: keep-alive
Location: /program_sign
Vary: Cookie
X-Frame-Options: DENY
Content-Security-Policy: frame-ancestors 'none';
X-XSS-Protection: 1; mode=block
X-Content-Type-Options: nosniff
Strict-Transport-Security: max-age=63072000; includeSubDomains
Referrer-Policy: same-origin
Feature-Policy: geolocation 'self'; vibrate 'none'
```
Remove the unused default
```
sudo rm -rf /etc/nginx/sites-available/default
```

### Configure Auditor Service -- `auditor.py`
Create the `systemd` service
```
sudo nano /etc/systemd/system/auditor.service
```
```
[Unit]
Description=Log Auditor Script Runner
After=network.target

[Service]
Type=simple
User=user
Group=user
WorkingDirectory=/home/user
Environment="PATH=/home/user/venv/bin"
Environment=PYTHONUNBUFFERED=1
ExecStart=/home/user/venv/bin/python auditor.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```
Start the service now and on boot
```
sudo systemctl daemon-reload
sudo systemctl enable --now auditor.service
```