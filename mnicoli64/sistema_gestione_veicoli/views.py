import re
import logging
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseServerError
from django.views.decorators.http import require_http_methods, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.db.models import Case, When, Value, CharField

from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db import IntegrityError, transaction, DatabaseError, connection
import json
from datetime import datetime

from .models import Veicolo, Targa, Revisione, TargaAttiva, TargaRestituita
from .forms import VeicoloForm

logger = logging.getLogger(__name__)

# Homepage View
def dashboard(request):
    """Dashboard principale del sistema"""
    context = {
        'total_veicoli': Veicolo.objects.count(),
        'total_targhe': Targa.objects.count(),
        'targhe_attive': TargaAttiva.objects.count(),
        'targhe_restituite': TargaRestituita.objects.count(),
        'revisioni_totali': Revisione.objects.count(),
        'revisioni_positive': Revisione.objects.filter(esito='positivo').count(),
        'revisioni_negative': Revisione.objects.filter(esito='negativo').count(),
    }
    return render(request, 'pages/homepage.html', context)


# =============================================================================
# VEICOLI VIEWS
# =============================================================================

filter_fields = [
    'telaio', 'marca', 'modello', 'dataProd',
    'numero', 'dataEm', 'stato', 'targa',
    'veicolo', 'dataRev', 'dataRes', 'esito', 'motivazione'
]

# central configuration dict for each field
FIELD_CONFIG = {
    'telaio':      {'label': 'Numero Telaio',     'placeholder': 'Cerca per telaio...',      'type': 'text',   'icon': 'bi-upc-scan'},
    'marca':       {'label': 'Marca',              'placeholder': 'Cerca per marca...',       'type': 'text',   'icon': 'bi-building'},
    'modello':     {'label': 'Modello',            'placeholder': 'Cerca per modello...',     'type': 'text',   'icon': 'bi-car-front'},
    'dataProd':    {'label': 'Data Produzione',    'placeholder': 'Seleziona data...',        'type': 'date',   'icon': 'bi-calendar-date'},
    'numero':      {'label': 'Numero',             'placeholder': 'Cerca per numero...',      'type': 'text',   'icon': 'bi-tag'},
    'dataEm':      {'label': 'Data Emissione',     'placeholder': 'Seleziona data...',        'type': 'date',   'icon': 'bi-calendar-date'},
    'stato':       {'label': 'Stato Targa',        'placeholder': 'Seleziona stato...',       'type': 'select', 'icon': 'bi-flag',
                    'options': [('attiva', 'Attiva'), ('restituita', 'Restituita'), ('Non assegnata', 'Non assegnata')]},
    'targa':       {'label': 'Targa',              'placeholder': 'Cerca per targa...',       'type': 'text',   'icon': 'bi-tag'},
    'veicolo':     {'label': 'Veicolo',            'placeholder': 'Cerca per veicolo...',     'type': 'text',   'icon': 'bi-car-front'},
    'dataRev':     {'label': 'Data Revisione',     'placeholder': 'Seleziona data...',        'type': 'date',   'icon': 'bi-calendar-check'},
    'dataRes':     {'label': 'Data Restituzione',  'placeholder': 'Seleziona data...',        'type': 'date',   'icon': 'bi-calendar-x'},
    'esito':       {'label': 'Esito Revisione',    'placeholder': 'Seleziona esito...',       'type': 'select', 'icon': 'bi-clipboard-check',
                    'options': [('positivo', 'Positivo'), ('negativo', 'Negativo')]},
    'motivazione': {'label': 'Motivazione',        'placeholder': 'Cerca per motivazione...', 'type': 'text',   'icon': 'bi-chat-text'},
}

VEICOLO_FIELDS = [
    'telaio','marca','modello','dataProd',
]

TARGA_FIELDS = [
    'numero','dataEm','stato'
]

TARGA_ATTIVA_FIELDS = [
    'targa', 'veicolo','dataEm'
]

TARGA_RESTITUITA_FIELDS = [
   'targa','veicolo','dataEm','dataRes'
]

REVISIONE_FIELDS = [
    'numero', 'targa', 'dataRev', 'esito','motivazione'
]

class VeicoloListView(ListView):
    model = Veicolo
    template_name = 'pages/veicolo.html'
    context_object_name = 'veicoli'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        for field, cfg in FIELD_CONFIG.items():
            val = self.request.GET.get(field)
            if val:
                lookup = field if cfg['input_type']=='date' else f"{field}__icontains"
                qs = qs.filter(**{lookup: val})
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        current = {f: self.request.GET.get(f, '') for f in VEICOLO_FIELDS}

        # build list of field‑configs including the current value
        ctx['filter_fields'] = []
        for f in VEICOLO_FIELDS:
            if f in FIELD_CONFIG:
                cfg = FIELD_CONFIG[f].copy()
                cfg.update(name=f, value=current[f])
                ctx['filter_fields'].append(cfg)

        return ctx

class VeicoloDetailView(DetailView):
    model = Veicolo
    template_name = 'pages/veicoli/detail.html'
    context_object_name = 'veicolo'

class VeicoloCreateView(CreateView):
    model = Veicolo
    form_class = VeicoloForm
    template_name = 'pages/veicoli/form.html'
    success_url = reverse_lazy('veicoli_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Veicolo aggiunto con successo!')
        return super().form_valid(form)

class VeicoloUpdateView(UpdateView):
    model = Veicolo
    form_class = VeicoloForm
    template_name = 'pages/veicoli/form.html'
    success_url = reverse_lazy('veicoli_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Veicolo modificato con successo!')
        return super().form_valid(form)

class VeicoloDeleteView(DeleteView):
    model = Veicolo
    template_name = 'pages/veicoli/confirm_delete.html'
    success_url = reverse_lazy('veicoli_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Veicolo eliminato con successo!')
        return super().delete(request, *args, **kwargs)

# =============================================================================
# API VIEWS per AJAX (compatibilità con frontend PHP)
# =============================================================================

@require_http_methods(["GET"])
def get_veicoli_data(request):
    """API per ottenere dati veicoli con filtri (compatibile con AJAX frontend PHP)"""
    try:
        # Parametri filtro
        telaio = request.GET.get('telaio', '')
        marca = request.GET.get('marca', '')
        modello = request.GET.get('modello', '')
        dataProd = request.GET.get('dataProd', '')
        
        # Ordinamento
        sort = request.GET.get('sort', 'telaio')
        order = request.GET.get('order', 'asc')
        
        # Query base
        veicoli = Veicolo.objects.all()
        
        # Applicazione filtri
        if telaio:
            veicoli = veicoli.filter(telaio__icontains=telaio)
        if marca:
            veicoli = veicoli.filter(marca__icontains=marca)
        if modello:
            veicoli = veicoli.filter(modello__icontains=modello)
        if dataProd:
            veicoli = veicoli.filter(dataProd=dataProd)
        
        # Ordinamento
        if order == 'desc':
            sort = f'-{sort}'
        
        # Mapping dei campi per ordinamento
        sort_mapping = {
            'telaio': 'telaio',
            'marca': 'marca',
            'modello': 'modello',
            'dataProd': 'dataProd',
            '-dataProd': '-dataProd'
        }
        
        if sort in sort_mapping:
            veicoli = veicoli.order_by(sort_mapping[sort])
        else:
            veicoli = veicoli.order_by(sort)
        
        # Serializzazione
        data = []
        for veicolo in veicoli:
            data.append({
                'telaio': veicolo.telaio,
                'marca': veicolo.marca,
                'modello': veicolo.modello,
                'dataProd': veicolo.dataProd.strftime('%Y-%m-%d'),
            })
        
        columns = [
            {'name': 'telaio', 'label': 'Telaio', 'isLink': True, 'linkTarget': 'veicoli'},
            {'name': 'marca', 'label': 'Marca'},
            {'name': 'modello', 'label': 'Modello'},
            {'name': 'dataProd', 'label': 'Data Produzione', 'type': 'date'},
        ]
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'columns': columns
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def add_veicolo_api(request):
    """API per aggiungere nuovo veicolo (compatibile con AJAX frontend PHP)"""
    try:
        # Gestione dati da form-data o JSON
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        # Validazione dati
        required_fields = ['telaio', 'marca', 'modello', 'dataProd']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'status': 'error',
                    'message': f'Campo {field} obbligatorio'
                }, status=400)
        
        # Verifica unicità telaio
        if Veicolo.objects.filter(telaio=data['telaio']).exists():
            return JsonResponse({
                'status': 'error',
                'message': 'Numero di telaio già esistente'
            }, status=400)
        
        # Creazione veicolo
        veicolo = Veicolo.objects.create(
            telaio=data['telaio'],
            marca=data['marca'],
            modello=data['modello'],
            dataProd=data['dataProd']
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Veicolo aggiunto con successo'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@require_http_methods(["GET"])
def get_veicolo_detail_api(request, telaio):
    """API per ottenere dettagli singolo veicolo"""
    try:
        veicolo = get_object_or_404(Veicolo, telaio=telaio)
        
        data = {
            'telaio': veicolo.telaio,
            'marca': veicolo.marca,
            'modello': veicolo.modello,
            'dataProd': veicolo.dataProd.strftime('%Y-%m-%d')
        }
        
        return JsonResponse({
            'status': 'success',
            'data': data
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def update_veicolo_api(request, telaio):
    """API per aggiornare veicolo esistente"""
    try:
        veicolo = get_object_or_404(Veicolo, telaio=telaio)
        
        # Gestione dati da form-data o JSON
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        # Aggiornamento campi
        if 'marca' in data:
            veicolo.marca = data['marca']
        if 'modello' in data:
            veicolo.modello = data['modello']
        if 'dataProd' in data:
            veicolo.dataProd = data['dataProd']
        
        # Gestione cambio telaio
        if 'telaio' in data and data['telaio'] != veicolo.telaio:
            # Verifica unicità nuovo telaio
            if Veicolo.objects.filter(telaio=data['telaio']).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Numero di telaio già esistente'
                }, status=400)
            veicolo.telaio = data['telaio']
        
        veicolo.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Veicolo aggiornato con successo'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def delete_veicolo_api(request, telaio):
    """API per eliminare veicolo"""
    try:
        veicolo = get_object_or_404(Veicolo, telaio=telaio)
        veicolo.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Veicolo eliminato con successo'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

# =============================================================================
# TARGHE VIEWS
# =============================================================================

class TargaListView(ListView):
    model = Targa
    template_name = 'pages/targa.html'
    context_object_name = 'targhe'
    paginate_by = 20
    
    def get_queryset(self):
        qs = super().get_queryset()
        for field, cfg in FIELD_CONFIG.items():
            val = self.request.GET.get(field)
            if val:
                lookup = field if cfg['input_type']=='date' else f"{field}__icontains"
                qs = qs.filter(**{lookup: val})
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Gestione Targhe'
        current = {f: self.request.GET.get(f, '') for f in TARGA_FIELDS}

        # build list of field‑configs including the current value
        ctx['filter_fields'] = []
        for f in TARGA_FIELDS:
            if f in FIELD_CONFIG:
                cfg = FIELD_CONFIG[f].copy()
                cfg.update(name=f, value=current[f])
                ctx['filter_fields'].append(cfg)

        return ctx

class TargaAttivaListView(ListView):
    model = TargaAttiva
    template_name = 'pages/targa_attiva.html'
    context_object_name = 'targhe_attive'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        for field, cfg in FIELD_CONFIG.items():
            val = self.request.GET.get(field)
            if val:
                lookup = field if cfg['input_type']=='date' else f"{field}__icontains"
                qs = qs.filter(**{lookup: val})
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Gestione Targhe Attive'
        current = {f: self.request.GET.get(f, '') for f in TARGA_ATTIVA_FIELDS}

        # build list of field‑configs including the current value
        ctx['filter_fields'] = []
        for f in TARGA_ATTIVA_FIELDS:
            if f in FIELD_CONFIG:
                cfg = FIELD_CONFIG[f].copy()
                cfg.update(name=f, value=current[f])
                ctx['filter_fields'].append(cfg)

        return ctx

@require_http_methods(["GET"])
def get_targhe_data(request):
    """API per ottenere dati targhe con filtri"""
    try:
        # Parametri filtro
        numero = request.GET.get('numero', '')
        dataEm = request.GET.get('dataEm', '')
        stato = request.GET.get('stato', '')
        
        # Ordinamento
        sort = request.GET.get('sort', 'numero')
        order = request.GET.get('order', 'asc')
        
        # Query base con JOIN per stato
        targhe = Targa.objects.all()
        
        # Applicazione filtri
        if numero:
            targhe = targhe.filter(numero__icontains=numero)
        if dataEm:
            targhe = targhe.filter(dataEm=dataEm)
        
        # Ordinamento
        if order == 'desc':
            sort = f'-{sort}'
        targhe = targhe.order_by(sort)
        
        # Serializzazione con stato
        data = []
        for targa in targhe:
            stato_targa = targa.stato
            if not stato or stato_targa == stato:
                data.append({
                    'numero': targa.numero,
                    'dataEm': targa.dataEm.strftime('%Y-%m-%d'),
                    'stato': stato_targa
                })
        
        columns = [
            {'name': 'numero', 'label': 'Numero', 'isLink': True, 'linkTarget': 'targhe'},
            {'name': 'dataEm', 'label': 'Data Emissione', 'type': 'date'},
            {'name': 'stato', 'label': 'Stato', 'type': 'status'}
        ]
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'columns': columns
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@require_http_methods(["GET"])
def table_api(request):
    table   = request.GET.get('table', '')
    sort    = request.GET.get('sort')
    order   = request.GET.get('order', 'asc').lower()
    order   = '-' if order == 'desc' else ''

    try:
        data = []
        columns = []

        if table == 'veicolo':
            qs = Veicolo.objects.all()

            # filters
            if telaio := request.GET.get('telaio'):
                qs = qs.filter(telaio__icontains=telaio)
            if marca := request.GET.get('marca'):
                qs = qs.filter(marca__icontains=marca)
            if modello := request.GET.get('modello'):
                qs = qs.filter(modello__icontains=modello)
            if dataProd := request.GET.get('dataProd'):
                qs = qs.filter(dataProd=dataProd)

            # sorting
            if sort:
                qs = qs.order_by(f"{order}{sort}")

            # serialize
            data = list(qs.values('telaio', 'marca', 'modello', 'dataProd'))

            # columns definition
            columns = [
                {'name':'telaio','label':'Telaio','isLink':True,'linkTarget':'veicoli'},
                {'name':'marca','label':'Marca'},
                {'name':'modello','label':'Modello'},
                {'name':'dataProd','label':'Data Produzione','type':'date'},
            ]

        elif table == 'targa':
            # annotate stato with CASE
            qs = (
                Targa.objects
                .annotate(
                    stato=Case(
                        When(targaattiva__isnull=False,   then=Value('Attiva')),
                        When(targarestituita__isnull=False, then=Value('Restituita')),
                        default=Value('Non assegnata'),
                        output_field=CharField()
                    )
                )
            )

            if numero := request.GET.get('numero'):
                qs = qs.filter(numero__icontains=numero)
            if dataEm := request.GET.get('dataEm'):
                qs = qs.filter(dataEm=dataEm)
            if stato := request.GET.get('stato'):
                qs = qs.filter(stato=stato)

            if sort:
                qs = qs.order_by(f"{order}{sort}")

            data = list(qs.values('numero', 'dataEm', 'stato'))

            columns = [
                {'name':'numero','label':'Numero','isLink':True,'linkTarget':'targhe'},
                {'name':'dataEm','label':'Data Emissione','type':'date'},
                {'name':'stato','label':'Stato','type':'status'},
            ]

        elif table == 'revisione':
            qs = Revisione.objects.all()

            if numero := request.GET.get('numero'):
                qs = qs.filter(numero__icontains=numero)
            if targa := request.GET.get('targa'):
                qs = qs.filter(targa__numero__icontains=targa)
            if dataRev := request.GET.get('dataRev'):
                qs = qs.filter(dataRev=dataRev)
            if esito := request.GET.get('esito'):
                qs = qs.filter(esito=esito)
            if motivazione := request.GET.get('motivazione'):
                qs = qs.filter(motivazione__icontains=motivazione)

            if sort:
                qs = qs.order_by(f"{order}{sort}")

            data = list(qs.values('numero', 'targa', 'dataRev', 'esito', 'motivazione'))

            columns = [
                {'name':'numero','label':'Numero'},
                {'name':'targa','label':'Targa','isLink':True,'linkTarget':'targhe'},
                {'name':'dataRev','label':'Data Revisione','type':'date'},
                {'name':'esito','label':'Esito'},
                {'name':'motivazione','label':'Motivazione'},
            ]

        elif table == 'targa_attiva':
            qs = (
                TargaAttiva.objects
                .select_related('targa','veicolo')
                .all()
            )
            if targa := request.GET.get('targa'):
                qs = qs.filter(targa__numero__icontains=targa)
            if veicolo := request.GET.get('veicolo'):
                qs = qs.filter(veicolo__telaio__icontains=veicolo)
            if dataEm := request.GET.get('dataEm'):
                qs = qs.filter(targa__dataEm=dataEm)

            if sort:
                qs = qs.order_by(f"{order}{sort}")
                
            # annotate joins
            data = []
            for ta in qs:
                data.append({
                    'targa':   ta.targa.numero,
                    'veicolo': ta.veicolo.telaio,
                    'marca':   ta.veicolo.marca,
                    'modello': ta.veicolo.modello,
                    'dataEm':  ta.targa.dataEm,
                })

            columns = [
                {'name':'targa','label':'Targa','isLink':True,'linkTarget':'targhe'},
                {'name':'veicolo','label':'Telaio Veicolo','isLink':True,'linkTarget':'veicoli'},
                {'name':'marca','label':'Marca'},
                {'name':'modello','label':'Modello'},
                {'name':'dataEm','label':'Data Emissione','type':'date'},
            ]

        elif table == 'targa_restituita':
            qs = (
                TargaRestituita.objects
                .select_related('targa','veicolo')
                .all()
            )
            
            if targa := request.GET.get('targa'):
                qs = qs.filter(targa__numero__icontains=targa)
            if veicolo := request.GET.get('veicolo'):
                qs = qs.filter(veicolo__telaio__icontains=veicolo)
            if dataEm := request.GET.get('dataEm'):
                qs = qs.filter(targa__dataEm=dataEm)
            if dataRes := request.GET.get('dataRes'):
                qs = qs.filter(dataRes=dataRes)

            if sort:
                qs = qs.order_by(f"{order}{sort}")

            data = []
            for tr in qs:
                data.append({
                    'targa':   tr.targa.numero,
                    'veicolo': tr.veicolo.telaio,
                    'marca':   tr.veicolo.marca,
                    'modello': tr.veicolo.modello,
                    'dataEm':  tr.targa.dataEm,
                    'dataRes': tr.dataRes,
                })

            columns = [
                {'name':'targa','label':'Targa','isLink':True,'linkTarget':'targhe'},
                {'name':'veicolo','label':'Telaio Veicolo','isLink':True,'linkTarget':'veicoli'},
                {'name':'marca','label':'Marca'},
                {'name':'modello','label':'Modello'},
                {'name':'dataEm','label':'Data Emissione','type':'date'},
                {'name':'dataRes','label':'Data Restituzione','type':'date'},
            ]

        else:
            return HttpResponseBadRequest(
                JsonResponse({'status':'error','message':'Tabella non valida'})
            )

        return JsonResponse({
            'status':  'success',
            'data':    data,
            'columns': columns
        }, json_dumps_params={'ensure_ascii': False})

    except Exception as e:
        return JsonResponse({
            'status':  'error',
            'message': str(e)
        }, status=500)
# =============================================================================
# ALTRE VIEWS (Revisioni, TargheAttive, TargheRestituite)
# =============================================================================

class RevisioneListView(ListView):
    model = Revisione
    template_name = 'pages/revisione.html'
    context_object_name = 'revisioni'
    paginate_by = 20
    
    def get_queryset(self):
        qs = super().get_queryset()
        for field, cfg in FIELD_CONFIG.items():
            val = self.request.GET.get(field)
            if val:
                lookup = field if cfg['input_type']=='date' else f"{field}__icontains"
                qs = qs.filter(**{lookup: val})
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Gestione Revisioni'
        current = {f: self.request.GET.get(f, '') for f in REVISIONE_FIELDS}

        # build list of field‑configs including the current value
        ctx['filter_fields'] = []
        for f in REVISIONE_FIELDS:
            if f in FIELD_CONFIG:
                cfg = FIELD_CONFIG[f].copy()
                cfg.update(name=f, value=current[f])
                ctx['filter_fields'].append(cfg)

        return ctx

class TargaRestituitaListView(ListView):
    model = TargaRestituita
    template_name = 'pages/targa_restituita.html'
    context_object_name = 'targhe_restituite'
    paginate_by = 20
    
    def get_queryset(self):
        qs = super().get_queryset()
        for field, cfg in FIELD_CONFIG.items():
            val = self.request.GET.get(field)
            if val:
                lookup = field if cfg['input_type']=='date' else f"{field}__icontains"
                qs = qs.filter(**{lookup: val})
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Gestione  Restituite'
        current = {f: self.request.GET.get(f, '') for f in TARGA_RESTITUITA_FIELDS}

        # build list of field‑configs including the current value
        ctx['filter_fields'] = []
        for f in TARGA_RESTITUITA_FIELDS:
            if f in FIELD_CONFIG:
                cfg = FIELD_CONFIG[f].copy()
                cfg.update(name=f, value=current[f])
                ctx['filter_fields'].append(cfg)

        return ctx

# =============================================================================
# AUTH VIEWS CUSTOM
# =============================================================================

def lista_veicoli(request):
    filter_fields = [
        'telaio', 'marca', 'modello', 'dataProd',
        'numero', 'dataEm', 'stato', 'targa',
        'veicolo', 'dataRev', 'dataRes', 'esito', 'motivazione'
    ]
    return render(request, 'your_app/filters.html', {
        'filter_fields': filter_fields
    })
    
