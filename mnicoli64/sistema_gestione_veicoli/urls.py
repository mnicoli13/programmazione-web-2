from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Veicoli - Views standard
    path('veicoli/', views.VeicoloListView.as_view(), name='veicoli_list'),
    path('veicoli/add/', views.VeicoloCreateView.as_view(), name='veicoli_add'),
    path('veicoli/<str:pk>/', views.VeicoloDetailView.as_view(), name='veicolo_detail'),
    path('veicoli/<str:pk>/edit/', views.VeicoloUpdateView.as_view(), name='veicolo_edit'),
    path('veicoli/<str:pk>/delete/', views.VeicoloDeleteView.as_view(), name='veicolo_delete'),
    
    # Veicoli - API per AJAX (compatibilità con frontend PHP)
    path('api/veicoli/', views.get_veicoli_data, name='veicoli_api'),
    path('api/veicoli/add/', views.add_veicolo_api, name='add_veicolo_api'),
    path('api/veicoli/<str:telaio>/detail/', views.get_veicolo_detail_api, name='get_veicolo_api'),
    path('api/veicoli/<str:telaio>/update/', views.update_veicolo_api, name='update_veicolo_api'),
    path('api/veicoli/<str:telaio>/delete/', views.delete_veicolo_api, name='delete_veicolo_api'),
    
    # Targhe
    path('targhe/', views.TargaListView.as_view(), name='targhe_list'),
    path('api/targhe/', views.get_targhe_data, name='targhe_api'),
    
    # Revisioni
    path('revisioni/', views.RevisioneListView.as_view(), name='revisioni_list'),
    
    # Targhe Attive
    path('targhe-attive/', views.TargaAttivaListView.as_view(), name='targhe_attive_list'),
    
    # Targhe Restituite
    path('targhe-restituite/', views.TargaRestituitaListView.as_view(), name='targhe_restituite_list'),
    
    path('api/table/', views.table_api, name='api-table'),
]