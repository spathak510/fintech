from django.db import models


class LinkGenerateLogs(models.Model):
    type = (
        ('netbanking', 'netbanking'),
        ('statement', 'statement')
    )
    auto_id = models.AutoField(primary_key=True)
    txn_id = models.CharField(max_length=100)
    perfios_txn_id = models.CharField(max_length=500, null=True, blank=True)
    response_json = models.TextField(null=True, blank=True)
    generated_link = models.TextField(null=True, blank=True)
    link_type = models.CharField(max_length=20, null=True, blank=True)
    link_expire_at = models.CharField(max_length=100, null=True, blank=True)
    status_code = models.IntegerField(null=True)
    exception = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "link_generate_logs"
