#!/usr/bin/env python3

import argparse
from collections import namedtuple
import datetime
import hashlib
import json
import csv
import os
import subprocess

import flask
from flask import Flask
import sacrebleu


app = Flask(__name__, template_folder='.')

DATA = []

TestSet = namedtuple("TestSet", ["id", "language", "language_full", "source", "reference"])
Result = namedtuple("Result", ["rank", "team_name", "timestamp", "chrf"])

LANGUAGES = {
	"cs": "Czech",
	"de": "German",
	"hsb": "Upper Sorbian",
	"gla": "Scottish Gaelic",
	"gle": "Irish",
	"epo": "Esperanto",
	"iku": "Inuktitut",
	"ukr": "Ukrainian",
	"hau": "Hausa",
	"tel": "Telugu",
	"zho": "Chinese",
	"ita": "Italian",
	"nor": "Norwegian",
	"ltz": "Luxembourgish",
	"ori": "Odia",
	"sxu": "Saxon German",
	"pl": "Polish",
	"csb": "Kashubian",
	"yid": "Yidish",
	"he": "Hebrew",
	"srd": "Sardinian"
}


@app.route("/script.js")
def script():
    return flask.send_file("script.js")


@app.route("/")
def index():
    if app.config["after_competition"]:
        return leaderboard()
    return flask.render_template("page.html", test_data=DATA)


def collect_logs():
    for path, _, files in os.walk("logs"):
        for f in files:
            with open(os.path.join(path, f)) as j:
                try:
                    yield json.load(j)
                except json.JSONDecodeError:
                    pass


def format_time(timestamp):
    return datetime.datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def get_leaderboards():
    results = [[] for _ in DATA]
    for log in collect_logs():
        results[log["test_set_id"]].append(
            (log["team_name"], format_time(log["timestamp"]), log["chrf"]))

    unique_results = []
    for result_list in results:
        unique_dict = {}
        for team_name, timestamp, chrf in result_list:
            if team_name not in unique_dict or unique_dict[team_name][-1] < chrf:
                unique_dict[team_name] = (team_name, timestamp, chrf)
        unique_results.append(list(unique_dict.values()))

    leaderboards = []
    for result_list in unique_results:
        result_list.sort(key=lambda x: x[-1], reverse=True)
        if not app.config["after_competition"]:
            result_list = result_list[:10]
        leaderboards.append(
            [Result(i + 1, team_name, timestamp, chrf)
             for i, (team_name, timestamp, chrf)
             in enumerate(result_list)])

    return leaderboards


@app.route("/leaderboard")
def leaderboard():
    return flask.render_template(
        "leaderboard.html",
        test_data=zip(DATA, get_leaderboards()),
        after_competition=app.config["after_competition"])


@app.route("/mt_eval", methods=["POST"])
def mt_eval():
    team_name = flask.request.form["team_name"]
    test_set_id = int(flask.request.form["test_set_id"])
    translation = flask.request.form["translation"]
    reference = DATA[test_set_id].reference
    language = DATA[test_set_id].language

    # Copute chrF score using sacrebleu
    chrf = sacrebleu.sentence_chrf(translation, [reference])

    # Log the submission
    if flask.request.form["log_attempt"] == "true":
        submission_hash = hashlib.md5((team_name + language + translation).encode()).hexdigest()
        os.makedirs(f"logs/{submission_hash[:2]}", exist_ok=True)
        with open(f"logs/{submission_hash[:2]}/{submission_hash}.json", "w") as f:
            json.dump({
                "team_name": team_name,
                "test_set_id": test_set_id,
                "language": language,
                "translation": translation,
                "timestamp": datetime.datetime.now().isoformat(),
                "chrf": chrf.score
            }, f)

    return flask.jsonify({"chrf": chrf.score})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to listen on.")
    parser.add_argument(
        "--port", default=5000, type=int, help="Port to listen on.")
    parser.add_argument(
        "data", help="csv file with test data.", type=argparse.FileType("r"))
    parser.add_argument(
        "--after-competition", action="store_true",
        help="It is already after the competition.")
    args = parser.parse_args()

    args.data.readline()
    reader = csv.reader(args.data)
    for i, row in enumerate(reader):
        DATA.append(
            TestSet(i, row[0], LANGUAGES[row[0]], row[1], row[2]))

    args.data.close()

    os.makedirs("logs", exist_ok=True)

    # Store if it is after the competition
    app.config["after_competition"] = args.after_competition

    app.run(host=args.host, port=args.port, debug=True)
