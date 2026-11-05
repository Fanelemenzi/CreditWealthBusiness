from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.shortcuts import get_object_or_404

from assessments.models import Assessment
from assessments.serializers import (
    AssessmentCreateSerializer,
    AssessmentResultSerializer,
)


class AssessmentSubmitView(generics.CreateAPIView):
    """
    POST /api/assessments/submit/
    Creates the assessment, attaches it to the authenticated owner,
    and dispatches the async scoring pipeline.
    """
    serializer_class = AssessmentCreateSerializer

    def perform_create(self, serializer):
        assessment = serializer.save(
            owner=self.request.user,
            status=Assessment.Status.SUBMITTED,
            submitted_at=timezone.now(),
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {"message": "Assessment submitted. Scoring in progress."},
            status=status.HTTP_202_ACCEPTED,
        )


class AssessmentListView(generics.ListAPIView):
    serializer_class = AssessmentResultSerializer

    def get_queryset(self):
        return Assessment.objects.filter(owner=self.request.user)


class AssessmentResultView(generics.RetrieveAPIView):
    """
    GET /api/assessments/{id}/result/
    Returns the final BVSS and tier once scoring is complete.
    """
    serializer_class = AssessmentResultSerializer

    def get_object(self):
        return get_object_or_404(
            Assessment,
            id=self.kwargs["pk"],
            owner=self.request.user,
        )

    def retrieve(self, request, *args, **kwargs):
        assessment = self.get_object()
        if assessment.status not in (
            Assessment.Status.COMPLETE, Assessment.Status.VERIFIED
        ):
            return Response(
                {
                    "status": assessment.status,
                    "message": "Scoring is still in progress. Check back shortly.",
                },
                status=status.HTTP_202_ACCEPTED,
            )
        return super().retrieve(request, *args, **kwargs)


class SMSWebhookView(APIView):
    """
    POST /api/verification/sms-webhook/
    Africa's Talking inbound SMS webhook.
    Matches token to reference, parses scores, updates verification status.
    """
    permission_classes = []  # AT signs requests; verify via IP allowlist in production

    def post(self, request):
        from assessments.models import SocialReference
        from verification.sms import parse_reference_reply, score_from_reference_replies
        from verification.models import SMSWebhookLog

        from_number = request.data.get("from", "")
        body = request.data.get("text", "")

        SMSWebhookLog.objects.create(from_number=from_number, body=body)

        # Extract token (8-char uppercase sequence)
        import re
        token_match = re.search(r"\b([A-Z0-9]{8})\b", body.upper())
        if not token_match:
            return Response({"status": "no_token"}, status=200)

        token = token_match.group(1)

        try:
            ref = SocialReference.objects.get(verification_token=token)
        except SocialReference.DoesNotExist:
            return Response({"status": "unknown_token"}, status=200)

        scores = parse_reference_reply(body)
        if scores:
            composite = score_from_reference_replies(
                scores["q1"], scores["q2"], scores["q3"]
            )
            ref.q1_reliability_score = scores["q1"] * 20
            ref.q2_financial_score = scores["q2"] * 20
            ref.q3_duration_score = scores["q3"] * 20
            ref.composite_trust_score = composite
            ref.verification_status = SocialReference.VerificationStatus.RESPONDED
            ref.responded_at = timezone.now()
            ref.save()

            SMSWebhookLog.objects.filter(
                from_number=from_number, body=body
            ).update(token_found=token, processed=True)

        return Response({"status": "processed"}, status=200)