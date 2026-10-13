from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/", views.dashboard),
    path("products/", views.products),
    path("products/export/", views.export_products),
    path("products/<int:pk>/", views.product_detail),
    path("products/<int:pk>/link/", views.link_supplier),
    path("products/<int:pk>/link/<int:fid>/", views.unlink_supplier),
    path("suppliers/", views.suppliers),
    path("suppliers/export/", views.export_suppliers),
    path("suppliers/<int:pk>/", views.supplier_detail),
]
