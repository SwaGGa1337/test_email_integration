import email
import os
from datetime import datetime
from email.header import decode_header
from imap_tools import MailBox, AND
from django.conf import settings
from django.core.files.base import ContentFile
from .models import EmailMessage, Attachment

class EmailHandler:
    def __init__(self, account):
        self.account = account
        self.settings = account.get_imap_settings()

    async def process_messages(self):
        with MailBox(self.settings['host']).login(
            self.account.email, 
            self.account.password
        ) as mailbox:
            # Получаем последнее обработанное сообщение
            last_message = EmailMessage.objects.filter(
                account=self.account
            ).order_by('-received_date').first()

            # Формируем критерии поиска
            criteria = None
            if last_message:
                criteria = AND(date_gte=last_message.received_date.date())

            messages = mailbox.fetch(criteria=criteria, reverse=True)
            total_messages = len(list(messages))
            
            for i, msg in enumerate(messages, 1):
                try:
                    # Проверяем, существует ли сообщение
                    if not EmailMessage.objects.filter(message_id=msg.uid).exists():
                        email_message = EmailMessage.objects.create(
                            account=self.account,
                            message_id=msg.uid,
                            subject=msg.subject,
                            sender=msg.from_,
                            sent_date=msg.date,
                            received_date=msg.date,
                            content=msg.text or msg.html
                        )

                        # Обработка вложений
                        attachments_info = []
                        for att in msg.attachments:
                            attachment = Attachment.objects.create(
                                email_message=email_message,
                                filename=att.filename,
                                content_type=att.content_type,
                                size=len(att.payload)
                            )
                            
                            # Сохраняем файл
                            file_content = ContentFile(att.payload)
                            attachment.file.save(att.filename, file_content)
                            
                            attachments_info.append({
                                'id': attachment.id,
                                'filename': attachment.filename,
                                'size': attachment.size
                            })
                        
                        email_message.attachments = attachments_info
                        email_message.save()

                except Exception as e:
                    print(f"Error processing message: {e}")
                    continue

                yield {
                    'progress': i,
                    'total': total_messages,
                    'message': {
                        'subject': email_message.subject,
                        'sender': email_message.sender,
                        'date': email_message.received_date.strftime('%Y-%m-%d %H:%M')
                    }
                } 