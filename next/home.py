from flask import Blueprint, render_template
import next.utils as utils
from next.lib.pijemont import doc as doc_gen
from next.lib.pijemont import verifier

home = Blueprint(
    "home",
    __name__,
    template_folder="../dashboard/templates",
    static_folder="../dashboard/static",
)


@home.route("/")
def redirect_form():
    available_apps = utils.get_supported_apps()
    return render_template("home.html", available_apps=available_apps)
