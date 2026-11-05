from rest_framework import serializers
from assessments.models import Assessment, FraudFlag, SocialReference
from accounts.models import BusinessOwner


class SocialReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialReference
        fields = ["id", "name", "phone", "relationship", "is_family"]
        read_only_fields = ["id"]

    def validate(self, data):
        if data.get("is_family"):
            raise serializers.ValidationError(
                "Family references are not accepted. "
                "Please provide two non-family references."
            )
        return data


class AssessmentCreateSerializer(serializers.ModelSerializer):
    social_references = SocialReferenceSerializer(many=True, write_only=True)

    class Meta:
        model = Assessment
        fields = [
            "id",
            "pillar_1_data",
            "pillar_2_data",
            "pillar_3_data",
            "pillar_4_data",
            "pillar_5_data",
            "pillar_6_data",
            "semantic_challenge_answer",
            "semantic_covid_answer",
            "semantic_customer_answer",
            "semantic_advantage_answer",
            "social_references",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        references_data = validated_data.pop("social_references", [])
        assessment = Assessment.objects.create(**validated_data)

        for ref_data in references_data:
            SocialReference.objects.create(assessment=assessment, **ref_data)

        return assessment

    def validate_pillar_5_data(self, value):
        """
        If stokvel membership is claimed, coordinator phone is required
        for the social verification layer.
        """
        if value.get("stokvel_status") == "active_regular":
            if not value.get("stokvel_coordinator_phone"):
                raise serializers.ValidationError(
                    "Stokvel coordinator phone is required when active "
                    "membership is claimed."
                )
        return value


class FraudFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = FraudFlag
        fields = ["rule_id", "severity", "penalty_pct", "pillars_involved", "created_at"]


class AssessmentResultSerializer(serializers.ModelSerializer):
    """
    Returned to the applicant after scoring.
    Fraud flags are NEVER included in this serializer.
    The applicant sees only their scores and tier.
    """
    improvement_tips = serializers.SerializerMethodField()
    approved_loan_max = serializers.ReadOnlyField()

    class Meta:
        model = Assessment
        fields = [
            "id",
            "status",
            "final_bvss",
            "risk_tier",
            "score_p1",
            "score_p2",
            "score_p3",
            "score_p4",
            "score_p5",
            "score_p6",
            "approved_loan_max",
            "expires_at",
            "improvement_tips",
            "requires_manual_review",
        ]

    def get_improvement_tips(self, obj) -> list:
        """
        Returns the two lowest-scoring pillars with actionable improvement advice.
        """
        pillar_scores = {
            "Owner character (P1)": float(obj.score_p1 or 0),
            "Financial performance (P2)": float(obj.score_p2 or 0),
            "Business maturity (P3)": float(obj.score_p3 or 0),
            "Market position (P4)": float(obj.score_p4 or 0),
            "Social capital (P5)": float(obj.score_p5 or 0),
            "Repayment capacity (P6)": float(obj.score_p6 or 0),
        }
        sorted_pillars = sorted(pillar_scores.items(), key=lambda x: x[1])
        tips = []
        advice_map = {
            "Owner character (P1)": "Complete a formal business training course and ensure your references are ready to verify your reliability.",
            "Financial performance (P2)": "Link your MoMo account and document your monthly revenues consistently for 3 months.",
            "Business maturity (P3)": "Move to a fixed business location and start keeping a written cashbook.",
            "Market position (P4)": "Identify a clear customer need only your business meets, and add at least one additional revenue stream.",
            "Social capital (P5)": "Join a registered stokvel or traders' association and secure two contactable non-family guarantors.",
            "Repayment capacity (P6)": "Reduce existing debt below 20% of monthly revenue and build a 1-month cash buffer.",
        }
        for pillar, score in sorted_pillars[:2]:
            tips.append({
                "pillar": pillar,
                "current_score": round(score, 1),
                "advice": advice_map.get(pillar, ""),
            })
        return tips