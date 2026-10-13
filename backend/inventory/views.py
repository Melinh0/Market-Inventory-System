import csv
import json
from datetime import date, timedelta

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Fornecedor, Produto, Vinculo

DIAS_PROXIMO = 30
ESTOQUE_MINIMO_PADRAO = 25


def _body(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return {}


def _status(produto, hoje=None):
    hoje = hoje or date.today()
    if produto.validade < hoje:
        return "vencido"
    if produto.validade <= hoje + timedelta(days=DIAS_PROXIMO):
        return "proximo"
    return "ok"


def produto_dict(produto):
    return {
        "id": produto.pk,
        "nome": produto.nome,
        "categoria": produto.categoria,
        "data_compra": produto.data_compra.isoformat(),
        "validade": produto.validade.isoformat(),
        "preco": float(produto.preco),
        "descricao": produto.descricao,
        "estoque": produto.estoque,
        "status": _status(produto),
        "fornecedores": [{"id": f.pk, "nome": f.nome} for f in produto.fornecedores.all()],
    }


def fornecedor_dict(fornecedor):
    produtos = list(fornecedor.produtos.all())
    return {
        "id": fornecedor.pk,
        "nome": fornecedor.nome,
        "endereco": fornecedor.endereco,
        "contato": fornecedor.contato,
        "produtos": [{"id": p.pk, "nome": p.nome} for p in produtos],
        "total_produtos": len(produtos),
    }


@csrf_exempt
@require_http_methods(["GET", "POST"])
def products(request):
    if request.method == "POST":
        data = _body(request)
        if not data.get("nome"):
            return JsonResponse({"detail": "Informe o nome do produto."}, status=400)
        produto = Produto.objects.create(
            nome=data["nome"],
            categoria=data.get("categoria") or "outros",
            data_compra=data.get("data_compra") or date.today().isoformat(),
            validade=data.get("validade") or date.today().isoformat(),
            preco=data.get("preco") or 0,
            descricao=data.get("descricao") or "",
            estoque=int(data.get("estoque") or 0),
        )
        produto = Produto.objects.prefetch_related("fornecedores").get(pk=produto.pk)
        return JsonResponse(produto_dict(produto), status=201)

    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    threshold = int(request.GET.get("threshold") or ESTOQUE_MINIMO_PADRAO)

    produtos = Produto.objects.prefetch_related("fornecedores")
    if query:
        produtos = produtos.filter(nome__icontains=query)

    itens = [produto_dict(p) for p in produtos]
    if status == "vencido":
        itens = [p for p in itens if p["status"] == "vencido"]
    elif status == "proximo":
        itens = [p for p in itens if p["status"] == "proximo"]
    elif status == "estoque_baixo":
        itens = [p for p in itens if p["estoque"] < threshold]

    return JsonResponse({"results": itens})


@csrf_exempt
@require_http_methods(["GET", "PATCH", "PUT", "DELETE"])
def product_detail(request, pk):
    produto = get_object_or_404(Produto.objects.prefetch_related("fornecedores"), pk=pk)

    if request.method == "DELETE":
        produto.delete()
        return JsonResponse({}, status=204)

    if request.method in ("PATCH", "PUT"):
        data = _body(request)
        for field in ("nome", "categoria", "data_compra", "validade", "preco", "descricao", "estoque"):
            if field in data:
                setattr(produto, field, data[field])
        produto.save()
        produto = Produto.objects.prefetch_related("fornecedores").get(pk=pk)

    return JsonResponse(produto_dict(produto))


@csrf_exempt
@require_http_methods(["POST"])
def link_supplier(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    data = _body(request)
    fornecedor = get_object_or_404(Fornecedor, pk=data.get("supplier_id"))
    Vinculo.objects.get_or_create(produto=produto, fornecedor=fornecedor)
    produto = Produto.objects.prefetch_related("fornecedores").get(pk=pk)
    return JsonResponse(produto_dict(produto))


@csrf_exempt
@require_http_methods(["DELETE"])
def unlink_supplier(request, pk, fid):
    produto = get_object_or_404(Produto, pk=pk)
    Vinculo.objects.filter(produto=produto, fornecedor_id=fid).delete()
    produto = Produto.objects.prefetch_related("fornecedores").get(pk=pk)
    return JsonResponse(produto_dict(produto))


@csrf_exempt
@require_http_methods(["GET", "POST"])
def suppliers(request):
    if request.method == "POST":
        data = _body(request)
        if not data.get("nome"):
            return JsonResponse({"detail": "Informe o nome do fornecedor."}, status=400)
        fornecedor = Fornecedor.objects.create(
            nome=data["nome"],
            endereco=data.get("endereco") or "",
            contato=data.get("contato") or "",
        )
        return JsonResponse(fornecedor_dict(fornecedor), status=201)

    fornecedores = Fornecedor.objects.prefetch_related("produtos")
    return JsonResponse({"results": [fornecedor_dict(f) for f in fornecedores]})


@csrf_exempt
@require_http_methods(["GET", "PATCH", "PUT", "DELETE"])
def supplier_detail(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)

    if request.method == "DELETE":
        fornecedor.delete()
        return JsonResponse({}, status=204)

    if request.method in ("PATCH", "PUT"):
        data = _body(request)
        for field in ("nome", "endereco", "contato"):
            if field in data:
                setattr(fornecedor, field, data[field])
        fornecedor.save()
        fornecedor = Fornecedor.objects.prefetch_related("produtos").get(pk=pk)

    return JsonResponse(fornecedor_dict(fornecedor))


@require_http_methods(["GET"])
def dashboard(request):
    hoje = date.today()
    produtos = list(Produto.objects.prefetch_related("fornecedores"))
    fornecedores = list(Fornecedor.objects.prefetch_related("produtos"))
    threshold = int(request.GET.get("threshold") or ESTOQUE_MINIMO_PADRAO)

    status_counts = {"vencido": 0, "proximo": 0, "ok": 0}
    por_categoria = {}
    for produto in produtos:
        status_counts[_status(produto, hoje)] += 1
        categoria = por_categoria.setdefault(
            produto.categoria, {"categoria": produto.categoria, "itens": 0, "estoque": 0, "valor": 0.0}
        )
        categoria["itens"] += 1
        categoria["estoque"] += produto.estoque
        categoria["valor"] += float(produto.preco) * produto.estoque

    ordenados = sorted(produtos, key=lambda p: float(p.preco) * p.estoque, reverse=True)
    top_valor = [
        {
            "nome": p.nome,
            "estoque": p.estoque,
            "valor": round(float(p.preco) * p.estoque, 2),
            "categoria": p.categoria,
        }
        for p in ordenados[:10]
    ]

    return JsonResponse(
        {
            "resumo": {
                "produtos": len(produtos),
                "fornecedores": len(fornecedores),
                "unidades": sum(p.estoque for p in produtos),
                "valor_estoque": round(sum(float(p.preco) * p.estoque for p in produtos), 2),
                "vencidos": status_counts["vencido"],
                "vencendo": status_counts["proximo"],
                "estoque_baixo": sum(1 for p in produtos if p.estoque < threshold),
                "vinculos": Vinculo.objects.count(),
            },
            "validade": status_counts,
            "categorias": sorted(por_categoria.values(), key=lambda c: c["valor"], reverse=True),
            "top_valor": top_valor,
            "fornecedores": [
                {"nome": f.nome, "produtos": len(list(f.produtos.all())), "id": f.pk}
                for f in fornecedores
            ],
            "estoque_baixo_lista": [
                {"nome": p.nome, "estoque": p.estoque, "id": p.pk}
                for p in sorted(produtos, key=lambda x: x.estoque)
                if p.estoque < threshold
            ],
        }
    )


@require_http_methods(["GET"])
def export_products(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="produtos.csv"'
    response.write("\ufeff")
    writer = csv.writer(response, delimiter=";")
    writer.writerow(["ID", "Nome", "Categoria", "Compra", "Validade", "Preco", "Estoque", "Fornecedores"])
    for produto in Produto.objects.prefetch_related("fornecedores"):
        writer.writerow(
            [
                produto.pk,
                produto.nome,
                produto.categoria,
                produto.data_compra,
                produto.validade,
                produto.preco,
                produto.estoque,
                ", ".join(f.nome for f in produto.fornecedores.all()),
            ]
        )
    return response


@require_http_methods(["GET"])
def export_suppliers(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="fornecedores.csv"'
    response.write("\ufeff")
    writer = csv.writer(response, delimiter=";")
    writer.writerow(["ID", "Nome", "Endereco", "Contato", "Produtos"])
    for fornecedor in Fornecedor.objects.prefetch_related("produtos"):
        writer.writerow(
            [
                fornecedor.pk,
                fornecedor.nome,
                fornecedor.endereco,
                fornecedor.contato,
                ", ".join(p.nome for p in fornecedor.produtos.all()),
            ]
        )
    return response
