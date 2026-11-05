from django.contrib import admin
from django.utils.html import format_html
from assessments.models import Assessment, FraudFlag, BehavioralSignal, SocialReference


class FraudFlagInline(admin.TabularInline):
    model = FraudFlag
    extra = 0
    readonly_fields = ["rule_id", "severity", "penalty_pct", "description", "pillars_involved", "created_at"]
    can_delete = False


class SocialReferenceInline(admin.TabularInline):
    model = SocialReference
    extra = 0
    readonly_fields = [
        "name", "phone", "relationship", "is_family",
        "verification_status", "composite_trust_score",
    ]
    can_delete = False


class BehavioralSignalInline(admin.StackedInline):
    model = BehavioralSignal
    extra = 0
    readonly_fields = [
        "question_timings", "revision_counts",
        "gps_distance_km", "device_fingerprint", "ip_address",
    ]
    can_delete = False


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = [
        "id", "owner", "status", "final_bvss_display",
        "risk_tier", "flag_count", "requires_manual_review", "submitted_at",
    ]
    list_filter = ["status", "risk_tier", "requires_manual_review"]
    search_fields = ["owner__phone", "owner__national_id", "id"]
    readonly_fields = [
        "id", "owner", "submitted_at", "completed_at", "expires_at",
        "raw_bvss", "penalty_multiplier", "final_bvss", "risk_tier",
        "score_p1", "score_p2", "score_p3", "score_p4", "score_p5", "score_p6",
        "social_verification_score",
    ]
    inlines = [FraudFlagInline, SocialReferenceInline, BehavioralSignalInline]

    fieldsets = (
        ("Owner", {"fields": ("id", "owner", "status")}),
        ("Scores", {
            "fields": (
                "score_p1", "score_p2", "score_p3",
                "score_p4", "score_p5", "score_p6",
                "raw_bvss", "penalty_multiplier", "final_bvss", "risk_tier",
            )
        }),
        ("Verification", {
            "fields": (
                "social_verification_complete",
                "social_verification_score",
                "requires_manual_review",
                "reviewer_notes",
            )
        }),
        ("Timeline", {
            "fields": ("submitted_at", "completed_at", "expires_at")
        }),
    )

    def final_bvss_display(self, obj):
        if obj.final_bvss is None:
            return "—"
        score = float(obj.final_bvss)
        color = (
            "#1D9E75" if score >= 800
            else "#639922" if score >= 650
            else "#BA7517" if score >= 500
            else "#D85A30" if score >= 350
            else "#A32D2D"
        )
        return format_html(
            '<strong style="color:{}">{}</strong>', color, f"{score:.0f}"
        )
    final_bvss_display.short_description = "BVSS"

    def flag_count(self, obj):
        count = obj.fraud_flags.count()
        if count == 0:
            return "✓"
        return format_html('<span style="color:#A32D2D">{} flags</span>', count)
    flag_count.short_description = "Flags"


@admin.register(FraudFlag)
class FraudFlagAdmin(admin.ModelAdmin):
    list_display = ["rule_id", "severity", "penalty_pct", "pillars_involved", "assessment", "created_at"]
    list_filter = ["severity", "rule_id"]
    search_fields = ["assessment__id", "rule_id"]
    readonly_fields = ["assessment", "rule_id", "severity", "penalty_pct", "description", "pillars_involved"]