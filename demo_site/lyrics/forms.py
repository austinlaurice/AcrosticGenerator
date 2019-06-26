from django import forms
from .misc_english import RHYME_LIST

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
                                    'size'  : 100,
                                    'class' : 'form-control',
                                    'id'    : 'hidden_sentence',
                                    'onchange': 'tableShow(\'pattern_define\', \'hidden_sentence\')',
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
                                    'id'          : 'length',
                                    'onchange': 'tableShow(\'pattern_define\', \'length\')',
                                }
                            )
                      )
    length_word     = forms.CharField(
                            max_length=100,
                            required=False,
                            widget=forms.TextInput(
                                attrs={
                                    'size'        : 100,
                                    'class'       : 'form-control',
                                    'placeholder' : 'ex.15;10;3;18;12',
                                    'id'          : 'length_word'
                                }
                            )
                      )

    pattern         = forms.ChoiceField(
                            choices=[
                                (0, 'First character of each sentence'),
                                (1, 'Last character of each sentence'),
                                (2, 'Diagonal line'),
                                (3, 'Draw it by myself')
                            ],
                            widget=forms.Select(
                                attrs={
                                    'class'     : 'form-control',
                                    'onchange'  : 'tableShow(\'pattern_define\', \'pattern\')',
                                    'id'        : 'pattern'
                                    #'onchange': 'tableShow(\'pattern_define\', pattern, \'pattern\')',
                                }
                            )
                      )

    selected_index  = forms.CharField(
                            max_length=100,
                            required=False,
                            widget=forms.HiddenInput(
                                attrs={
                                    'id'          : 'selected_index'
                                }
                            )
                      )
