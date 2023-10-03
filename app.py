from flask import *
import os
from markdown import markdown

class App:
    def __init__(self, name):
        self.app = Flask(name)

        self.wiki_name = os.getenv("WIKI_NAME")

        if os.getenv("DEBUG"):
            self.app.config["TEMPLATES_AUTO_RELOAD"] = True

        self.register_paths()
    
    def read_md_file(self, path):
        with open(os.path.join("md", path), "r+") as md:
            return markdown(md.read())

    def get_pages(self, subpath=""):
        pages = os.listdir(os.path.join("md", subpath))
        for i in range(0, len(pages)):
            if ".md" in pages[i]:
                pages[i] = pages[i].split(".")[0]
            else:
                pages[i] = [pages[i], self.get_pages(os.path.join(subpath, pages[i]))]
        if "index" in pages:
            pages.remove("index")
        return pages
    
    def register_paths(self):
        
        @self.app.route("/")
        def index():
            return render_template("page.html" , wikiname=self.wiki_name, content=self.read_md_file("index.md"))
        
        @self.app.route("/sidebar")
        def sidebar():
            return render_template("sidebar.html", wikiname=self.wiki_name, pages=self.get_pages())
        
        @self.app.route("/<path:page>")
        def render_page(page):
            return render_template("page.html" , wikiname=self.wiki_name, content=self.read_md_file(page + ".md"))
    
    def run(self, host, port):
        self.app.run(host, port)