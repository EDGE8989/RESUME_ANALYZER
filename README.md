# ClearWrite — Intelligent Grammar and Spelling Correction Engine

A small, explainable English writing assistant built with Django and classical NLP techniques. The spelling and grammar checks run locally in Python; no hosted grammar or generative AI service is called. The interface is responsive and includes saved analysis history.

## Features

- Text and sentence tokenization, input normalization, and basic POS tagging.
- Custom Levenshtein minimum edit distance implementation.
- Dictionary based spelling detection with frequency ranked candidates and a small bigram context tie breaker.
- Grammar rules for common subject–verb agreement, article selection, past time markers, spacing, and punctuation.
- Narrow contextual rules for selected preposition collocations, common homophones, and count noun agreement.
- Structured issue records include the original span, replacement choices, category, confidence, severity, offsets, and explanation.
- Explanations, suggested corrected text, original/corrected comparison, and saved history backed by SQLite.
- NLTK word corpus and POS tagger are used when their datasets are installed; compact built in lexicon and rule tagger keep the app working offline.

The rule set is intentionally understandable and limited. It demonstrates classical techniques and is not a complete proofreader. Suggestions should be reviewed by the writer.

## Audit notes and measured evaluation

The original implementation used a very small fallback vocabulary and treated any unknown token as a spelling error. Its past-tense heuristic also formed `-ed` for almost any word after “yesterday”, which could create false corrections. The current version uses conservative known verb forms, morphology-aware dictionary lookup for common inflections, and small context patterns where the evidence is fairly strong. The issue pipeline now adds categories, confidence values, severity, original text and candidate lists. Confidence is a rule heuristic, not a calibrated probability.

Run the labeled smoke evaluation with:

```powershell
python -c "from analyzer.nlp.evaluate import evaluate; print(evaluate())"
```

The bundled 20-sentence evaluation set currently reports 10 true positives, 0 false positives, and 0 false negatives for the coarse question “does this sentence contain any labeled issue?” (precision 1.00, recall 1.00, F1 1.00, false-positive rate 0.00). Average latency in a local run was about 259 ms per sentence, including cold-start dictionary setup. These numbers describe only this small hand-authored regression set; they are not representative benchmark claims, and the score does not assess every suggested correction. Expand the dataset before drawing accuracy conclusions. The preceding code did not have a comparable labeled evaluation harness, so there is no reliable before score.

### Current limitations from the audit

- This remains a pattern based checker with a compact lexicon; long-tail vocabulary and nuanced syntax can be missed or falsely flagged.
- The contextual phrase rules cover selected examples, not general language understanding. No pretrained model was added because this project prioritizes offline operation and explainability.
- POS tagging is only analysis metadata and is not a full parse. Sentence segmentation does not specially handle abbreviations.
- Severity and confidence are transparent heuristic labels, not calibrated probabilities.
- NLTK corpus mode may take longer to initialize and should be benchmarked separately on the target hardware.

## Requirements

- Python 3.10+
- pip and a virtual environment

## Setup (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. The Django admin is available at `/admin/` after creating an admin user with `python manage.py createsuperuser`.

### Optional NLTK datasets

The app gracefully falls back when NLTK datasets are missing. To use the larger NLTK English word list and averaged-perceptron POS tagger, install the datasets once:

```powershell
python -m nltk.downloader words averaged_perceptron_tagger_eng
```

On older NLTK releases, the POS model may be named `averaged_perceptron_tagger`; download that resource if the newer name is unavailable.

## Run checks

```powershell
python manage.py test analyzer
```

The tests cover edit distance, spelling and grammar rules, tokenizers, HTTP input validation, and saving/reopening an analysis.

## Project structure

```text
grammar_engine/       Django project settings and URL configuration
analyzer/models.py    Analysis history model
analyzer/views.py     Input validation, analysis orchestration, and history views
analyzer/nlp/         Separate spelling and grammar engines
templates/            Django templates
static/               Responsive CSS and small editor script
```

## Algorithms at a glance

1. Regex tokenization identifies words while preserving punctuation and original text offsets.
2. Spelling candidates are filtered by length and ranked using custom dynamic-programming edit distance, then word frequency. A small transparent bigram table breaks frequency ties using immediate context.
3. Grammar checks apply explicit token-pattern rules. Each result includes the matched text, rule category, a candidate, and a plain language explanation.
4. POS tagging uses NLTK if available. A suffix and closed-class rule tagger is the offline fallback.

SQLite history contains submitted writing. Clear individual entries from the History detail screen. This academic demo does not include account isolation or production deployment hardening.
