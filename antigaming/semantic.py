"""
Semantic trap scoring for four open-ended questions.
Real operators answer specifically with named entities, numbers, and
operational details. Vague answers signal a performed rather than
experienced response.

Scoring is heuristic-based — no ML model required for initial deployment.
A future version can replace this module with a fine-tuned classifier
trained on pilot responses.
"""
import re
from dataclasses import dataclass


@dataclass
class SemanticScore:
    question_id: str
    raw_score: int       # 0–100
    named_entities: int
    numeric_anchors: int
    operational_verbs: int
    coherence_score: int


OPERATIONAL_VERBS = {
    "renegotiated", "shifted", "closed", "opened", "hired", "fired",
    "moved", "bought", "sold", "reduced", "increased", "negotiated",
    "switched", "stopped", "started", "delivered", "installed", "repaired",
    "contacted", "paid", "borrowed", "saved", "invested", "lost", "gained",
}

VAGUE_FILLER = {
    "good service", "quality products", "fair prices", "competitive",
    "very difficult", "challenging", "hard time", "many customers",
    "loyal customers", "often", "sometimes", "generally", "usually",
}


def score_semantic_answer(question_id: str, answer: str) -> SemanticScore:
    """
    Scores a single free-text answer on four dimensions, returns 0–100.
    """
    if not answer or len(answer.strip()) < 20:
        return SemanticScore(question_id, 0, 0, 0, 0, 0)

    text = answer.lower()

    # 1. Named entities: capitalized words or proper nouns in original answer
    named = len(re.findall(r"\b[A-Z][a-z]{1,}\b", answer))
    named_score = min(named * 20, 40)  # cap at 40 pts

    # 2. Numeric anchors: any number, amount, percentage, date
    numbers = re.findall(r"\b\d+[\.,]?\d*\b|\b\d+%\b", text)
    numeric_score = min(len(numbers) * 10, 30)  # cap at 30 pts

    # 3. Operational verbs: action words describing what was actually done
    words = set(text.split())
    ops_found = words.intersection(OPERATIONAL_VERBS)
    ops_score = min(len(ops_found) * 10, 20)  # cap at 20 pts

    # 4. Coherence penalty: generic filler phrases reduce score
    filler_found = sum(1 for phrase in VAGUE_FILLER if phrase in text)
    coherence_penalty = min(filler_found * 10, 30)

    raw = named_score + numeric_score + ops_score - coherence_penalty
    raw = max(0, min(100, raw))

    return SemanticScore(
        question_id=question_id,
        raw_score=raw,
        named_entities=named,
        numeric_anchors=len(numbers),
        operational_verbs=len(ops_found),
        coherence_score=max(0, 30 - coherence_penalty),
    )


def score_all_semantic_answers(assessment) -> dict:
    """
    Scores all four semantic trap answers and returns a summary dict.
    These scores are informational — they reduce individual sub-scores
    within their relevant pillar rather than applying a multiplier penalty.
    """
    results = {}

    questions = {
        "challenge": assessment.semantic_challenge_answer,
        "covid": assessment.semantic_covid_answer,
        "customer": assessment.semantic_customer_answer,
        "advantage": assessment.semantic_advantage_answer,
    }

    for q_id, answer in questions.items():
        results[q_id] = score_semantic_answer(q_id, answer)

    # Overall semantic credibility: average across all four
    avg = sum(s.raw_score for s in results.values()) / len(results)
    results["overall_credibility"] = round(avg, 1)

    return results