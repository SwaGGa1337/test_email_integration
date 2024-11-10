from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from .models import EmailAccount, EmailMessage

class EmailAccountCreateView(CreateView):
    model = EmailAccount
    fields = ['email', 'password', 'provider']
    success_url = reverse_lazy('email_list')
    template_name = 'emails/account_form.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['email'].widget.attrs.update({'class': 'form-control'})
        form.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'type': 'password'
        })
        form.fields['provider'].widget.attrs.update({'class': 'form-control'})
        return form

class EmailListView(ListView):
    model = EmailMessage
    template_name = 'emails/email_list.html'
    context_object_name = 'emails'
    paginate_by = 50

    def get_queryset(self):
        return EmailMessage.objects.select_related('account').all() 