from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field
from crispy_forms.bootstrap import FormActions
from .models import Veicolo, Targa, Revisione, TargaAttiva, TargaRestituita


class VeicoloForm(forms.ModelForm):
    """Form per la gestione dei veicoli"""
    
    class Meta:
        model = Veicolo
        fields = ['telaio', 'marca', 'modello', 'dataProd']
        widgets = {
            'telaio': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Inserisci numero telaio',
                'maxlength': 50
            }),
            'marca': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Inserisci marca',
                'maxlength': 100
            }),
            'modello': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Inserisci modello',
                'maxlength': 100
            }),
            'dataProd': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
        labels = {
            'telaio': 'Numero Telaio',
            'marca': 'Marca',
            'modello': 'Modello',
            'dataProd': 'Data Produzione'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('telaio', css_class='form-group col-md-6 mb-3'),
                Column('marca', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('modello', css_class='form-group col-md-6 mb-3'),
                Column('dataProd', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            FormActions(
                Submit('submit', 'Salva', css_class='btn btn-primary'),
                css_class='text-end'
            )
        )
        
        # Imposta tutti i campi come obbligatori
        for field in self.fields:
            self.fields[field].required = True
    
    def clean_telaio(self):
        """Validazione personalizzata per il telaio"""
        telaio = self.cleaned_data.get('telaio')
        if telaio:
            telaio = telaio.strip().upper()
            
            # Verifica unicità solo se è un nuovo record o se il telaio è cambiato
            if self.instance.pk is None or self.instance.telaio != telaio:
                if Veicolo.objects.filter(telaio=telaio).exists():
                    raise ValidationError('Questo numero di telaio è già stato utilizzato.')
        
        return telaio


class TargaForm(forms.ModelForm):
    """Form per la gestione delle targhe"""
    
    class Meta:
        model = Targa
        fields = ['numero', 'dataEm']
        widgets = {
            'numero': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Inserisci numero targa',
                'maxlength': 20
            }),
            'dataEm': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
        labels = {
            'numero': 'Numero Targa',
            'dataEm': 'Data Emissione'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('numero', css_class='form-group col-md-6 mb-3'),
                Column('dataEm', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            FormActions(
                Submit('submit', 'Salva', css_class='btn btn-primary'),
                css_class='text-end'
            )
        )
        
        for field in self.fields:
            self.fields[field].required = True


class RevisioneForm(forms.ModelForm):
    """Form per la gestione delle revisioni"""
    
    class Meta:
        model = Revisione
        fields = ['targa', 'dataRev', 'esito', 'motivazione']
        widgets = {
            'targa': forms.Select(attrs={'class': 'form-control'}),
            'dataRev': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'esito': forms.Select(attrs={'class': 'form-control'}),
            'motivazione': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Inserisci motivazione (obbligatoria per esito negativo)'
            }),
        }
        labels = {
            'targa': 'Targa',
            'dataRev': 'Data Revisione',
            'esito': 'Esito',
            'motivazione': 'Motivazione'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('targa', css_class='form-group col-md-6 mb-3'),
                Column('dataRev', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('esito', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            'motivazione',
            FormActions(
                Submit('submit', 'Salva', css_class='btn btn-primary'),
                css_class='text-end'
            )
        )
        
        # Campi obbligatori
        self.fields['targa'].required = True
        self.fields['dataRev'].required = True
        self.fields['esito'].required = True
        self.fields['motivazione'].required = False  # Dipende dall'esito
    
    def clean(self):
        """Validazione del vincolo esito/motivazione"""
        cleaned_data = super().clean()
        esito = cleaned_data.get('esito')
        motivazione = cleaned_data.get('motivazione')
        
        if esito == 'positivo' and motivazione:
            raise ValidationError({
                'motivazione': 'Per esito positivo la motivazione deve essere vuota'
            })
        
        if esito == 'negativo' and not motivazione:
            raise ValidationError({
                'motivazione': 'Per esito negativo la motivazione è obbligatoria'
            })
        
        return cleaned_data


class TargaAttivaForm(forms.ModelForm):
    """Form per assegnare una targa a un veicolo"""
    
    class Meta:
        model = TargaAttiva
        fields = ['targa', 'veicolo']
        widgets = {
            'targa': forms.Select(attrs={'class': 'form-control'}),
            'veicolo': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'targa': 'Targa',
            'veicolo': 'Veicolo'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('targa', css_class='form-group col-md-6 mb-3'),
                Column('veicolo', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            FormActions(
                Submit('submit', 'Assegna Targa', css_class='btn btn-primary'),
                css_class='text-end'
            )
        )
        
        # Filtra solo targhe non assegnate
        try:
            targhe_assegnate = TargaAttiva.objects.values_list('targa', flat=True)
            self.fields['targa'].queryset = Targa.objects.exclude(numero__in=targhe_assegnate)
        except:
            self.fields['targa'].queryset = Targa.objects.all()
        
        for field in self.fields:
            self.fields[field].required = True
    
    def clean_veicolo(self):
        """Verifica che il veicolo non abbia già una targa attiva"""
        veicolo = self.cleaned_data.get('veicolo')
        if veicolo and TargaAttiva.objects.filter(veicolo=veicolo).exists():
            raise ValidationError('Questo veicolo ha già una targa attiva.')
        return veicolo


class TargaRestituitaForm(forms.ModelForm):
    """Form per registrare la restituzione di una targa"""
    
    class Meta:
        model = TargaRestituita
        fields = ['targa', 'veicolo', 'dataRes']
        widgets = {
            'targa': forms.Select(attrs={'class': 'form-control'}),
            'veicolo': forms.Select(attrs={'class': 'form-control'}),
            'dataRes': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
        labels = {
            'targa': 'Targa',
            'veicolo': 'Veicolo',
            'dataRes': 'Data Restituzione'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('targa', css_class='form-group col-md-4 mb-3'),
                Column('veicolo', css_class='form-group col-md-4 mb-3'),
                Column('dataRes', css_class='form-group col-md-4 mb-3'),
                css_class='form-row'
            ),
            FormActions(
                Submit('submit', 'Registra Restituzione', css_class='btn btn-warning'),
                css_class='text-end'
            )
        )
        
        for field in self.fields:
            self.fields[field].required = True


class FiltroVeicoliForm(forms.Form):
    """Form per filtrare i veicoli (usato nell'interfaccia AJAX)"""
    
    telaio = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filtra per telaio'
        })
    )
    marca = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filtra per marca'
        })
    )
    modello = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filtra per modello'
        })
    )
    dataProd = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'GET'
        self.helper.layout = Layout(
            Row(
                Column('telaio', css_class='form-group col-md-3 mb-3'),
                Column('marca', css_class='form-group col-md-3 mb-3'),
                Column('modello', css_class='form-group col-md-3 mb-3'),
                Column('dataProd', css_class='form-group col-md-3 mb-3'),
                css_class='form-row'
            ),
            FormActions(
                Submit('filter', 'Filtra', css_class='btn btn-outline-primary'),
                css_class='text-end'
            )
        )