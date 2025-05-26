from django import forms
from .models import News, Review, TourPackage, Order

class TourPackageForm(forms.ModelForm):
    class Meta:
        model = TourPackage
        fields = '__all__'
        widgets = {
            'departure_date': forms.DateInput(attrs={'type': 'date'}),
            'return_date': forms.DateInput(attrs={'type': 'date'}),
        }

class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status', 'manager', 'notes']


class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ['title', 'slug', 'summary', 'content', 'image', 'category', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'summary': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }



class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['text', 'rating', 'hotel']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ваш отзыв...'
            }),
            'rating': forms.Select(attrs={
                'class': 'form-select'
            }),
            'hotel': forms.HiddenInput()
        }
        labels = {
            'text': '',
            'rating': 'Оценка',
            'hotel': ''
        }