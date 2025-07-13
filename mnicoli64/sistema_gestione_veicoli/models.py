from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.urls import reverse


class Veicolo(models.Model):
    telaio = models.CharField(
        max_length=50, 
        primary_key=True, 
        verbose_name="Numero Telaio",
        help_text="Numero di telaio univoco del veicolo"
    )
    marca = models.CharField(max_length=100, verbose_name="Marca")
    modello = models.CharField(max_length=100, verbose_name="Modello")
    dataProd = models.DateField(
        verbose_name="Data Produzione", 
        db_column='dataProd'
    )
    
    class Meta:
        db_table = 'Veicolo'
        verbose_name = "Veicolo"
        verbose_name_plural = "Veicoli"
        ordering = ['telaio']
    
    def __str__(self):
        return f"{self.marca} {self.modello} ({self.telaio})"
    
    def get_absolute_url(self):
        return reverse('veicolo_detail', kwargs={'pk': self.telaio})


class Targa(models.Model):
    numero = models.CharField(
        max_length=20, 
        primary_key=True, 
        verbose_name="Numero Targa"
    )
    dataEm = models.DateField(
        verbose_name="Data Emissione", 
        db_column='dataEm'
    )
    
    class Meta:
        db_table = 'Targa'
        verbose_name = "Targa"
        verbose_name_plural = "Targhe"
        ordering = ['numero']
    
    def __str__(self):
        return self.numero
    
    def get_absolute_url(self):
        return reverse('targa_detail', kwargs={'pk': self.numero})
    
    @property
    def stato(self):
        """Restituisce lo stato della targa (Attiva, Restituita, Non assegnata)"""
        try:
            TargaAttiva.objects.get(targa=self)
            return 'Attiva'
        except TargaAttiva.DoesNotExist:
            try:
                TargaRestituita.objects.filter(targa=self).exists()
                if TargaRestituita.objects.filter(targa=self).exists():
                    return 'Restituita'
            except TargaRestituita.DoesNotExist:
                pass
        return 'Non assegnata'


class Revisione(models.Model):
    ESITO_CHOICES = [
        ('positivo', 'Positivo'),
        ('negativo', 'Negativo'),
    ]
    
    numero = models.AutoField(primary_key=True)
    targa = models.ForeignKey(
        Targa, 
        on_delete=models.CASCADE, 
        db_column='targa',
        verbose_name="Targa"
    )
    dataRev = models.DateField(
        verbose_name="Data Revisione", 
        db_column='dataRev'
    )
    esito = models.CharField(
        max_length=10, 
        choices=ESITO_CHOICES, 
        verbose_name="Esito"
    )
    motivazione = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Motivazione",
        help_text="Obbligatoria per esito negativo, vuota per esito positivo"
    )
    
    class Meta:
        db_table = 'Revisione'
        verbose_name = "Revisione"
        verbose_name_plural = "Revisioni"
        ordering = ['-dataRev']
    
    def __str__(self):
        return f"Revisione {self.numero} - {self.targa} ({self.esito})"
    
    def clean(self):
        """Validazione del vincolo esito/motivazione"""
        if self.esito == 'positivo' and self.motivazione:
            raise ValidationError({
                'motivazione': 'Per esito positivo la motivazione deve essere vuota'
            })
        if self.esito == 'negativo' and not self.motivazione:
            raise ValidationError({
                'motivazione': 'Per esito negativo la motivazione è obbligatoria'
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class TargaAttiva(models.Model):
    targa = models.OneToOneField(
        Targa,
        on_delete=models.CASCADE,
        primary_key=True,
        db_column='targa',          # <— tell Django the actual column
        verbose_name="Targa"
    )
    veicolo = models.OneToOneField(
        Veicolo,
        on_delete=models.CASCADE,
        unique=True,
        db_column='veicolo',        # likewise if your column is named just 'veicolo'
        verbose_name="Veicolo"
    )
    class Meta:
        db_table = 'TargaAttiva'
        managed = False             # if this is a legacy table you don’t want Django to migrate
        verbose_name = "Targa Attiva"
        verbose_name_plural = "Targhe Attive"

class TargaRestituita(models.Model):
    targa = models.OneToOneField(
        Targa,  
        on_delete=models.CASCADE,
        primary_key=True, 
        db_column='targa',
        verbose_name="Targa"
    )
    veicolo = models.OneToOneField(
        Veicolo, 
        on_delete=models.CASCADE,
        db_column='veicolo', 
        verbose_name="Veicolo"
    )
    
    dataRes = models.DateField(db_column='dataRes', verbose_name="Data Restituzione")

    class Meta:
        db_table = 'TargaRestituita'
        managed = False
        verbose_name = "Targa Restituita"
        verbose_name_plural = "Targhe Restituite"

class Utenti(models.Model):
    """
    Modello per mappare la tabella Utenti esistente.
    Utilizzato per la migrazione dei dati verso Django User.
    """
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'Utenti'
        verbose_name = "Utente (Legacy)"
        verbose_name_plural = "Utenti (Legacy)"
        managed = False  # Django non gestirà questa tabella
    
    def __str__(self):
        return self.username
