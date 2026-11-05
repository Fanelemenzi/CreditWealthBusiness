import json
import hashlib
import math
from decimal import Decimal
from typing import List

from antigaming.rules import FraudFlagResult


class BehavioralSignalMiddleware:
    """
    Django middleware that records timing and revision metadata
    for assessment API endpoints. Data is stored in BehavioralSignal.
    """

    ASSESSMENT_PATH_PREFIX = "/api/assessments/"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        import time
        request._start_time = time.time()
        response = self.get_response(request)

        if self._is_assessment_answer_endpoint(request):
            self._record_signals(request, response)

        return response

    def _is_assessment_answer_endpoint(self, request) -> bool:
        return (
            request.path.startswith(self.ASSESSMENT_PATH_PREFIX)
            and request.method in ("POST", "PATCH")
        )

    def _record_signals(self, request, response):
        """
        On each answer submission, update the BehavioralSignal record:
        - log time taken for this question
        - increment revision counter if the answer was previously set
        """
        import time
        from assessments.models import BehavioralSignal

        if response.status_code not in (200, 201):
            return

        try:
            body = json.loads(request.body)
            assessment_id = self._extract_assessment_id(request)
            if not assessment_id:
                return

            signal, _ = BehavioralSignal.objects.get_or_create(
                assessment_id=assessment_id
            )

            elapsed = time.time() - getattr(request, "_start_time", time.time())

            for question_id, answer in body.items():
                if question_id.startswith("_"):
                    continue

                timings = signal.question_timings
                timings[question_id] = elapsed
                signal.question_timings = timings

                revisions = signal.revision_counts
                if question_id in revisions:
                    revisions[question_id] = revisions[question_id] + 1
                else:
                    revisions[question_id] = 0
                signal.revision_counts = revisions

            # Device fingerprint
            if not signal.device_fingerprint:
                signal.device_fingerprint = self._fingerprint(request)

            signal.ip_address = self._get_client_ip(request)
            signal.user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]
            signal.save()

        except Exception:
            pass  # behavioral collection is non-critical; never raise

    @staticmethod
    def _extract_assessment_id(request) -> str:
        parts = request.path.strip("/").split("/")
        try:
            idx = parts.index("assessments")
            return parts[idx + 1]
        except (ValueError, IndexError):
            return ""

    @staticmethod
    def _fingerprint(request) -> str:
        raw = "|".join([
            request.META.get("HTTP_USER_AGENT", ""),
            request.META.get("HTTP_ACCEPT_LANGUAGE", ""),
            request.META.get("HTTP_ACCEPT_ENCODING", ""),
        ])
        return hashlib.sha256(raw.encode()).hexdigest()[:64]

    @staticmethod
    def _get_client_ip(request) -> str:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")


class BehavioralRuleChecker:
    """
    Evaluates behavioral signals against two anti-gaming rules.
    Called by FraudDetectionEngine after cross-pillar rules.
    """

    # Financial question IDs that should take >3s for a real answer
    FINANCIAL_QUESTION_IDS = {
        "revenue_bracket",
        "profit_margin_pct",
        "debt_status",
        "debt_to_income_pct",
        "emergency_buffer_months",
        "monthly_revenue",
    }

    SPEED_THRESHOLD_SECONDS = 3.0
    SPEED_TRIGGER_COUNT = 3
    REVISION_THRESHOLD = 3
    REVISION_TRIGGER_COUNT = 2

    def __init__(self, behavioral_signal):
        self.signal = behavioral_signal

    def run(self) -> List[FraudFlagResult]:
        results = []
        r1 = self._check_speed()
        r2 = self._check_revisions()
        if r1:
            results.append(r1)
        if r2:
            results.append(r2)
        return results

    def _check_speed(self):
        """
        BEH_SPEED_001 — Low
        3 or more financial questions answered in under 3 seconds.
        Real business owners need time to recall financial figures.
        """
        fast_answers = sum(
            1
            for qid, elapsed in self.signal.question_timings.items()
            if qid in self.FINANCIAL_QUESTION_IDS
            and elapsed < self.SPEED_THRESHOLD_SECONDS
        )

        if fast_answers >= self.SPEED_TRIGGER_COUNT:
            return FraudFlagResult(
                rule_id="BEH_SPEED_001",
                severity="low",
                penalty_pct=Decimal("2.00"),
                description=(
                    f"{fast_answers} financial questions answered in under "
                    f"{self.SPEED_THRESHOLD_SECONDS}s. Real owners typically "
                    "take longer to recall financial figures from memory."
                ),
                pillars_involved="Behavioral",
            )
        return None

    def _check_revisions(self):
        """
        BEH_REVISE_001 — Medium
        2 or more financial answers revised 3+ times.
        Excessive revision suggests testing answer combinations.
        """
        heavily_revised = sum(
            1
            for qid, count in self.signal.revision_counts.items()
            if qid in self.FINANCIAL_QUESTION_IDS
            and count >= self.REVISION_THRESHOLD
        )

        if heavily_revised >= self.REVISION_TRIGGER_COUNT:
            return FraudFlagResult(
                rule_id="BEH_REVISE_001",
                severity="medium",
                penalty_pct=Decimal("5.00"),
                description=(
                    f"{heavily_revised} financial answers revised "
                    f"{self.REVISION_THRESHOLD}+ times each. Pattern suggests "
                    "the applicant was testing answer combinations rather than "
                    "reporting known figures."
                ),
                pillars_involved="Behavioral",
            )
        return None


def calculate_gps_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Haversine formula — returns distance in km between two GPS coordinates.
    Used to compare declared business location against session GPS.
    """
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))