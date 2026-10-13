from django.contrib import admin

from .models import Fornecedor, Produto, Vinculo


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ["id", "nome", "categoria", "validade", "preco", "estoque"]
    list_filter = ["categoria"]
    search_fields = ["nome"]


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ["id", "nome", "endereco", "contato"]
    search_fields = ["nome"]


admin.site.register(Vinculo)
