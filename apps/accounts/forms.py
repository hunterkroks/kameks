from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@mail.ru'}),
    )
    first_name = forms.CharField(
        max_length=100, required=True,
        label='Имя',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ваше имя'}),
    )
    phone = forms.CharField(
        max_length=20, required=False,
        label='Номер телефона',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (___) ___-__-__'}),
    )

    class Meta:
        model = User
        fields = ('first_name', 'email', 'phone', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # username генерируется автоматически из email, убираем его из формы
        if 'username' in self.fields:
            del self.fields['username']
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Минимум 8 символов'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Повторите пароль'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        # username = часть email до @, с гарантией уникальности
        base = self.cleaned_data['email'].split('@')[0]
        username = base
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f'{base}{counter}'
            counter += 1
        user.username = username
        if commit:
            user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            phone = self.cleaned_data.get('phone', '').strip()
            if phone:
                profile.phone = phone
                profile.save()
        return user


class FlexLoginForm(forms.Form):
    """Вход по логину, email или телефону + пароль."""
    login = forms.CharField(
        label='Email или телефон',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email или номер телефона', 'autofocus': True}),
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Пароль'}),
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self._user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        login_val = cleaned.get('login', '').strip()
        password = cleaned.get('password', '')
        if not login_val or not password:
            return cleaned

        user = None

        # 1. По email (case-insensitive)
        try:
            u = User.objects.get(email__iexact=login_val)
            if u.check_password(password):
                user = u
        except User.DoesNotExist:
            pass

        # 2. По телефону в UserProfile
        if user is None:
            try:
                from .models import UserProfile as UP
                profile = UP.objects.select_related('user').get(phone=login_val)
                if profile.user.check_password(password):
                    user = profile.user
            except UP.DoesNotExist:
                pass

        if user is None:
            raise forms.ValidationError('Неверный логин или пароль. Проверьте данные и попробуйте снова.')

        if not user.is_active:
            raise forms.ValidationError('Аккаунт заблокирован. Обратитесь в поддержку.')

        self._user = user
        return cleaned

    def get_user(self):
        return self._user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('phone', 'company_name', 'inn', 'address', 'avatar')
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'inn': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
