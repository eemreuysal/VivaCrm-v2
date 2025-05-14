from django import forms
from django.contrib.auth import forms as admin_forms
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, HTML
from django.contrib.auth.forms import AuthenticationForm

User = get_user_model()


class UserChangeForm(admin_forms.UserChangeForm):
    class Meta(admin_forms.UserChangeForm.Meta):
        model = User
        fields = ["first_name", "last_name", "email", "avatar", "phone", "title", "department"]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-control mb-2'),
                Column('last_name', css_class='form-control mb-2'),
                css_class='grid grid-cols-1 md:grid-cols-2 gap-4'
            ),
            'email',
            'avatar',
            Row(
                Column('phone', css_class='form-control mb-2'),
                Column('title', css_class='form-control mb-2'),
                css_class='grid grid-cols-1 md:grid-cols-2 gap-4'
            ),
            'department',
            Submit('submit', 'Kaydet', css_class='btn btn-primary mt-4')
        )


class UserLoginForm(AuthenticationForm):
    """
    Custom login form that explicitly uses the username field
    """
    username = forms.CharField(label=_("Kullanıcı Adı"))
    password = forms.CharField(label=_("Şifre"), widget=forms.PasswordInput)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'username',
            'password',
            Submit('submit', 'Giriş Yap', css_class='btn btn-primary mt-4')
        )


class UserCreationForm(admin_forms.UserCreationForm):
    class Meta(admin_forms.UserCreationForm.Meta):
        model = User
        fields = ["username", "email"]
        error_messages = {
            "username": {"unique": _("Bu kullanıcı adı zaten alınmış.")},
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'username',
            'email',
            'password1',
            'password2',
            Submit('submit', 'Kaydol', css_class='btn btn-primary mt-4')
        )