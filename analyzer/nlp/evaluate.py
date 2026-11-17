"""Small deterministic regression set; metrics are descriptive, not corpus-wide claims."""
import time
from .grammar import check_grammar
from .spelling import check_spelling

CASES = [
    ("The quick brown fox jumps over the lazy dog.", False),
    ("I enjoy reading books every morning.", False),
    ("She are happy today.", True),
    ("They is ready now.", True),
    ("It is a apple.", True),
    ("Yesterday I go to school.", True),
    ("The students studies English.", True),  # Deliberately unsupported plural verb case.
    ("Your welcome to join us.", True),
    ("There going to the library.", True),
    ("We discussed about the project.", True),
    ("Many book are on the table.", True),
    ("I recieved the letter yesterday.", True),
    ("This is a complex sentence, and it remains correct.", False),
    ("She was happy, but they were tired.", False),
    ("I went there yesterday.", False),
    ("The analysis uses a custom language model.", False),
    ("He has been working all day.", False),
    ("A university opened nearby.", False),
    ("An honest answer matters.", False),
    ("We can meet tomorrow.", False),
]


def evaluate():
    tp = fp = fn = exact = 0
    start = time.perf_counter()
    for text, expected_error in CASES:
        spelling, corrected = check_spelling(text)
        grammar = check_grammar(corrected)
        detected = bool(spelling or grammar)
        tp += int(detected and expected_error)
        fp += int(detected and not expected_error)
        fn += int(not detected and expected_error)
        exact += int(detected == expected_error)
    elapsed = time.perf_counter() - start
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {"cases": len(CASES), "tp": tp, "fp": fp, "fn": fn,
            "precision": precision, "recall": recall,
            "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
            "false_positive_rate": fp / sum(not expected for _, expected in CASES),
            "classification_accuracy": exact, "avg_latency_ms": elapsed * 1000 / len(CASES)}


if __name__ == "__main__":
    print(evaluate())
