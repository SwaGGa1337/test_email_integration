from django.db import models
import os

class EmailAccount(models.Model):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    provider = models.CharField(
        max_length=20,
        choices=[
            ('gmail', 'Gmail'),
            ('yandex', 'Yandex'),
            ('mailru', 'Mail.ru')
        ]
    )
    last_checked = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.email

    def get_imap_settings(self):
        IMAP_SETTINGS = {
            'gmail': {'host': 'imap.gmail.com', 'port': 993},
            'yandex': {'host': 'imap.yandex.ru', 'port': 993},
            'mailru': {'host': 'imap.mail.ru', 'port': 993},
        }
        return IMAP_SETTINGS.get(self.provider)

class EmailMessage(models.Model):
    account = models.ForeignKey(EmailAccount, on_delete=models.CASCADE)
    message_id = models.CharField(max_length=255, unique=True)
    subject = models.CharField(max_length=255)
    sender = models.EmailField()
    sent_date = models.DateTimeField()
    received_date = models.DateTimeField()
    content = models.TextField()
    attachments = models.JSONField(default=list)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-received_date']
        indexes = [
            models.Index(fields=['message_id']),
            models.Index(fields=['received_date']),
        ]

    def __str__(self):
        return self.subject

    def delete(self, *args, **kwargs):
        # Сначала удаляем все вложения
        for attachment in self.attachment_set.all():
            attachment.delete()
        # Затем удаляем само сообщение
        super().delete(*args, **kwargs)

class Attachment(models.Model):
    email_message = models.ForeignKey(EmailMessage, on_delete=models.CASCADE)
    file = models.FileField(upload_to='attachments/%Y/%m/%d/')
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    size = models.IntegerField()

    def __str__(self):
        return self.filename

    def delete(self, *args, **kwargs):
        # Удаляем физический файл
        if self.file:
            storage = self.file.storage
            if storage.exists(self.file.name):
                storage.delete(self.file.name)
        
        # Вызываем родительский метод delete
        super().delete(*args, **kwargs)
