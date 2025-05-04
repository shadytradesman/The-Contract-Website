from markdown import Markdown


def parse(text):
    md = Markdown(extensions=["codehilite", "tables", "smarty", "admonition", "toc", "fenced_code"])
    html = md.convert(text)
    return html
