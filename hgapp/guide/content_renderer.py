from django.templatetags.static import static
import re

# Support for "STML" or Spencer Text Markup Language
# This is a super-janky markup language that is intended only for admin use.
# DO NOT GIVE USERS ACCESS TO THESE METHODS. THEY ARE NOT SECURE OR EVEN REALLY STABLE.
def render_content(unrendered_content, pics_by_slug):
    rendered_content = __render_section_links(str(unrendered_content))
    rendered_content = __render_columns(rendered_content)
    rendered_content = __render_gm_tip(rendered_content)
    rendered_content = __render_examples(rendered_content)
    rendered_content = __render_images(rendered_content, pics_by_slug)
    return rendered_content

def __render_images(content, pics_by_slug):
    return re.sub(r"(<p>[\s]*)?\{![\s]*image(-sm)? ([\w./-]+)[\s]*!\}([\s]*</p>)?",
                  lambda x: '<div class="css-guide-image{}" style="background-image: url(\'{}\');"></div>'.format(
                      x.group(2) if x.group(2) else "",
                      pics_by_slug[x.group(3)].picture.url),
                  content)


# {{article-slug|link-text}} to link to that article
def __render_section_links(content):
    return re.sub(r"\{\{([\w-]+)\|([\w\s-]+)\}\}", r"<a href=#\1>\2</a>", content)


# {!col1!} {!col2!} {!colend!}
def __render_columns(content):
    col1_start = '<div class="row"><div class="col-md-6 col-xs-12">'
    col2_start = '</div><div class="col-md-6 col-xs-12">'
    col_end = '</div></div>'
    rendered_content = re.sub(r"(<p>[\s]*)?\{!col1!\}([\s]*</p>)?", col1_start, content)
    rendered_content = re.sub(r"(<p>[\s]*)?\{!col2!\}([\s]*</p>)?", col2_start, rendered_content)
    rendered_content = re.sub(r"(<p>[\s]*)?\{!colend!\}([\s]*</p>)?", col_end, rendered_content)
    return rendered_content


def __render_gm_tip(content):
    start = '<div class="css-gm-tip"><div class="css-gm-tip-header"><div class="css-guide-image-xs" style="background-image: url(\'{}\')"></div> GM Tip</div><div class="css-gm-tip-content">' \
        .format(static("guide/graphics/Sky_D10.png"))
    end = '</div></div>'
    rendered_content = re.sub(r"(<p>[\s]*)?\{!start-gm-tip!\}([\s]*</p>)?", start, content)
    rendered_content = re.sub(r"(<p>[\s]*)?\{!end-gm-tip!\}([\s]*</p>)?", end, rendered_content)
    return rendered_content


def __render_examples(content):
    start = '<div class="css-examples">' \
            '<a class="wiki-entry-collapsible" role="button">' \
            '<div class="css-examples-header"><div class="css-guide-image-xs" style="background-image: url(\'{}\')">' \
            '</div> {} <small style="font-size: 12px; font-weight: 400;">(<span class="visible-xs-inline visible-sm-inline">tap</span><span class="hidden-xs hidden-sm">click</span> to expand)</small></div>' \
            '</a>' \
            '<div class="css-examples-content collapse-content"  style="display:none;">' \
        .format(static("guide/graphics/Pink_D10.png"), r"\2")
    end = '</div></div>'
    rendered_content = re.sub(r"(<p>[\s]*)?\{!start-examples\|([\w\s]+)!\}([\s]*</p>)?", start, content)
    rendered_content = re.sub(r"(<p>[\s]*)?\{!end-examples!\}([\s]*</p>)?", end, rendered_content)
    return rendered_content

# Render text on save. Replaces
# {{fancy-section}} with entire section
