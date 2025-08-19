lifetime = datetime.datetime.now() + datetime.timedelta(minutes=5)

payload = {
    'username' : username,
    'admin' : 1,
    'exp' : lifetime
}

access_token = jwt.encode(payload, self.secret, algorithm="HS256")