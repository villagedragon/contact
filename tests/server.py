"""Defines functions related to the custom Flask testing server."""

import base64
import os
import random
import secrets
import threading
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Generator
from typing import Set

from flask import Blueprint
from flask import Flask
from flask import jsonify
from flask import render_template
from flask import request
from flask import send_from_directory
from flask import session
from werkzeug.datastructures import FileStorage
from werkzeug.datastructures import ImmutableMultiDict

from tests.data_structures import ImmutableDict


TEST_SERVER_INFO = ImmutableDict(
    {
        "port": 5000,
        "secret_key": secrets.token_hex(16),
        "submit_route": "/submit",
    }
)

CONFIG_DATA_MAP: Dict[str, Any] = {}


def generate_unique_random_ports(num_ports: int) -> Generator[int, None, None]:
    """Generator that only yield unique random ports."""
    # create set of used ports
    used_ports: Set[int] = set()

    # loop over ports
    while len(used_ports) < num_ports:
        # get random port
        port = random.randint(5001, 65535)

        # check it is unique
        if port not in used_ports:
            # send it forward
            yield port

            # mark it as used
            used_ports.add(port)


def get_html_tag_from_mimetype(file: FileStorage, encoded_data: str) -> str:
    """Generate an HTML tag based on the MIME type of the file."""
    # create data URL for reuse below
    data_url = f"data:{file.mimetype};base64,{encoded_data}"

    # match the mimetype
    match file.mimetype.split("/")[0]:
        case "image":
            tag = f"<img src={data_url!r}>"
        case "video":
            tag = (
                f"<video controls>"
                f"    <source src={data_url!r} type={file.mimetype!r}>"
                f"    Your browser does not support the video tag."
                f"</video>"
            )
        case "audio":
            tag = (
                f"<audio controls>"
                f"    <source src={data_url!r} type={file.mimetype!r}>"
                f"    Your browser does not support the audio tag."
                f"</audio>"
            )
        case _:
            tag = f"<a href={data_url!r}>Download {file.filename}</a>"

    return tag


def process_form_data(form_data: ImmutableMultiDict) -> Dict[str, Any]:
    """Process form data to handle multi-values."""
    # setup processed results
    processed_data: Dict[str, Any] = {}

    # check form key/values
    for key, value in form_data.items(multi=True):
        # check if key indicates file(s)
        if key in request.files:
            processed_data[key] = ""

        # check to see if there are multiple values
        elif key in processed_data:
            processed_data[key] += f", {value}"

        # handle normally
        else:
            processed_data[key] = value

    return processed_data


def process_uploaded_files(processed_data: Dict[str, Any]) -> None:
    """Process uploaded files and generate HTML tags."""
    # get list of tuples for key/files pairs
    for key, files in request.files.lists():
        # loop over each file
        for file in files:
            # make sure it exists
            if file.filename:
                # get data from file
                file_data = file.read()

                # convert to base64 for data URL creation later ...
                encoded_data = base64.b64encode(file_data).decode("utf-8")

                # create tag
                tag = get_html_tag_from_mimetype(file, encoded_data)

                # update current results
                if key in processed_data:
                    processed_data[key] += "<br>" + tag
                else:
                    processed_data[key] = tag


def create_main_blueprint(
    serve_directory: Path, config_data_map: Dict[str, Any]
) -> Blueprint:
    """Builds a Flask Blueprint for all main routes."""
    main_bp = Blueprint("main", __name__)

    @main_bp.route("/")
    def index():
        """Serve the index file in the project dir."""
        # get token from query parameters
        token = request.args.get("token")

        # check if token exists
        if token and (config_data := config_data_map.get(token)):
            # update session token
            session["config_data_token"] = token

            # notify
            print(f"Received token: {token}")
            print(f"Website will be configured using: {config_data}")

        return send_from_directory(serve_directory, "index.html")

    @main_bp.route("/<path:path>")
    def other_root_files(path):
        """Serve any other files (e.g. config.json) from the project dir."""
        if "config.json" in path and (token := session.get("config_data_token")):
            config_data = config_data_map[token]
            print(f"Serving updated config.json data: {config_data}")
            return jsonify(config_data)
        else:
            return send_from_directory(serve_directory, path)

    @main_bp.route("/styles/<path:path>")
    def serve_styles(path):
        """Send any CSS files from the temp dir."""
        css_file = os.path.join("styles", path)
        if os.path.exists(os.path.join(serve_directory, css_file)):
            return send_from_directory(serve_directory, css_file)
        else:
            return "CSS file not found\n", 404

    @main_bp.route("/scripts/<path:path>")
    def serve_scripts(path):
        """Send any JavaScript files from the temp dir."""
        js_file = os.path.join("scripts", path)
        if os.path.exists(os.path.join(serve_directory, js_file)):
            return send_from_directory(serve_directory, js_file)
        else:
            return "JavaScript file not found\n", 404

    return main_bp


def create_config_blueprint(config_data_map: Dict[str, Any]) -> Blueprint:
    """Builds a Flask Blueprint for all config updating routes."""
    config_bp = Blueprint("config", __name__)

    @config_bp.route("/update_config", methods=["POST"])
    def update_config():
        """Update session with new JSON data."""
        if request.is_json:
            config_data = request.json
            token = secrets.token_urlsafe(16)
            session["config_data_token"] = token
            config_data_map[token] = config_data
            print(f"Updating config data: {config_data}")
            return jsonify({"token": token}), 200
        else:
            return "Invalid request format. Only JSON requests are accepted.\n", 400

    @config_bp.route("/reset_config")
    def reset_config():
        """Clears the session cache of any config data token."""
        session.pop("config_data_token", None)
        return "Configuration reset successfully!\n", 200

    return config_bp


def create_submit_blueprint() -> Blueprint:
    """Builds a Flask Blueprint for all form submission routes."""
    submit_bp = Blueprint("submit", __name__)

    @submit_bp.route(TEST_SERVER_INFO["submit_route"], methods=["POST"])
    def submit_form():
        """Render HTML form data as a response form."""
        # notify what form data was received
        print(f"Form data received: {request.form}")

        # notify what data was processed
        processed_data = process_form_data(request.form)
        print(f"Processed data: {processed_data}")

        # notify what files were added (if any)
        process_uploaded_files(processed_data)
        print(f"Added uploaded files: {request.files}")

        # render the contact form response
        return render_template("form_response_template.html", form_data=processed_data)

    return submit_bp


def build_flask_app(serve_directory: Path) -> Flask:
    """Assembles Flask app to serve static site."""
    # get instance
    app = Flask(__name__)

    # set port
    app.config["PORT"] = TEST_SERVER_INFO["port"]

    # set secret key
    app.config["SECRET_KEY"] = TEST_SERVER_INFO["secret_key"]

    # set up config data map
    config_data_map = CONFIG_DATA_MAP

    # build blueprints
    main_bp = create_main_blueprint(serve_directory, config_data_map)
    config_bp = create_config_blueprint(config_data_map)
    submit_bp = create_submit_blueprint()

    # add blueprints to Flask app
    app.register_blueprint(main_bp)
    app.register_blueprint(config_bp)
    app.register_blueprint(submit_bp)

    return app


def run_threaded_flask_app(app: Flask) -> None:
    """Run a Flask app using threading."""
    # launch Flask app for project dir in thread
    thread = threading.Thread(target=app.run)
    thread.daemon = True
    thread.start()
