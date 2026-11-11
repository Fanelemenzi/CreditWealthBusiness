"""
Migration: add firebase_uid, make phone/national_id/date_of_birth optional.

phone and national_id become nullable/blank because Firebase does not supply
them at sign-up — the owner fills them in later via PATCH /api/auth/me/.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        # Add firebase_uid — the stable link to the Firebase account
        migrations.AddField(
            model_name="businessowner",
            name="firebase_uid",
            field=models.CharField(
                blank=True,
                db_index=True,
                max_length=128,
                null=True,
                unique=True,
                verbose_name="Firebase UID",
            ),
        ),
        # phone: was required (unique, not null) — now optional
        migrations.AlterField(
            model_name="businessowner",
            name="phone",
            field=models.CharField(
                blank=True,
                max_length=20,
                null=True,
                unique=True,
                verbose_name="phone number",
            ),
        ),
        # national_id: was required (unique, not null) — now optional
        migrations.AlterField(
            model_name="businessowner",
            name="national_id",
            field=models.CharField(
                blank=True,
                max_length=50,
                null=True,
                unique=True,
                verbose_name="national ID",
            ),
        ),
        # date_of_birth: was required — now optional
        migrations.AlterField(
            model_name="businessowner",
            name="date_of_birth",
            field=models.DateField(
                blank=True,
                null=True,
                verbose_name="date of birth",
            ),
        ),
    ]
