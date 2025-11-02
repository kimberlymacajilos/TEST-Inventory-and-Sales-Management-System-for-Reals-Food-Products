# Generated migration for adding database indexes to improve expiration check performance

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('realsproj', '0001_initial'),  # Update this to your latest migration
    ]

    operations = [
        # Add indexes for ProductBatches expiration queries
        migrations.AddIndex(
            model_name='productbatches',
            index=models.Index(
                fields=['is_archived', 'expiration_date', 'quantity'],
                name='product_exp_idx'
            ),
        ),
        # Add indexes for RawMaterialBatches expiration queries
        migrations.AddIndex(
            model_name='rawmaterialbatches',
            index=models.Index(
                fields=['is_archived', 'expiration_date', 'quantity'],
                name='rawmat_exp_idx'
            ),
        ),
        # Add indexes for Notifications expiration alerts
        migrations.AddIndex(
            model_name='notifications',
            index=models.Index(
                fields=['notification_type', 'item_type', 'item_id'],
                name='notif_exp_idx'
            ),
        ),
        # Add indexes for Withdrawals queries (for financial loss page)
        migrations.AddIndex(
            model_name='withdrawals',
            index=models.Index(
                fields=['reason', 'date', 'item_type'],
                name='withdraw_loss_idx'
            ),
        ),
    ]
