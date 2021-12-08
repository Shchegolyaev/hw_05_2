from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import ContactForm, CreationForm


def user_contact(request):
    form = ContactForm()

    return render(request, 'contact.html', {'form': form})


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('login')
    template_name = "signup.html"
