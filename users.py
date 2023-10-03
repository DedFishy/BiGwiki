import bcrypt

class Users:
    def __init__(self):
        pass

    def create_user(self, username, password, rank):
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode(), salt)

        with open("users/" + username + ".user", "w+") as user_file:
            user_file.write(password_hash.hex() + "\n" + rank)
        
    def read_user(self, username):
        with open("users/" + username + ".user", "r+") as user_file:
            data = user_file.readlines()
        
        return {"password_hash": data[0], "rank": data[1]}
    
    def check_password(self, username, password):
        password_hashed = self.read_user(username)["password_hash"]
        return bcrypt.checkpw(password.encode(), bytes.fromhex(password_hashed))

if __name__ == "__main__":
    users = Users()
    print("BiGwiki User Manager")
    print("""
1. Create user
2. Read user
3. Check password
""")
    action = input(">")

    if action == "1":
        users.create_user(input("Username >"), input("Password >"), input("Rank >"))
    elif action == "2":
        print(users.read_user(input("Username >")))
    elif action == "3":
        print(users.check_password(input("Username >"), input("Password >")))