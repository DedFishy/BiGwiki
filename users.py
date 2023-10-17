import bcrypt
import os
import errors
import binascii
from uuid import uuid4

class Users:
    def __init__(self):
        pass

    def create_user(self, username, password, rank):
        if os.path.exists("users/" + username + ".user"):
            raise errors.UserExistsError()
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode(), salt)

        with open("users/" + username + ".user", "w+") as user_file:
            user_file.write(password_hash.hex() + "\n" + str(rank))
        return True
        
    def read_user(self, username):
        with open("users/" + username + ".user", "r+") as user_file:
            data = user_file.readlines()
        
        return {"password_hash": data[0], "rank": data[1]}
    
    def check_password(self, username, password):
        try:
            password_hashed = self.read_user(username)["password_hash"]
            return bcrypt.checkpw(password.encode(), bytes.fromhex(password_hashed))
        except FileNotFoundError:
            return False
    
    def create_token(self, username):
        token = binascii.hexlify(os.urandom(20)).decode()
        salt = bcrypt.gensalt()
        token_hash = bcrypt.hashpw(token.encode(), salt)
        if not os.path.exists("tokens/" + username):
            os.mkdir("tokens/" + username)
        with open("tokens/" + username + "/" + uuid4().hex + ".token", "w+") as token_file:
            token_file.write(token_hash.hex())
        return token
    
    def check_token(self, username, token):
        if not username or not token:
            return False
        for file in os.listdir("tokens/" + username):
            print("token file", file)
            with open("tokens/" + username + "/" + file, "r") as token_file:
                if bcrypt.checkpw(token.encode(), bytes.fromhex(token_file.read())):
                    return True
        return False
    
    def remove_token(self, username, token):
        if not username or not token:
            return False
        for file in os.listdir("tokens/" + username):
            token_file_target = None
            with open("tokens/" + username + "/" + file, "r") as token_file:
                if bcrypt.checkpw(token.encode(), bytes.fromhex(token_file.read())):
                    token_file_target = file
            if token_file_target:
                os.remove("tokens/" + username + "/" + token_file_target)
                return True
        return False

if __name__ == "__main__":
    users = Users()
    print("BiGwiki User Manager")
    print("""
1. Create user
2. Read user
3. Check password
4. Create token
5. Check token
""")
    action = input(">")

    if action == "1":
        users.create_user(input("Username >"), input("Password >"), input("Rank >"))
    elif action == "2":
        print(users.read_user(input("Username >")))
    elif action == "3":
        print(users.check_password(input("Username >"), input("Password >")))
    elif action == "4":
        print(users.create_token(input("Username >")))
    elif action == "5":
        print(users.check_token(input("Username >"), input("Token >")))