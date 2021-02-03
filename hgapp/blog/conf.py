from django.conf import settings  # noqa

from appconf import AppConf

from .utils import load_path_attr


def is_installed(package):
    try:
        __import__(package)
        return True
    except ImportError:
        return False


DEFAULT_MARKUP_CHOICE_MAP = {
    "markdown": {"label": "Markdown", "parser": "blog.parsers.markdown_parser.parse"}
}
if is_installed("creole"):
    DEFAULT_MARKUP_CHOICE_MAP.update({
        "creole": {"label": "Creole", "parser": "blog.parsers.creole_parser.parse"},
    })


class PinaxBlogAppConf(AppConf):

    ALL_SECTION_NAME = "all"
    SECTIONS = []
    UNPUBLISHED_STATES = [
        "Draft"
    ]
    FEED_TITLE = "Blog"
    SECTION_FEED_TITLE = "Blog (%s)"
    MARKUP_CHOICE_MAP = DEFAULT_MARKUP_CHOICE_MAP
    MARKUP_CHOICES = DEFAULT_MARKUP_CHOICE_MAP
    SCOPING_MODEL = None
    SCOPING_URL_VAR = None
    SLUG_UNIQUE = False
    PAGINATE_BY = 10
    HOOKSET = "blog.hooks.PinaxBlogDefaultHookSet"
    ADMIN_JS = ("js/admin_post_form.js",)

    def configure_markup_choices(self, value):
        return [
            (key, value[key]["label"])
            for key in value.keys()
        ]

    def configure_hookset(self, value):
        return load_path_attr(value)()

    class Meta:
        prefix = "pinax_blog"
