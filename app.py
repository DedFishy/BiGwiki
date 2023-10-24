from flask import *
import os
from markdown import markdown
import users
import shutil

class App:
    def __init__(self, name):
        self.app = Flask(name)

        self.users = users.Users()

        self.wiki_name = os.getenv("WIKI_NAME")
        self.default_permission_level = os.getenv("DEFAULT_PERMISSION_LEVEL")

        if os.getenv("DEBUG"):
            self.app.config["TEMPLATES_AUTO_RELOAD"] = True

        self.register_paths()
    
    def read_md_file(self, path):
        if not os.path.exists(os.path.join("md", path)):
            path = "special/404.md"
        with open(os.path.join("md", path), "r+") as md:
            return markdown(md.read())

    def read_md_raw(self, path):
        if not os.path.exists(os.path.join("md", path)):
            path = "special/404.md"
        with open(os.path.join("md", path), "r+") as md:
            return md.read()

    def get_pages(self, subpath=""):
        pages = os.listdir(os.path.join("md", subpath))
        if subpath == "" and "special" in pages:
            pages.remove("special")
        for i in range(0, len(pages)):
            if ".md" in pages[i]:
                pages[i] = pages[i].split(".")[0]
            else:
                pages[i] = [pages[i], self.get_pages(os.path.join(subpath, pages[i]))]
        if "home" in pages:
            pages.remove("home")
        return pages
    
    def process_login(self):
        username = request.cookies.get("username", "")
        token = request.cookies.get("token", False)
        if token:
            token = self.users.check_token(username, token)
        
        if not token:
            permission_level = int(self.default_permission_level)
        else:
            permission_level = int(self.users.read_user(username)["rank"])
        
        return username, token, permission_level
    
    def render_error(self, title, content):
        result = self.read_md_file("special/error.md")
        result = result.replace("{{ title }}", title)
        result = result.replace("{{ errorcontent }}", content)

        return render_template("page.html" , wikiname=self.wiki_name, content=result, pagename=title, permissionlevel=0)
    
    def render_message(self, title, content):
        result = self.read_md_file("special/message.md")
        result = result.replace("{{ title }}", title)
        result = result.replace("{{ messagecontent }}", content)
        return render_template("page.html" , wikiname=self.wiki_name, content=result, pagename=title, permissionlevel=0)
    
    def validate_path(self, path, file=None):
        if path.strip() != path:
            return False
        if file:
            if file.strip() != file:
                return False
            if file == "":
                return False
            
        path = path.replace("/", "")
        path = path + file

        for char in path:
            if char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ _-1234567890":
                return False

        return True
    
    def register_paths(self):
        
        @self.app.route("/")
        def index():
            return render_page("home")
        
        @self.app.route("/sidebar")
        def sidebar():
            username, token, permission_level = self.process_login()
            pages = []
            if permission_level >= 0:
                pages = self.get_pages()
            return render_template("sidebar.html", wikiname=self.wiki_name, pages=pages, isloggedin=str(token).lower(), permissionlevel = permission_level, username=username)
        
        @self.app.route("/logout")
        def logout():
            if not request.origin:
                origin = "/"
            else:
                origin = request.origin
            response = redirect(origin)
            self.users.remove_token(request.cookies["username"], request.cookies["token"])
            response.delete_cookie("username")
            response.delete_cookie("token")

            return response

        @self.app.route("/login", methods=["POST"])
        def login():
            result = self.users.check_password(request.form["username"], request.form["password"])
            if result:
                token = self.users.create_token(request.form["username"])
                response = redirect(request.origin)
                response.set_cookie("token", token)
                response.set_cookie("username", request.form["username"])
                return response
            else:
                return self.render_error("Invalid login", "The login information you provided was wrong!")
        
        @self.app.route("/signup", methods=["POST"])
        def signup():
            result = self.users.create_user(request.form["username"], request.form["password"], 0)
            if result:
                token = self.users.create_token(request.form["username"])
                response = redirect(request.origin)
                response.set_cookie("token", token)
                response.set_cookie("username", request.form["username"])

                return response
        
        @self.app.route("/addfolder", methods=["POST"])
        def add_folder():
            username, token, permission_level = self.process_login()
                
            if permission_level < 1:
                return self.render_error("Not allowed", "You don't have permission to add folders!")
            
            adding_to = request.form["adding-to"]
            add_name = request.form["add-name"]

            if not self.validate_path(adding_to, add_name):
                return self.render_error("Invalid path or name", "You can only use a-z, A-Z, 0-9, - and _ in path and file names!")
            
            print("md" + adding_to)
            if not os.path.exists("md" + adding_to):
                return self.render_error("Path doesn't exist", "The path you're trying to add to doesn't exist!")

            new_folder = "md" + adding_to + add_name
            try:
                os.mkdir(new_folder)
            except Exception as e:
                return self.render_error("Folder creation error", "An error occurred: " + str(e))

            return self.render_message("Success", "The folder `" + new_folder + "` has been created.")

        @self.app.route("/addpage", methods=["POST"])
        def add_file():
            username, token, permission_level = self.process_login()
                
            if permission_level < 1:
                return self.render_error("Not allowed", "You don't have permission to add files!")
            
            adding_to = request.form["adding-to"]
            add_name = request.form["add-name"]

            if not self.validate_path(adding_to, add_name):
                return self.render_error("Invalid path or name", "You can only use a-z, A-Z, 0-9, - and _ in path and file names!")
            
            print("md" + adding_to)
            if not os.path.exists("md" + adding_to):
                return self.render_error("Path doesn't exist", "The path you're trying to add to doesn't exist!")

            new_file = "md" + adding_to + add_name
            try:
                with open(new_file + ".md", "w+") as file:
                    file.write("Write something in this file, for Pete's sake!")
            except Exception as e:
                return self.render_error("File creation error", "An error occurred: " + str(e))

            return self.render_message("Success", "The file `" + new_file + "` has been created.")
        
        @self.app.route("/deletepage", methods=["POST"])
        def delete_page():
            username, token, permission_level = self.process_login()
                
            if permission_level < 1:
                return self.render_error("Not allowed", "You don't have permission to delete files!")
            
            path = "md/" + request.form["path"] + ".md"
            print(path)

            if os.path.exists(path):
                os.remove(path)
                return self.render_message("Success", "The file `" + path + "` has been deleted.")

            return self.render_error("Not found", "The file you're trying to delete was not found.")
        
        @self.app.route("/deletefolder", methods=["POST"])
        def delete_folder():
            username, token, permission_level = self.process_login()
                
            if permission_level < 1:
                return self.render_error("Not allowed", "You don't have permission to delete folders!")
            
            path = "md" + request.form["path"]
            print(path)

            if os.path.exists(path):
                shutil.rmtree(path)
                return self.render_message("Success", "The folder `" + path + "` has been deleted.")

            return self.render_error("Not found", "The folder you're trying to delete was not found.")
        
        @self.app.route("/editpage", methods=["POST"])
        def editpage():
            username, token, permission_level = self.process_login()
                
            if permission_level < 1:
                return self.render_error("Not allowed", "You don't have permission to edit pages!")

            path = "md/" + request.form["path"] + ".md"
            print(path)



            if os.path.exists(path):
                
                if path != request.form["name"] + ".md":
                    if request.form["path"] == "home" or request.form["path"].startswith("special"):
                        return self.render_error("Not allowed", "You can't rename this page!")
                    os.rename(path, "md/" + request.form["name"] + ".md")
                    path = "md/" + request.form["name"] + ".md"
                with open(path, "w") as file:
                    file.write(request.form["content"])
                return redirect("/" + request.form["name"])
            
            return self.render_error("Not found", "The page you're trying to edit was not found.")
        
        @self.app.route("/<path:page>")
        def render_page(page):
            username, token, permission_level = self.process_login()
                
            if permission_level < 0:
                return self.render_error("Not allowed", "You don't have permission to access this wiki! Try logging in to an account.")

            return render_template("page.html" , wikiname=self.wiki_name, content=self.read_md_file(page + ".md"), contentraw=self.read_md_raw(page + ".md"), pagename=page,  permissionlevel=permission_level)

        

        @self.app.route("/favicon.ico")
        def favicon():
            return send_from_directory("static", "favicon.ico")
    
    def run(self, host, port):
        self.app.run(host, port)