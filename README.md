# Web app for an assignment of the NPFL140 course on Large Language Models

This web app runs during the machine translation assignment in the [course on large language models](https://ufal.mff.cuni.cz/courses/npfl140) (LLMs) at Charles University. The students are assigned paragraphs in several languages, and they are supposed to translate them using several LLMs that we provide them via an API. This app gives feedback in the form of the chrF score for a secret reference translation. When the students are happy with their results, they submit their scores to a leaderboard. For more details on the assignment, you can read the [complete instructions for students](https://github.com/kasnerz/npfl140/tree/main/09_translation).

After the submission deadline, we switch the app to a different mode showing the complete leaderboards and reference translations.

## Running the app
The app uses `flask` for the web service and `sacrebleu` to compute the chrF score.

The test data are provided in a CSV file (`data.csv` contains our test data from 2024) with three columns: language code, text in the source text, and translation into English.

During the submission phase, run the app using the following command:
```
python3 server.py data.csv --port 8080
```

The submissions are logged into the JSON files in the logs directory.

After the submission phase, run the following
```
python3 server.py data.csv --port 8080 --after-competition
```
