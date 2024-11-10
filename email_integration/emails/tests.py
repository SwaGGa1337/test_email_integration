from django.test import TransactionTestCase, Client
from django.urls import reverse
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from channels.auth import AuthMiddlewareStack
from asgiref.sync import sync_to_async
from django.core.files.base import ContentFile
from datetime import datetime
import pytz
import os

from .models import EmailAccount, EmailMessage, Attachment
from .consumers import EmailSyncConsumer
from email_integration.routing import websocket_urlpatterns

class EmailAccountModelTests(TransactionTestCase):
    def setUp(self):
        self.account = EmailAccount.objects.create(
            email='test@yandex.ru',
            password='test_password',
            provider='yandex'
        )

    def test_email_account_creation(self):
        """Тест создания учетной записи почты"""
        self.assertEqual(self.account.email, 'test@yandex.ru')
        self.assertEqual(self.account.provider, 'yandex')
        self.assertTrue(self.account.is_active)

    def test_get_imap_settings(self):
        """Тест получения настроек IMAP для разных провайдеров"""
        # Тест Yandex
        yandex_settings = self.account.get_imap_settings()
        self.assertEqual(yandex_settings['host'], 'imap.yandex.ru')
        self.assertEqual(yandex_settings['port'], 993)

        # Тест Gmail
        gmail_account = EmailAccount.objects.create(
            email='test@gmail.com',
            password='test_password',
            provider='gmail'
        )
        gmail_settings = gmail_account.get_imap_settings()
        self.assertEqual(gmail_settings['host'], 'imap.gmail.com')
        self.assertEqual(gmail_settings['port'], 993)

class EmailMessageModelTests(TransactionTestCase):
    def setUp(self):
        self.account = EmailAccount.objects.create(
            email='test@yandex.ru',
            password='test_password',
            provider='yandex'
        )
        self.message = EmailMessage.objects.create(
            account=self.account,
            message_id='test_id_123',
            subject='Test Subject',
            sender='sender@example.com',
            sent_date=datetime.now(pytz.UTC),
            received_date=datetime.now(pytz.UTC),
            content='Test content'
        )

    def test_email_message_creation(self):
        """Тест создания сообщения"""
        self.assertEqual(self.message.subject, 'Test Subject')
        self.assertEqual(self.message.sender, 'sender@example.com')
        self.assertFalse(self.message.is_read)

    def test_attachments_handling(self):
        """Тест обработки вложений"""
        # Создаем тестовое вложение
        attachment_data = {
            'id': 1,
            'filename': 'test.txt',
            'size': 100
        }
        self.message.attachments = [attachment_data]
        self.message.save()

        # Проверяем сохранение и получение вложения
        saved_message = EmailMessage.objects.get(id=self.message.id)
        self.assertEqual(len(saved_message.attachments), 1)
        self.assertEqual(saved_message.attachments[0]['filename'], 'test.txt')

class WebSocketTests(TransactionTestCase):
    async def test_websocket_connection(self):
        """Тест WebSocket соединения"""
        application = AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
        communicator = WebsocketCommunicator(application, "/ws/emails/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()

    async def test_websocket_receive_message(self):
        """Тест получения сообщений через WebSocket"""
        application = AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
        communicator = WebsocketCommunicator(application, "/ws/emails/")
        await communicator.connect()

        account = await self.async_create_account()
        await communicator.send_json_to({
            'account_id': account.id
        })

        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'sync_status')
        self.assertEqual(response['status'], 'starting')

        await communicator.disconnect()

    @staticmethod
    async def async_create_account():
        return await sync_to_async(EmailAccount.objects.create)(
            email='test@yandex.ru',
            password='test_password',
            provider='yandex'
        )

class ViewTests(TransactionTestCase):
    def setUp(self):
        self.client = Client()
        self.account = EmailAccount.objects.create(
            email='test@yandex.ru',
            password='test_password',
            provider='yandex'
        )

    def test_email_list_view(self):
        """Тест отображения списка писем"""
        # Создаем тестовые письма
        for i in range(3):
            EmailMessage.objects.create(
                account=self.account,
                message_id=f'test_id_{i}',
                subject=f'Test Subject {i}',
                sender='sender@example.com',
                sent_date=datetime.now(pytz.UTC),
                received_date=datetime.now(pytz.UTC),
                content=f'Test content {i}'
            )

        # Проверяем страницу списка
        response = self.client.get(reverse('email_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'emails/email_list.html')
        self.assertEqual(len(response.context['emails']), 3)

    def test_account_create_view(self):
        """Тест создания нового почтового аккаунта"""
        response = self.client.get(reverse('account_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'emails/account_form.html')

        # Тестируем POST запрос
        post_data = {
            'email': 'new@gmail.com',
            'password': 'new_password',
            'provider': 'gmail'
        }
        response = self.client.post(reverse('account_create'), post_data)
        self.assertEqual(response.status_code, 302)  # Редирект после успешного создания
        
        # Проверяем создание аккаунта
        self.assertTrue(
            EmailAccount.objects.filter(email='new@gmail.com').exists()
        )

class AttachmentTests(TransactionTestCase):
    def setUp(self):
        self.account = EmailAccount.objects.create(
            email='test@yandex.ru',
            password='test_password',
            provider='yandex'
        )
        self.message = EmailMessage.objects.create(
            account=self.account,
            message_id='test_id_123',
            subject='Test Subject',
            sender='sender@example.com',
            sent_date=datetime.now(pytz.UTC),
            received_date=datetime.now(pytz.UTC),
            content='Test content'
        )

    def test_attachment_creation(self):
        """Тест создания вложения"""
        # Создаем тестовый файл
        file_content = ContentFile(b'Test file content')
        
        attachment = Attachment.objects.create(
            email_message=self.message,
            filename='test.txt',
            content_type='text/plain',
            size=len('Test file content')
        )
        attachment.file.save('test.txt', file_content)

        # Проверяем сохранение вложения
        saved_attachment = Attachment.objects.get(id=attachment.id)
        self.assertEqual(saved_attachment.filename, 'test.txt')
        self.assertEqual(saved_attachment.content_type, 'text/plain')
        self.assertEqual(saved_attachment.size, len('Test file content'))
        
        # Проверяем содержимое файла
        self.assertEqual(
            saved_attachment.file.read().decode(),
            'Test file content'
        )

    def test_attachment_deletion(self):
        """Тест удаления вложения вместе с сообщением"""
        # Создаем вложение
        file_content = ContentFile(b'Test file content')
        attachment = Attachment.objects.create(
            email_message=self.message,
            filename='test.txt',
            content_type='text/plain',
            size=len('Test file content')
        )
        attachment.file.save('test.txt', file_content)

        # Сохраняем путь к файлу
        file_path = attachment.file.path

        # Удаляем сообщение
        self.message.delete()

        # Проверяем, что вложение тоже удалено
        self.assertFalse(Attachment.objects.filter(id=attachment.id).exists())
        # Проверяем, что файл удален с диска
        self.assertFalse(os.path.exists(file_path))
