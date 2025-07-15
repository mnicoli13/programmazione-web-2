from django.db import models
from django.core.exceptions import ValidationError
from django.urls import reverse

class Veicolo(models.Model):
    telaio = models.CharField(
        max_length=50,
        primary_key=True,
        verbose_name="Numero Telaio",
        help_text="Numero di telaio univoco del veicolo"
    )
    marca = models.CharField(max_length=100, verbose_name="marca")
    modello = models.CharField(max_length=100, verbose_name="modello")
    dataProd = models.DateField(
        verbose_name="dataProduzione",
        db_column='dataProd'
    )

    class Meta:
        db_table = 'veicolo'
        verbose_name = "veicolo"
        verbose_name_plural = "veicoli"
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
        db_table = 'targa'
        verbose_name = "targa"
        verbose_name_plural = "targhe"
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
            if TargaRestituita.objects.filter(targa=self).exists():
                return 'Restituita'
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
        verbose_name="targa"
    )
    dataRev = models.DateField(
        verbose_name="dataRevisione",
        db_column='dataRev'
    )
    esito = models.CharField(
        max_length=10,
        choices=ESITO_CHOICES,
        verbose_name="esito"
    )
    motivazione = models.TextField(
        blank=True,
        null=True,
        verbose_name="motivazione",
        help_text="Obbligatoria per esito negativo, vuota per esito positivo"
    )

    class Meta:
        db_table = 'revisione'
        verbose_name = "revisione"
        verbose_name_plural = "revisioni"
        ordering = ['-dataRev']

    def __str__(self):
        return f"revisione {self.numero} - {self.targa} ({self.esito})"

    def clean(self):
        """Validazione del vincolo esito/motivazione"""
        if self.esito == 'positivo' and self.motivazione:
            raise ValidationError({'motivazione': 'Per esito positivo la motivazione deve essere vuota'})
        if self.esito == 'negativo' and not self.motivazione:
            raise ValidationError({'motivazione': 'Per esito negativo la motivazione è obbligatoria'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class TargaAttiva(models.Model):
    targa = models.OneToOneField(
        Targa,
        on_delete=models.CASCADE,
        primary_key=True,
        db_column='targa',
        verbose_name="targa"
    )
    veicolo = models.OneToOneField(
        Veicolo,
        on_delete=models.CASCADE,
        unique=True,
        db_column='veicolo',
        verbose_name="veicolo"
    )

    class Meta:
        db_table = 'targa_attiva'     # Tabella reale in minuscolo
        managed = True                # Ora Django creerà la tabella
        verbose_name = "targa attiva"
        verbose_name_plural = "targhe attive"

class TargaRestituita(models.Model):
    targa = models.OneToOneField(
        Targa,
        on_delete=models.CASCADE,
        primary_key=True,
        db_column='targa',
        verbose_name="targa"
    )
    veicolo = models.OneToOneField(
        Veicolo,
        on_delete=models.CASCADE,
        db_column='veicolo',
        verbose_name="veicolo"
    )
    dataRes = models.DateField(
        db_column='dataRes',
        verbose_name="Data Restituzione"
    )

    class Meta:
        db_table = 'targa_restituita' # Tabella reale in minuscolo
        managed = True                # Ora Django creerà la tabella
        verbose_name = "targa restituita"
        verbose_name_plural = "targhe restituite"
