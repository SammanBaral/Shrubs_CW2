from django.contrib import admin


from .models import AuditLog
from django.contrib import admin

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'user_role', 'action', 'entity', 'entity_id', 'ip_address')
    search_fields = ('user__username', 'action', 'entity', 'entity_id', 'ip_address', 'user_role')
    list_filter = ('user_role', 'action', 'entity')
