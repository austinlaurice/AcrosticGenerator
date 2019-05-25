from django import forms
from .misc import RHYME_LIST

class PostForm(forms.Form):
    rhyme           = forms.ChoiceField(
                            choices=RHYME_LIST,
                            widget=forms.Select(
                                attrs={'class':'form-control'}
                            )
                      )

    keywords        = forms.CharField(
                            max_length=100,
                            required=False,
                            widget=forms.TextInput(
                                attrs={
                                    'size': 100,
                                    'class':'form-control'
                                }
                            )
                      )

    hidden_sentence = forms.CharField(
                            max_length=100,
                            widget=forms.TextInput(
                                attrs={
                                    'size': 100,
                                    'class':'form-control'
                                }
                            )
                      )

    length          = forms.CharField(
                            max_length=100,
                            required=False,
                            widget=forms.TextInput(
                                attrs={
                                    'size'        : 100,
                                    'class'       : 'form-control',
                                    'placeholder' : 'ex.15;10;3;18;12',
                                    'id'          : 'length'
                                }
                            )
                      )
    pattern         = forms.CharField(
                            max_length=100,
                            widget=forms.TextInput(
                                attrs={
                                    'size': 100,
                                    'class':'form-control'
                                }
                            )
                      )
    #pattern         = forms.ChoiceField(
    #                        choices=[
    #                            (0, 'First character of each sentence'),
    #                            (1, 'Last character of each sentence'),
    #                            (2, 'Diagonal line'),
    #                            (3, 'Draw it by myself')
    #                        ],
    #                        widget=forms.Select(
    #                            attrs={
    #                                'class':'form-control'
    #                            }
    #                        )
    #                  )
    
    
    
    
