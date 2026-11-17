"""Explainable grammar checks built from token patterns and hand-written rules."""
import re

SUBJECTS_SINGULAR = {"he", "she", "it", "this", "that", "each", "everyone", "somebody"}
SUBJECTS_PLURAL = {"they", "we", "you", "these", "those"}
IRREGULAR_PAST = {"go": "went", "eat": "ate", "see": "saw", "run": "ran", "write": "wrote", "come": "came", "take": "took", "break": "broke", "make": "made", "have": "had", "do": "did", "buy": "bought", "bring": "brought", "think": "thought", "teach": "taught", "catch": "caught", "feel": "felt", "leave": "left", "meet": "met", "say": "said", "find": "found", "give": "gave", "know": "knew", "speak": "spoke", "drive": "drove", "choose": "chose", "begin": "began", "drink": "drank", "sing": "sang", "swim": "swam", "fall": "fell", "forget": "forgot", "get": "got", "keep": "kept", "lose": "lost", "pay": "paid", "send": "sent", "sit": "sat", "stand": "stood", "understand": "understood"}
REGULAR_PAST = {"walk": "walked", "play": "played", "study": "studied", "work": "worked", "visit": "visited", "watch": "watched", "talk": "talked", "cook": "cooked", "open": "opened", "clean": "cleaned", "help": "helped", "call": "called", "live": "lived", "move": "moved", "arrive": "arrived", "decide": "decided", "repair": "repaired", "photograph": "photographed", "finish": "finished", "start": "started", "want": "wanted", "need": "needed", "ask": "asked", "answer": "answered", "use": "used", "change": "changed", "carry": "carried"}


def tokenize_words(text: str):
    """A simple regex word tokenizer that retains punctuation as separate tokens."""
    return re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?|[^\w\s]", text)


def tokenize_sentences(text: str):
    """Split on sentence-ending punctuation followed by whitespace or end."""
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip()]


def _add(issues, text, start, end, suggestion, explanation, rule):
    issues.append({"type": "grammar", "category": rule, "word": text[start:end], "original_text": text[start:end], "suggestion": suggestion,
                   "suggestions": [suggestion] if suggestion else [], "start": start, "end": end, "explanation": explanation, "rule": rule,
                   "confidence": 0.94, "severity": "moderate"})


def check_grammar(text: str):
    issues = []
    # Subject–verb agreement: a compact set of frequent present-tense patterns.
    for match in re.finditer(r"\b(he|she|it|this|that|everyone|each)\s+(are|were|have|do)\b", text, re.I):
        subject, verb = match.group(1), match.group(2)
        fix = {"are": "is", "were": "was", "have": "has", "do": "does"}[verb.lower()]
        if verb.isupper(): fix = fix.upper()
        elif verb[0].isupper(): fix = fix.capitalize()
        _add(issues, text, match.start(2), match.end(2), fix,
             f'The singular subject “{subject}” needs “{fix}” in the present/past agreement pattern.', "subject_verb_agreement")
    for match in re.finditer(r"\b(they|we|you|these|those)\s+(is|was|has|does)\b", text, re.I):
        subject, verb = match.group(1), match.group(2)
        fix = {"is": "are", "was": "were", "has": "have", "does": "do"}[verb.lower()]
        if verb.isupper(): fix = fix.upper()
        elif verb[0].isupper(): fix = fix.capitalize()
        _add(issues, text, match.start(2), match.end(2), fix,
             f'The subject “{subject}” takes “{fix}” in this agreement pattern.', "subject_verb_agreement")
    plural_verb_forms = {"studies": "study", "plays": "play", "runs": "run", "walks": "walk", "eats": "eat", "works": "work", "goes": "go", "has": "have", "does": "do"}
    for match in re.finditer(r"\b(students|people|children|dogs|cats|they|we)\s+(studies|plays|runs|walks|eats|works|goes|has|does)\b", text, re.I):
        subject, verb = match.group(1), match.group(2)
        fix = plural_verb_forms[verb.lower()]
        if verb.isupper(): fix = fix.upper()
        elif verb[0].isupper(): fix = fix.capitalize()
        _add(issues, text, match.start(2), match.end(2), fix,
             f'The plural subject “{subject}” takes the base verb form “{fix}”.', "subject_verb_agreement")

    # Common determiner error before a vowel sound (rule is deliberately lexical/simple).
    vowel_sound_words = {"apple", "orange", "elephant", "hour", "honest", "idea", "engine", "umbrella", "example", "egg", "answer"}
    for match in re.finditer(r"\b(a|an)\s+([A-Za-z]+)\b", text, re.I):
        article, noun = match.group(1), match.group(2)
        should_an = noun.lower() in vowel_sound_words or (noun[:1].lower() in "aeiou" and noun.lower() not in {"university", "user", "unit", "european"})
        wanted = "an" if should_an else "a"
        if article.lower() != wanted:
            fix = wanted.upper() if article.isupper() else wanted.capitalize() if article[0].isupper() else wanted
            _add(issues, text, match.start(1), match.end(1), fix,
                 f'Use “{fix}” before “{noun}” because its initial sound is ' + ("a vowel" if should_an else "a consonant") + ".", "article_usage")

    # Frequent past-time marker followed by a base-form verb.
    for match in re.finditer(r"\b(yesterday|last\s+(?:night|week|month|year)|ago)\s+(?:I\s+|we\s+|they\s+|he\s+|she\s+|it\s+)?([a-z]+)\b", text, re.I):
        verb = match.group(2)
        past = IRREGULAR_PAST.get(verb.lower()) or REGULAR_PAST.get(verb.lower())
        if past:
            if verb.isupper(): past = past.upper()
            elif verb[0].isupper(): past = past.capitalize()
            _add(issues, text, match.start(2), match.end(2), past,
                 f'“{match.group(1)}” signals past time, so the verb should use its past form (“{past}”).', "tense_consistency")

    # Double spaces and repeated punctuation: useful mechanical grammar checks.
    for match in re.finditer(r" {2,}", text):
        _add(issues, text, match.start(), match.end(), " ", "Use a single space between words.", "spacing")
    for match in re.finditer(r"([.!?])\1+", text):
        _add(issues, text, match.start(), match.end(), match.group(1), "Avoid repeating sentence-ending punctuation.", "punctuation")

    # Narrow collocation checks are safer than replacing prepositions globally.
    collocations = [
        (r"\bdiscuss\s+about\b", "discuss", "", "The verb “discuss” takes its topic directly; remove “about”.", "preposition_usage"),
        (r"\bdepend\s+of\b", "depend", "on", "The usual collocation is “depend on”.", "preposition_usage"),
        (r"\bmarried\s+with\b", "married", "to", "The standard collocation is “married to”.", "preposition_usage"),
    ]
    for pattern, verb, fix, explanation, rule in collocations:
        for match in re.finditer(pattern, text, re.I):
            start = match.start() + len(verb) + 1
            end = match.end()
            _add(issues, text, start, end, fix, explanation, rule)

    # Conventional verb + noun expression (avoid broad style rewrites).
    for match in re.finditer(r"\bmake\s+(photographs|photos|a\s+photograph)\b", text, re.I):
        replacement = match.group(1)
        fix = "take" if replacement.lower().startswith("a ") else "take"
        _add(issues, text, match.start(), match.start() + 4, fix,
             "The conventional English expression is “take photographs”.", "word_choice")

    # Clearly signaled homophone/context errors.
    for match in re.finditer(r"\b(their|there)\s+(going|is|are|was|were)\b", text, re.I):
        wrong = match.group(1)
        if wrong.lower() == "their":
            fix = "They're" if wrong[0].isupper() else "they're"
            _add(issues, text, match.start(1), match.end(1), fix,
                 "A verb follows here, so the contraction “they’re” (they are) fits; “their” shows possession.", "confused_words")
    for match in re.finditer(r"\b(your)\s+(welcome|right|wrong|late|early)\b", text, re.I):
        fix = "You're" if match.group(1)[0].isupper() else "you're"
        _add(issues, text, match.start(1), match.end(1), fix,
             "The following adjective needs “you’re” (you are); “your” shows possession.", "confused_words")

    # A constrained count noun pattern catches common number agreement mistakes.
    for match in re.finditer(r"\b(many|several|few)\s+([a-z]+)\b", text, re.I):
        noun = match.group(2)
        if not noun.lower().endswith("s") and noun.lower() not in {"people", "children", "men", "women"}:
            fix = noun + ("ies" if noun.lower().endswith("y") and len(noun) > 1 and noun[-2].lower() not in "aeiou" else "s")
            if noun.lower().endswith("y") and fix.endswith("ys"): fix = noun[:-1] + "ies"
            if noun[0].isupper(): fix = fix.capitalize()
            _add(issues, text, match.start(2), match.end(2), fix,
                 f'“{match.group(1)}” refers to more than one, so the count noun should be plural (“{fix}”).', "number_agreement")

    # Sentence initial capitalization, excluding lower case after abbreviations is a known limitation.
    for match in re.finditer(r"(?:^|(?<=[.!?])\s+)([a-z])", text):
        _add(issues, text, match.start(1), match.end(1), match.group(1).upper(),
             "Capitalize the first letter of a sentence.", "capitalization")

    for issue in issues:
        if issue["rule"] in {"punctuation", "spacing", "capitalization"}:
            issue["severity"] = "minor"
        elif issue["rule"] in {"subject_verb_agreement", "tense_consistency", "number_agreement", "confused_words"}:
            issue["severity"] = "critical" if issue["rule"] == "confused_words" else "moderate"
    return sorted(issues, key=lambda item: item["start"])


def pos_tag_tokens(text: str):
    """Use NLTK's tagger when present; fall back to a transparent rule tagger."""
    words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?|[^\w\s]", text)
    try:
        import nltk
        try:
            return nltk.pos_tag(words)
        except LookupError:
            pass
    except ImportError:
        pass
    tags = []
    for word in words:
        w = word.lower()
        if re.fullmatch(r"[^\w\s]", word): tag = "."
        elif w in {"a", "an", "the"}: tag = "DT"
        elif w in {"he", "she", "it", "they", "we", "you", "i"}: tag = "PRP"
        elif w in {"is", "are", "was", "were", "be", "am", "has", "have", "do", "does"} or w.endswith("ed"): tag = "VB"
        elif w.endswith("ly"): tag = "RB"
        elif w.endswith(("ous", "ful", "ive", "able", "al")): tag = "JJ"
        elif w.endswith("s"): tag = "NNS"
        else: tag = "NN"
        tags.append((word, tag))
    return tags
