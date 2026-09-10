from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(5, '★★★★★ (5 - Outstanding)'),
                 (4, '★★★★☆ (4 - Great Work)'),
                 (3, '★★★☆☆ (3 - Satisfactory)'),
                 (2, '★★☆☆☆ (2 - Below Expectation)'),
                 (1, '★☆☆☆☆ (1 - Poor)')],
        widget=forms.Select(attrs={'class': 'form-control select-modern'})
    )

    class Meta:
        model = Review
        fields = ('rating', 'comment')
        widgets = {
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Share your experience working with this professional...'}),
        }
