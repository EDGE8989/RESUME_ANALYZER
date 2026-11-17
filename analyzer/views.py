import json
import re

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Analysis
from .nlp.grammar import check_grammar, pos_tag_tokens, tokenize_sentences
from .nlp.spelling import check_spelling
from .nlp.languagetool import check_with_languagetool

MAX_TEXT_LENGTH = 10000


def _run_analysis(text):
    spelling_issues, corrected = check_spelling(text)
    grammar_issues = check_grammar(corrected)
    grammar_issues.extend(check_with_languagetool(corrected))
    # Prefer the external local engine's richer match when spans overlap.
    unique = {}
    for issue in grammar_issues:
        key = (issue["start"], issue["end"])
        if key not in unique or issue.get("category", "").startswith("languagetool:"):
            unique[key] = issue
    grammar_issues = sorted(unique.values(), key=lambda issue: issue["start"])
    # Apply grammar substitutions from right to left so offsets stay valid.
    for issue in reversed(grammar_issues):
        corrected = corrected[:issue["start"]] + issue["suggestion"] + corrected[issue["end"]:]
    issues = sorted(spelling_issues + grammar_issues, key=lambda item: item["start"])
    for issue in issues:
        issue.setdefault("original_text", issue.get("word", ""))
        issue.setdefault("category", issue.get("rule", issue.get("type", "language")))
        issue.setdefault("suggestions", [issue["suggestion"]] if issue.get("suggestion") else [])
        issue.setdefault("confidence", 0.8)
        issue.setdefault("severity", "moderate" if issue.get("type") == "grammar" else "minor")
    words = re.findall(r"\b[\w']+\b", text)
    return {
        "original_text": text,
        "corrected_text": corrected,
        "issues": issues,
        "word_count": len(words),
        "sentence_count": len(tokenize_sentences(text)),
        "issue_count": len(issues),
        "pos_tags": pos_tag_tokens(text)[:40],
    }


def home(request):
    return render(request, "analyzer/home.html")


@require_POST
def analyze(request):
    text = request.POST.get("text", "").strip()
    if not text:
        message = "Enter some text to analyze."
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"error": message}, status=400)
        return render(request, "analyzer/home.html", {"error": message, "input_text": text})
    if len(text) > MAX_TEXT_LENGTH:
        message = f"Please keep your text under {MAX_TEXT_LENGTH:,} characters."
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"error": message}, status=400)
        return render(request, "analyzer/home.html", {"error": message, "input_text": text[:MAX_TEXT_LENGTH]})
    result = _run_analysis(text)
    record = Analysis.objects.create(
        original_text=text,
        corrected_text=result["corrected_text"],
        issues=result["issues"],
        word_count=result["word_count"],
        issue_count=result["issue_count"],
    )
    result["analysis_id"] = record.pk
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(result)
    return render(request, "analyzer/home.html", {"result": result, "input_text": text})


def history(request):
    records = Analysis.objects.all()[:50]
    return render(request, "analyzer/history.html", {"records": records})


def history_detail(request, pk):
    record = get_object_or_404(Analysis, pk=pk)
    result = {
        "original_text": record.original_text,
        "corrected_text": record.corrected_text,
        "issues": record.issues,
        "word_count": record.word_count,
        "sentence_count": len(tokenize_sentences(record.original_text)),
        "issue_count": record.issue_count,
        "pos_tags": pos_tag_tokens(record.original_text)[:40],
    }
    return render(request, "analyzer/history_detail.html", {"record": record, "result": result})


@require_POST
def history_delete(request, pk):
    get_object_or_404(Analysis, pk=pk).delete()
    return redirect("history")
