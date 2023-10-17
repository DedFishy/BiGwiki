from flask import *
import os
from markdown import markdown
import users

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

    def get_pages(self, subpath=""):
        pages = os.listdir(os.path.join("md", subpath))
        for i in range(0, len(pages)):
            if ".md" in pages[i]:
                pages[i] = pages[i].split(".")[0]
            else:
                if pages[i] not in ["special"]:
                    pages[i] = [pages[i], self.get_pages(os.path.join(subpath, pages[i]))]
                else:
                    pages.pop(i)
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
            return render_template("sidebar.html", wikiname=self.wiki_name, pages=pages, isloggedin=str(token).lower(), username=username)
        
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
                return render_template("page.html" , wikiname=self.wiki_name, content=self.read_md_file("special/bad-login.md"), pagename="Bad login", permissionlevel=self.default_permission_level)
        
        @self.app.route("/signup", methods=["POST"])
        def signup():
            result = self.users.create_user(request.form["username"], request.form["password"], 0)
            if result:
                token = self.users.create_token(request.form["username"])
                response = redirect(request.origin)
                response.set_cookie("token", token)
                response.set_cookie("username", request.form["username"])

                return response
        
        @self.app.route("/<path:page>")
        def render_page(page):
            username, token, permission_level = self.process_login()
                
            if permission_level < 0:
                return render_template("page.html" , wikiname=self.wiki_name, content=self.read_md_file("special/not-allowed.md"), pagename="Not allowed",  permissionlevel=permission_level)
            return render_template("page.html" , wikiname=self.wiki_name, content=self.read_md_file(page + ".md"), pagename=page,  permissionlevel=permission_level)

        @self.app.route("/favicon.ico")
        def favicon():
            return send_from_directory("static", "favicon.ico")
    
    def run(self, host, port):
        self.app.run(host, port)