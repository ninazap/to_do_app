import hashlib


# Проверка паролей
def test_passwords():
    passwords = {
        "admin": "admin_password",
        "alexey": "alexey_password",
        "maria": "maria_password",
        "dmitry": "dmitry_password",
        "olga": "olga_password"
    }

    for user, password in passwords.items():
        sha256_hash = hashlib.sha256(password.encode()).hexdigest()
        print(f"{user}: {sha256_hash}")