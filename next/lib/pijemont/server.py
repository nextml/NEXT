from flask import Flask, request, render_template
import json, sys, verifier
import doc as doc_gen

app = Flask(__name__, static_url_path="/static")


@app.route("/doc/<string:form>")
def doc(form="raw"):
    api, blank, pretty = doc_gen.get_docs("example.yaml", ".")

    if form == "pretty":
        return render_template("doc.html", doc_string=pretty, base_dir="/static")
    elif form == "blank":
        return render_template("raw.html", doc=blank)
    elif form == "raw":
        return render_template("raw.html", doc=api)

    return json.dumps(api)


@app.route("/form/<string:fn>")
def form(fn="excite"):
    api, _ = verifier.load_doc("example.yaml", ".")
    return render_template(
        "form.html", api_doc=api, submit="/submit", function_name=fn, base_dir="/static"
    )


@app.route("/submit", methods=["POST"])
def submit():
    print(json.dumps(request.data))
    return "done"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(sys.argv[1]), debug=True)
