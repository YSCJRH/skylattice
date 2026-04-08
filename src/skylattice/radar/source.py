"""GitHub-backed discovery for the technology radar."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Iterable
import uuid

from skylattice.actions import GitHubAdapter

from .models import RadarCandidate, RadarCandidateStatus, RadarDecision, RadarEvidence


class GitHubRadarSource:
    def __init__(self, github: GitHubAdapter, *, now: datetime | None = None) -> None:
        self.github = github
        self.now = now or datetime.now(UTC)

    def discover(
        self,
        *,
        run_id: str,
        topics: Iterable[str],
        created_days: int,
        active_days: int,
        limit: int,
    ) -> tuple[list[RadarCandidate], list[RadarEvidence]]:
        per_query = max(5, min(limit, max(limit // max(len(tuple(topics)) * 2, 1), 1)))
        discovered: dict[str, RadarCandidate] = {}
        evidence: list[RadarEvidence] = []
        created_cutoff = (self.now - timedelta(days=created_days)).date().isoformat()
        active_cutoff = (self.now - timedelta(days=active_days)).date().isoformat()

        for topic in topics:
            queries = (
                (f"topic:{topic} created:>={created_cutoff} archived:false fork:false mirror:false", "stars"),
                (f"topic:{topic} pushed:>={active_cutoff} archived:false fork:false mirror:false", "updated"),
            )
            for query, sort in queries:
                for item in self.github.search_repositories(query=query, sort=sort, per_page=per_query):
                    repo_slug = str(item.get("full_name", ""))
                    if not repo_slug:
                        continue
                    candidate = discovered.get(repo_slug)
                    if candidate is None:
                        candidate = self._candidate_from_search(run_id=run_id, item=item, matched_topic=topic)
                    else:
                        merged_topics = tuple(sorted({*candidate.topics, topic.lower(), *self._extract_topics(item)}))
                        metadata = dict(candidate.metadata)
                        matched_terms = sorted({*metadata.get("matched_topics", []), topic.lower()})
                        metadata["matched_topics"] = matched_terms
                        candidate = replace(candidate, topics=merged_topics, metadata=metadata)
                    discovered[repo_slug] = candidate
                    evidence.append(
                        RadarEvidence(
                            evidence_id=f"evidence-{uuid.uuid4().hex}",
                            run_id=run_id,
                            candidate_id=discovered[repo_slug].candidate_id,
                            evidence_kind="search-result",
                            source=query,
                            summary=f"GitHub search matched {repo_slug} for topic '{topic}'",
                            payload={"sort": sort, "stars": int(item.get("stargazers_count", 0))},
                        )
                    )
                    if len(discovered) >= limit:
                        break
                if len(discovered) >= limit:
                    break
            if len(discovered) >= limit:
                break

        return list(discovered.values()), evidence

    def enrich_candidate(self, candidate: RadarCandidate) -> tuple[RadarCandidate, list[RadarEvidence]]:
        repo = self.github.get_repository(candidate.repo_slug)
        release = self.github.get_latest_release(candidate.repo_slug)
        topics = tuple(sorted({*candidate.topics, *self._extract_topics(repo)}))
        metadata = dict(candidate.metadata)
        metadata["language"] = repo.get("language")
        metadata["license"] = (repo.get("license") or {}).get("spdx_id") if isinstance(repo.get("license"), dict) else None
        enriched = replace(
            candidate,
            description=str(repo.get("description") or candidate.description),
            topics=topics,
            stars=int(repo.get("stargazers_count", candidate.stars)),
            forks=int(repo.get("forks_count", candidate.forks)),
            watchers=int(repo.get("subscribers_count", candidate.watchers)),
            created_at_remote=str(repo.get("created_at") or candidate.created_at_remote),
            pushed_at_remote=str(repo.get("pushed_at") or candidate.pushed_at_remote),
            latest_release_at=str(release.get("published_at")) if isinstance(release, dict) and release.get("published_at") else candidate.latest_release_at,
            metadata=metadata,
        )
        evidence = [
            RadarEvidence(
                evidence_id=f"evidence-{uuid.uuid4().hex}",
                run_id=candidate.run_id,
                candidate_id=candidate.candidate_id,
                evidence_kind="repository",
                source=f"repos/{candidate.repo_slug}",
                summary=f"Loaded repository metadata for {candidate.repo_slug}",
                payload={
                    "topics": list(topics),
                    "watchers": enriched.watchers,
                    "language": metadata.get("language"),
                },
            )
        ]
        if isinstance(release, dict):
            evidence.append(
                RadarEvidence(
                    evidence_id=f"evidence-{uuid.uuid4().hex}",
                    run_id=candidate.run_id,
                    candidate_id=candidate.candidate_id,
                    evidence_kind="release",
                    source=f"repos/{candidate.repo_slug}/releases/latest",
                    summary=f"Loaded latest release metadata for {candidate.repo_slug}",
                    payload={
                        "tag_name": release.get("tag_name"),
                        "published_at": release.get("published_at"),
                    },
                )
            )
        return enriched, evidence

    def _candidate_from_search(self, *, run_id: str, item: dict[str, object], matched_topic: str) -> RadarCandidate:
        return RadarCandidate(
            candidate_id=f"cand-{uuid.uuid4().hex}",
            run_id=run_id,
            repo_slug=str(item.get("full_name", "")),
            repo_name=str(item.get("name", "")),
            html_url=str(item.get("html_url", "")),
            description=str(item.get("description") or ""),
            topics=tuple(sorted({matched_topic.lower(), *self._extract_topics(item)})),
            stars=int(item.get("stargazers_count", 0)),
            forks=int(item.get("forks_count", 0)),
            watchers=int(item.get("watchers_count", 0)),
            created_at_remote=str(item.get("created_at") or "") or None,
            pushed_at_remote=str(item.get("pushed_at") or "") or None,
            latest_release_at=None,
            score=0.0,
            score_breakdown={},
            decision=RadarDecision.OBSERVE,
            status=RadarCandidateStatus.DISCOVERED,
            reason="discovered from GitHub search",
            metadata={"matched_topics": [matched_topic.lower()]},
        )

    @staticmethod
    def _extract_topics(item: dict[str, object]) -> tuple[str, ...]:
        raw_topics = item.get("topics", [])
        if not isinstance(raw_topics, list):
            return ()
        return tuple(str(topic).lower() for topic in raw_topics if topic)
