import string
import secrets


def generate_password():
    allowed_symbols = "!?#$%&"
    alphabet = string.ascii_letters + string.digits + allowed_symbols
    while True:
        password = ''.join(secrets.choice(alphabet) for i in range(10))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password)
                and any(c in allowed_symbols for c in password)):
            break
    return password
