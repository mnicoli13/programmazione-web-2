import re
import logging
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseServerError
from django.views.decorators.http import require_http_methods, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.db.models import Case, When, Value, CharField

from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model, authenticate, login
from django.utils import timezone
from django.db import IntegrityError, transaction, DatabaseError, connection
import json
from datetime import datetime

from .models import Veicolo, Targa, Revisione, TargaAttiva, TargaRestituita
from .forms import VeicoloForm

logger = logging.getLogger(__name__)

# Homepage View
@login_required
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

class VeicoloListView(LoginRequiredMixin, ListView):
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

class VeicoloDetailView(LoginRequiredMixin, DetailView):
    model = Veicolo
    template_name = 'pages/veicoli/detail.html'
    context_object_name = 'veicolo'

class VeicoloCreateView(LoginRequiredMixin, CreateView):
    model = Veicolo
    form_class = VeicoloForm
    template_name = 'pages/veicoli/form.html'
    success_url = reverse_lazy('veicoli_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Veicolo aggiunto con successo!')
        return super().form_valid(form)

class VeicoloUpdateView(LoginRequiredMixin, UpdateView):
    model = Veicolo
    form_class = VeicoloForm
    template_name = 'pages/veicoli/form.html'
    success_url = reverse_lazy('veicoli_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Veicolo modificato con successo!')
        return super().form_valid(form)

class VeicoloDeleteView(LoginRequiredMixin, DeleteView):
    model = Veicolo
    template_name = 'pages/veicoli/confirm_delete.html'
    success_url = reverse_lazy('veicoli_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Veicolo eliminato con successo!')
        return super().delete(request, *args, **kwargs)

# =============================================================================
# API VIEWS per AJAX (compatibilità con frontend PHP)
# =============================================================================

@login_required
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


@login_required
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


@login_required
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


@login_required
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


@login_required
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

class TargaListView(LoginRequiredMixin, ListView):
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

@login_required
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

@login_required
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

class RevisioneListView(LoginRequiredMixin, ListView):
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


class TargaRestituitaListView(LoginRequiredMixin, ListView):
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

User = get_user_model()

@require_POST
def auto_login(request):
    user_id = request.POST.get('user_id')
    if not user_id:
        return JsonResponse({'success': False, 'message': 'ID utente mancante'}, status=400)

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Utente non trovato'}, status=404)

    # Aggiorna last_login
    user.last_login = timezone.now()
    user.save(update_fields=['last_login'])

    # Effettua il login (popola session)
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)

    response_data = {
        'success': True,
        'message': 'Auto‑login effettuato con successo',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
        }
    }
    return JsonResponse(response_data)

@require_POST
def api_login(request):
    """
    POST params:
      - username: può essere nome utente o email
      - password
      - remember: opzionale, 'on' o 'true' per sessione lunga
    """
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    remember = request.POST.get('remember') in ('on', 'true', '1')

    # 400: campi mancanti
    if not username or not password:
        return JsonResponse(
            {'success': False, 'message': 'Nome utente e password sono obbligatori'},
            status=400
        )

    # Decidiamo se è un'email
    is_email = bool(re.match(r'^[^@]+@[^@]+\.[^@]+$', username))

    user = None
    if is_email:
        try:
            return JsonResponse(
                {'success': False, 'message': username},
                status=401
            )
            # cerchiamo l’utente con quell’email
            user_obj = User.objects.get(email__iexact=username)
            
        except User.DoesNotExist:
            return JsonResponse(
                {'success': False, 'message': 'Nome utente o password non validi'},
                status=401
            )
        # autentichiamo usando lo username effettivo
        user = authenticate(request,
                            username=user_obj.get_username(),
                            password=password)
    else:
        # login via username
        user = authenticate(request, username=username, password=password)

    if user is None:
        # 401: credenziali sbagliate
        return JsonResponse(
            {'success': False, 'message': 'Nome utente o password non validi'},
            status=401
        )

    # aggiorniamo last_login
    user.last_login = timezone.now()
    user.save(update_fields=['last_login'])

    # effettuiamo il login (popola session)
    login(request, user)

    # se “remember me” è selezionato, la sessione dura 30 giorni
    if remember:
        request.session.set_expiry(60 * 60 * 24 * 30)
    else:
        # default: sessione fino alla chiusura del browser
        request.session.set_expiry(0)

    # prepariamo i dati (senza password)
    user_data = {
        'id': user.id,
        'username': user.get_username(),
        'email': user.email,
    }

    return JsonResponse({
        'success': True,
        'message': 'Login effettuato con successo',
        'user': user_data
    }, status=200)
    
@require_POST
def api_register(request):
    """
    POST params:
      - username
      - email
      - password
      - confirm_password
      - terms (expected truthy, es. 'on' o 'true')
    """
    data = request.POST
    required = ['username', 'email', 'password', 'confirm_password', 'terms']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return JsonResponse({
            'success': False,
            'message': 'I seguenti campi sono obbligatori: ' + ', '.join(missing)
        }, status=400)

    username = data['username'].strip()
    email = data['email'].strip()
    password = data['password']
    confirm = data['confirm_password']
    terms = data['terms']

    # Username: almeno 4 e solo [A-Za-z0-9_]
    if len(username) < 4:
        return JsonResponse({'success': False,
                             'message': 'Il nome utente deve contenere almeno 4 caratteri'},
                            status=400)
    if not re.fullmatch(r'[A-Za-z0-9_]+', username):
        return JsonResponse({'success': False,
                             'message': 'Il nome utente può contenere solo lettere, numeri e underscore'},
                            status=400)

    # Email valida
    if not re.fullmatch(r'[^@]+@[^@]+\.[^@]+', email):
        return JsonResponse({'success': False,
                             'message': 'Indirizzo email non valido'},
                            status=400)

    # Password minimo 8 e conferma
    if len(password) < 8:
        return JsonResponse({'success': False,
                             'message': 'La password deve contenere almeno 8 caratteri'},
                            status=400)
    if password != confirm:
        return JsonResponse({'success': False,
                             'message': 'Le password non corrispondono'},
                            status=400)

    # “Terms” deve essere truthy
    if terms not in ('on', 'true', '1'):
        return JsonResponse({'success': False,
                             'message': 'Devi accettare i termini'},
                            status=400)

    # Controllo unicità username/email e creazione utente
    try:
        with transaction.atomic():
            # create_user gestisce hashing password e last_login di default
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
            )
            # Imposta created_at se lo usi (altrimenti è gestito da auto_now_add)
            if hasattr(user, 'created_at'):
                user.created_at = timezone.now()
                user.save(update_fields=['created_at'])
    except IntegrityError as e:
        # Assumiamo che IntegrityError arrivi per duplicate fields
        if User.objects.filter(username__iexact=username).exists():
            msg = 'Nome utente già in uso'
        elif User.objects.filter(email__iexact=email).exists():
            msg = 'Email già registrata'
        else:
            msg = 'Errore durante la registrazione'
        return JsonResponse({'success': False, 'message': msg}, status=400)
    except Exception as e:
        return JsonResponse({'success': False,
                             'message': f'Errore nella registrazione: {str(e)}'},
                            status=500)

    return JsonResponse({
        'success': True,
        'message': 'Registrazione completata con successo'
    }, status=200)

logger = logging.getLogger(__name__)

@require_POST
def api_check_username(request):
    """
    POST params:
      - username
    Risponde con JSON: { available: true/false }
    """
    username = request.POST.get('username', '').strip()
    if not username:
        return JsonResponse(
            {'error': 'Nome utente mancante', 'available': False},
            status=400
        )

    try:
        # Conta quanti utenti hanno quel username (case‐insensitive)
        exists = User.objects.filter(username__iexact=username).exists()
        return JsonResponse({'available': not exists}, status=200)

    except DatabaseError as e:
        logger.error("Errore DB in check_username: %s", e)
        return JsonResponse(
            {'error': 'db_error', 'message': str(e), 'available': False},
            status=500
        )

@require_POST
def api_check_email(request):
    email = request.POST.get('email', '').strip()

    if not email:
        return JsonResponse({'error': 'Email mancante', 'available': False})

    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM Utenti WHERE email = %s", [email])
        count = cursor.fetchone()[0]

    return JsonResponse({'available': count == 0})


def lista_veicoli(request):
    filter_fields = [
        'telaio', 'marca', 'modello', 'dataProd',
        'numero', 'dataEm', 'stato', 'targa',
        'veicolo', 'dataRev', 'dataRes', 'esito', 'motivazione'
    ]
    return render(request, 'your_app/filters.html', {
        'filter_fields': filter_fields
    })
    
