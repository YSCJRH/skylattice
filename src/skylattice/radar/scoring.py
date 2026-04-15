"""Candidate scoring for the technology radar."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Iterable

from .config import AdoptionRecord, RadarScoringConfig
from .models import RadarCandidate, RadarDecision


@dataclass(frozen=True)
class RadarScore:
    total: float
    breakdown: dict[str, float]
    decision: RadarDecision
    reason: str


class RadarScorer:
    def __init__(
        self,
        config: RadarScoringConfig,
        *,
        adoption_records: Iterable[AdoptionRecord] = (),
        now: datetime | None = None,
    ) -> None:
        self.config = config
        self.adoption_records = tuple(adoption_records)
        self.now = now or datetime.now(UTC)

    def score(self, candidate: RadarCandidate, *, active_days: int, created_days: int) -> RadarScore:
        topics = {item.lower() for item in candidate.topics}
        weights = self.config.weights
        star_score = min(candidate.stars / max(self.config.star_reference, 1), 1.0)
        activity_score = self._recency_score(candidate.pushed_at_remote, active_days)
        novelty_score = self._recency_score(candidate.created_at_remote, created_days)
        topicality_score = self._topic_overlap(topics, self.config.capability_gaps)
        release_score = self._recency_score(candidate.latest_release_at, self.config.release_days)
        gap_score = self._topic_overlap(topics, self.config.capability_gaps)
        adoption_boost = self._adoption_boost(candidate, topics)

        total = (
            weights.get("stars", 0.0) * star_score
            + weights.get("activity", 0.0) * activity_score
            + weights.get("novelty", 0.0) * novelty_score
            + weights.get("topicality", 0.0) * topicality_score
            + weights.get("release", 0.0) * release_score
            + weights.get("gap", 0.0) * gap_score
            + adoption_boost
        )
        total = round(min(total, 1.0), 4)
        breakdown = {
            "stars": round(star_score, 4),
            "activity": round(activity_score, 4),
            "novelty": round(novelty_score, 4),
            "topicality": round(topicality_score, 4),
            "release": round(release_score, 4),
            "gap": round(gap_score, 4),
            "adoption_boost": round(adoption_boost, 4),
        }

        promote_threshold = self.config.thresholds.get("promote", 0.72)
        experiment_threshold = self.config.thresholds.get("experiment", 0.60)
        shortlist_threshold = self.config.thresholds.get("shortlist", 0.45)
        if total >= promote_threshold:
            decision = RadarDecision.PROMOTE
            reason = "candidate clears automatic promotion threshold"
        elif total >= experiment_threshold:
            decision = RadarDecision.EXPERIMENT
            reason = "candidate is strong enough for a repo-contained spike"
        elif total >= shortlist_threshold:
            decision = RadarDecision.OBSERVE
            reason = "candidate merits semantic capture but not promotion"
        else:
            decision = RadarDecision.REJECT
            reason = "candidate is below the shortlist threshold"
        return RadarScore(total=total, breakdown=breakdown, decision=decision, reason=reason)

    def _adoption_boost(self, candidate: RadarCandidate, topics: set[str]) -> float:
        boost = 0.0
        for record in self.adoption_records:
            if (
                record.source_provider
                and record.source_handle
                and record.source_provider.lower() == candidate.source_provider.lower()
                and record.source_handle.lower() == candidate.identity_handle.lower()
            ):
                boost += record.preference_boost
                continue
            if record.repo_slug and record.repo_slug.lower() == candidate.repo_slug.lower():
                boost += record.preference_boost
                continue
            overlap = topics.intersection({item.lower() for item in record.tags})
            if overlap:
                boost += min(record.preference_boost, 0.05 * len(overlap))
        return min(boost, 0.15)

    @staticmethod
    def _topic_overlap(topics: set[str], targets: Iterable[str]) -> float:
        target_set = {item.lower() for item in targets}
        if not target_set:
            return 0.0
        overlap = len(topics.intersection(target_set))
        return overlap / len(target_set)

    def _recency_score(self, value: str | None, window_days: int) -> float:
        if not value or window_days <= 0:
            return 0.0
        created_at = _parse_datetime(value)
        if created_at is None:
            return 0.0
        age_days = max((self.now - created_at).days, 0)
        if age_days >= window_days:
            return 0.0
        return round(1 - (age_days / window_days), 4)


def _parse_datetime(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None
