"""
ATS scoring service.

Uses TF-IDF + cosine similarity (scikit-learn) to score a resume
against a job description. Returns a float between 0.0 and 1.0.
No GPU or heavy models required.
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def score_resume(resume_text: str, job_description: str) -> float:
    """
    Compute ATS match score between resume text and job description.

    Returns a float 0.0–1.0 (higher = better match).
    """
    if not resume_text or not job_description:
        return 0.0

    corpus = [resume_text.lower(), job_description.lower()]
    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),   # unigrams + bigrams for better skill matching
            max_features=10_000,
        )
        tfidf_matrix = vectorizer.fit_transform(corpus)
        score = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
    except Exception:
        score = 0.0

    return round(score, 4)
