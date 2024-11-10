from django.contrib import admin
from .models import EmailAccount, EmailMessage, Attachment

@admin.register(EmailAccount)
class EmailAccountAdmin(admin.ModelAdmin):
    list_display = ('email', 'provider', 'is_active', 'last_checked')
    list_filter = ('provider', 'is_active')
    search_fields = ('email',)

@admin.register(EmailMessage)
class EmailMessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'sender', 'received_date', 'account')
    list_filter = ('account', 'received_date')
    search_fields = ('subject', 'sender')
    date_hierarchy = 'received_date'

@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'email_message', 'content_type', 'size')
    list_filter = ('content_type',)
    search_fields = ('filename',) 