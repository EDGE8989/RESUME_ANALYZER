"""Dictionary spelling correction with an in-house Levenshtein algorithm."""
import re
from collections import Counter
from functools import lru_cache
from collections import defaultdict

# A compact fallback lexicon keeps the app useful offline. If the NLTK words
# corpus is installed, it is merged in at runtime.
BASE_FREQUENCIES = {
    "a": 50000, "about": 9000, "after": 8000, "all": 12000, "also": 7000,
    "an": 30000, "and": 60000, "are": 30000, "as": 35000, "at": 35000,
    "be": 50000, "because": 8000, "been": 15000, "before": 8000, "being": 6000,
    "but": 30000, "by": 25000, "can": 20000, "could": 10000, "day": 8000,
    "do": 30000, "does": 15000, "done": 7000, "each": 7000, "english": 3000,
    "error": 2000, "example": 3000, "for": 50000, "from": 30000, "get": 10000,
    "good": 10000, "grammar": 1000, "have": 40000, "he": 30000, "her": 20000,
    "here": 9000, "him": 15000, "his": 30000, "i": 60000, "if": 25000,
    "in": 60000, "into": 15000, "is": 60000, "it": 60000, "its": 15000,
    "just": 10000, "language": 7000, "like": 12000, "make": 12000, "many": 12000,
    "me": 20000, "more": 30000, "my": 30000, "need": 12000, "new": 15000,
    "not": 50000, "of": 65000, "on": 50000, "one": 35000, "or": 40000,
    "our": 20000, "out": 20000, "people": 15000, "please": 5000, "said": 20000,
    "see": 12000, "she": 30000, "should": 15000, "some": 25000, "spell": 1000,
    "spelling": 2000, "student": 7000, "students": 10000, "such": 10000,
    "text": 7000, "than": 15000, "that": 65000, "the": 100000, "their": 35000,
    "them": 30000, "then": 25000, "there": 35000, "these": 20000, "they": 50000,
    "this": 60000, "time": 30000, "to": 90000, "two": 20000, "up": 25000,
    "use": 20000, "very": 25000, "was": 60000, "we": 45000, "were": 40000,
    "what": 35000, "when": 35000, "which": 30000, "who": 20000, "will": 45000,
    "with": 65000, "word": 10000, "work": 20000, "would": 35000, "write": 8000,
    "you": 75000, "your": 50000, "apple": 1000, "book": 5000, "car": 5000,
    "cat": 2000, "dog": 4000, "fast": 7000, "fox": 500, "lazy": 1000,
    "quick": 5000, "brown": 5000, "jump": 5000, "over": 30000,
    "student's": 1000, "sentence": 7000, "sentence's": 100,
    "run": 10000, "runs": 7000, "running": 10000, "walk": 7000, "walks": 5000,
    "eat": 8000, "eats": 5000, "ate": 7000, "go": 15000, "goes": 10000,
    "went": 18000, "study": 8000, "studies": 5000, "studied": 6000,
    "play": 9000, "plays": 6000, "played": 8000, "has": 35000, "had": 40000,
    "am": 25000, "isn't": 8000, "aren't": 8000, "wasn't": 6000,
    "were": 40000, "doesn't": 12000, "don't": 25000, "did": 30000,
    "beautiful": 7000, "beautifully": 3000, "interesting": 9000,
    "university": 8000, "computer": 12000, "science": 12000, "project": 10000,
    "today": 20000, "yesterday": 7000, "tomorrow": 8000, "morning": 10000,
    "analyze": 3000, "analysis": 5000, "correction": 2000, "language": 7000,
    # Common academic and everyday vocabulary for the offline baseline.
    "able": 8000, "above": 12000, "across": 10000, "activity": 5000,
    "actually": 8000, "add": 10000, "age": 12000, "again": 30000,
    "against": 15000, "air": 15000, "almost": 12000, "along": 15000,
    "already": 18000, "always": 25000, "among": 12000, "another": 30000,
    "any": 40000, "anything": 15000, "around": 35000, "ask": 20000,
    "back": 40000, "bad": 12000, "based": 18000, "because": 8000,
    "best": 20000, "better": 25000, "between": 30000, "both": 30000,
    "business": 20000, "call": 35000, "change": 30000, "child": 18000,
    "city": 25000, "class": 20000, "come": 50000, "common": 25000,
    "community": 14000, "company": 25000, "complete": 15000, "consider": 12000,
    "correct": 12000, "day": 8000, "different": 35000, "done": 7000,
    "during": 25000, "early": 30000, "education": 20000, "end": 30000,
    "enough": 25000, "even": 45000, "every": 40000, "everything": 15000,
    "example": 3000, "experience": 30000, "fact": 25000, "family": 30000,
    "few": 35000, "find": 40000, "first": 60000, "follow": 20000,
    "form": 30000, "found": 35000, "four": 25000, "friend": 25000,
    "general": 25000, "give": 40000, "going": 35000, "great": 35000,
    "group": 30000, "hand": 35000, "help": 40000, "high": 50000,
    "home": 50000, "house": 35000, "however": 30000, "important": 35000,
    "information": 35000, "interest": 20000, "keep": 35000, "kind": 30000,
    "know": 60000, "large": 35000, "last": 45000, "learn": 25000,
    "learning": 22000, "left": 45000, "less": 35000, "life": 50000,
    "line": 45000, "little": 45000, "long": 60000, "look": 60000,
    "love": 45000, "man": 60000, "machine": 12000, "might": 35000,
    "most": 60000, "move": 30000, "much": 60000, "must": 50000,
    "name": 50000, "never": 50000, "next": 50000, "number": 50000,
    "often": 35000, "old": 50000, "only": 70000, "other": 75000,
    "own": 50000, "part": 60000, "place": 55000, "point": 55000,
    "problem": 35000, "program": 30000, "question": 35000, "read": 50000,
    "really": 55000, "right": 80000, "room": 50000, "same": 70000,
    "school": 60000, "science": 12000, "small": 50000, "something": 60000,
    "still": 70000, "study": 8000, "system": 50000, "tell": 55000,
    "thing": 80000, "think": 80000, "through": 70000, "under": 60000,
    "until": 50000, "while": 75000, "without": 55000, "woman": 50000,
    "world": 80000, "young": 45000, "student": 7000, "students": 10000,
    "project": 10000, "technology": 25000, "computer": 12000, "software": 12000,
    "data": 30000, "model": 35000, "method": 15000, "algorithm": 10000,
    "algorithms": 9000, "natural": 25000, "processing": 22000,
    "intelligent": 10000, "engine": 25000, "built": 50000, "using": 60000,
    "based": 18000, "custom": 10000, "frequency": 8000, "context": 25000,
    "grammar": 1000, "suggestion": 8000, "suggestions": 10000,
    "enjoy": 18000, "complex": 25000, "remain": 25000, "happy": 30000,
    "tired": 18000, "open": 25000, "nearby": 10000, "honest": 12000,
    "answer": 45000, "matter": 40000, "meet": 40000,
    "decide": 30000, "decided": 35000, "break": 30000, "broke": 30000,
    "hour": 45000, "other": 75000, "mother": 45000, "photograph": 25000,
    "photographs": 28000, "photo": 40000, "photos": 40000, "take": 60000,
    "took": 50000, "repair": 12000, "repaired": 15000, "car": 5000,
}


def minimum_edit_distance(source: str, target: str) -> int:
    """Return Levenshtein distance using a memory-efficient dynamic program."""
    if len(source) < len(target):
        source, target = target, source
    previous = list(range(len(target) + 1))
    for i, left in enumerate(source, 1):
        current = [i]
        for j, right in enumerate(target, 1):
            current.append(min(
                current[-1] + 1,             # insertion
                previous[j] + 1,             # deletion
                previous[j - 1] + (left != right),  # substitution
            ))
        previous = current
    return previous[-1]


@lru_cache(maxsize=1)
def get_frequencies():
    frequencies = Counter(BASE_FREQUENCIES)
    try:
        from nltk.corpus import words
        for word in words.words():
            word = word.lower()
            if word.isalpha():
                frequencies.setdefault(word, 1)
    except (ImportError, LookupError):
        pass
    return frequencies


def known(word: str) -> bool:
    word = word.lower()
    freq = get_frequencies()
    if word in freq:
        return True
    # Conservative morphology reduces false alarms on common inflections.
    if word.endswith("ies") and word[:-3] + "y" in freq:
        return True
    for suffix in ("ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) > len(suffix) + 2:
            stem = word[:-len(suffix)]
            if stem in freq or (stem.endswith(stem[-1:]) and stem[:-1] in freq):
                return True
            if suffix == "ed" and (stem + "e") in freq:
                return True
    return False


@lru_cache(maxsize=1)
def _words_by_length():
    buckets = {}
    for candidate in get_frequencies():
        buckets.setdefault(len(candidate), []).append(candidate)
    return buckets


def candidates(word: str, limit: int = 5):
    """Rank dictionary candidates by distance then corpus frequency."""
    word = word.lower()
    freq = get_frequencies()
    max_distance = 1 if len(word) <= 5 else 3 if len(word) >= 10 else 2
    scored = []
    buckets = _words_by_length()
    for length in range(max(1, len(word) - max_distance), len(word) + max_distance + 1):
        for candidate in buckets.get(length, ()):
            distance = minimum_edit_distance(word, candidate)
            if 0 < distance <= max_distance:
                scored.append((distance, -freq[candidate], candidate))
    scored.sort()
    return [item[2] for item in scored[:limit]]


@lru_cache(maxsize=1)
def _ngram_counts():
    """Build local bigram/trigram counts from a tiny transparent sample corpus."""
    corpus = [
        "she is a student", "he is a student", "they are students", "we are students",
        "an apple is on the table", "a book is on the table", "the cat is quick",
        "the dog is brown", "i went to school yesterday", "i walked to school yesterday",
        "students study english", "students use computers", "grammar correction engine",
        "natural language processing", "the language model uses word frequency",
        "a sentence has a subject and a verb", "the subject agrees with the verb",
        "the quick brown fox jumps over the lazy dog", "we can meet tomorrow",
    ]
    bigrams, trigrams = Counter(), Counter()
    for line in corpus:
        words = ["<s>", *re.findall(r"[a-z]+", line), "</s>"]
        bigrams.update(zip(words, words[1:]))
        trigrams.update(zip(words, words[1:], words[2:]))
    return bigrams, trigrams


def _best_context_candidate(word: str, previous_word: str, next_word: str, before_previous: str = ""):
    """Rank plausible edits using edit cost, local frequency, then n-gram context."""
    options = candidates(word, 8)
    if not options:
        return None
    bigrams, trigrams = _ngram_counts()
    freq = get_frequencies()
    def rank(candidate):
        contextual = bigrams.get((previous_word, candidate), 0) + bigrams.get((candidate, next_word), 0)
        contextual += 2 * trigrams.get((before_previous, previous_word, candidate), 0)
        return (-minimum_edit_distance(word, candidate), contextual, freq[candidate])
    return max(options, key=rank)


def check_spelling(text: str):
    """Return misspelling records and a corrected string preserving casing."""
    issues = []
    pattern = re.compile(r"\b[A-Za-z]+(?:'[A-Za-z]+)?\b")
    tokens = list(pattern.finditer(text))
    for index, match in enumerate(tokens):
        token = match.group()
        lower = token.lower()
        if known(lower) or len(lower) < 2:
            continue
        prev_word = tokens[index - 1].group().lower() if index else ""
        next_word = tokens[index + 1].group().lower() if index + 1 < len(tokens) else ""
        before_previous = tokens[index - 2].group().lower() if index > 1 else "<s>"
        suggestion = _best_context_candidate(lower, prev_word, next_word, before_previous)
        if suggestion:
            if token.isupper():
                suggestion = suggestion.upper()
            elif token[0].isupper():
                suggestion = suggestion.capitalize()
        issues.append({
            "type": "spelling", "category": "spelling", "word": token, "original_text": token, "suggestion": suggestion,
            "suggestions": [suggestion] if suggestion else [], "confidence": 0.86 if suggestion else 0.35,
            "severity": "moderate",
            "start": match.start(), "end": match.end(),
            "explanation": (f'“{token}” is not in the available dictionary. ' +
                           (f'Try “{suggestion}”, selected by edit distance and word frequency.' if suggestion else "No close dictionary match was found.")),
        })
    corrected = text
    for issue in reversed(issues):
        if issue["suggestion"]:
            corrected = corrected[:issue["start"]] + issue["suggestion"] + corrected[issue["end"]:]
    return issues, corrected
