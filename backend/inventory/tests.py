import json
from datetime import date, timedelta

from django.test import TestCase

from .models import Fornecedor, Produto, Vinculo

HOJE = date.today()


def make_produto(**kwargs):
    defaults = {
        "nome": "Arroz 5kg",
        "categoria": "alimento",
        "data_compra": HOJE - timedelta(days=10),
        "validade": HOJE + timedelta(days=90),
        "preco": 25.50,
        "descricao": "Arroz branco",
        "estoque": 40,
    }
    defaults.update(kwargs)
    return Produto.objects.create(**defaults)


class ProductApiTests(TestCase):
    def test_list_products(self):
        make_produto()
        response = self.client.get("/api/products/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["results"]), 1)
        produto = data["results"][0]
        self.assertEqual(produto["nome"], "Arroz 5kg")
        self.assertEqual(produto["status"], "ok")
        self.assertEqual(produto["fornecedores"], [])

    def test_create_product(self):
        payload = {
            "nome": "Feijão 1kg",
            "categoria": "alimento",
            "data_compra": HOJE.isoformat(),
            "validade": (HOJE + timedelta(days=60)).isoformat(),
            "preco": 8.90,
            "descricao": "Feijão carioca",
            "estoque": 15,
        }
        response = self.client.post(
            "/api/products/", data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["nome"], "Feijão 1kg")
        self.assertEqual(data["estoque"], 15)
        self.assertTrue(Produto.objects.filter(nome="Feijão 1kg").exists())

    def test_create_product_without_name_is_rejected(self):
        response = self.client.post(
            "/api/products/", data=json.dumps({}), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.json())

    def test_update_product(self):
        produto = make_produto()
        response = self.client.patch(
            f"/api/products/{produto.pk}/",
            data=json.dumps({"estoque": 5, "preco": 30.00}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        produto.refresh_from_db()
        self.assertEqual(produto.estoque, 5)
        self.assertEqual(float(produto.preco), 30.00)

    def test_delete_product(self):
        produto = make_produto()
        response = self.client.delete(f"/api/products/{produto.pk}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Produto.objects.filter(pk=produto.pk).exists())

    def test_status_transitions(self):
        vencido = make_produto(nome="Iogurte vencido", validade=HOJE - timedelta(days=1))
        proximo = make_produto(nome="Iogurte próximo", validade=HOJE + timedelta(days=10))
        ok = make_produto(nome="Iogurte ok", validade=HOJE + timedelta(days=60))
        statuses = {p.pk: p for p in (vencido, proximo, ok)}
        response = self.client.get("/api/products/")
        results = {item["id"]: item["status"] for item in response.json()["results"]}
        self.assertEqual(results[vencido.pk], "vencido")
        self.assertEqual(results[proximo.pk], "proximo")
        self.assertEqual(results[ok.pk], "ok")

    def test_filter_by_status(self):
        make_produto(nome="Vencido", validade=HOJE - timedelta(days=2))
        make_produto(nome="No prazo", validade=HOJE + timedelta(days=120))
        response = self.client.get("/api/products/?status=vencido")
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["nome"], "Vencido")

    def test_filter_low_stock(self):
        make_produto(nome="Queijo", estoque=3)
        make_produto(nome="Leite", estoque=100)
        response = self.client.get("/api/products/?status=estoque_baixo&threshold=10")
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["nome"], "Queijo")

    def test_search_by_name(self):
        make_produto(nome="Café torrado")
        make_produto(nome="Açúcar cristal")
        response = self.client.get("/api/products/?q=café")
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["nome"], "Café torrado")


class SupplierLinkTests(TestCase):
    def setUp(self):
        self.produto = make_produto()
        self.fornecedor = Fornecedor.objects.create(nome="Distribuidora Centro")

    def test_link_and_unlink_supplier(self):
        response = self.client.post(
            f"/api/products/{self.produto.pk}/link/",
            data=json.dumps({"supplier_id": self.fornecedor.pk}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["fornecedores"][0]["nome"], "Distribuidora Centro")
        self.assertEqual(Vinculo.objects.count(), 1)

        response = self.client.delete(
            f"/api/products/{self.produto.pk}/link/{self.fornecedor.pk}/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["fornecedores"], [])
        self.assertEqual(Vinculo.objects.count(), 0)

    def test_link_is_idempotent(self):
        for _ in range(2):
            self.client.post(
                f"/api/products/{self.produto.pk}/link/",
                data=json.dumps({"supplier_id": self.fornecedor.pk}),
                content_type="application/json",
            )
        self.assertEqual(Vinculo.objects.count(), 1)

    def test_link_unknown_supplier_returns_404(self):
        response = self.client.post(
            f"/api/products/{self.produto.pk}/link/",
            data=json.dumps({"supplier_id": 9999}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)


class SupplierApiTests(TestCase):
    def test_create_and_list_suppliers(self):
        payload = {"nome": "Atacado Sul", "endereco": "Rua A, 100", "contato": "(85) 99999-0000"}
        response = self.client.post(
            "/api/suppliers/", data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["total_produtos"], 0)

        response = self.client.get("/api/suppliers/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 1)

    def test_create_supplier_without_name_is_rejected(self):
        response = self.client.post(
            "/api/suppliers/", data=json.dumps({}), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_update_supplier(self):
        fornecedor = Fornecedor.objects.create(nome="Velho Nome")
        response = self.client.patch(
            f"/api/suppliers/{fornecedor.pk}/",
            data=json.dumps({"nome": "Novo Nome"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        fornecedor.refresh_from_db()
        self.assertEqual(fornecedor.nome, "Novo Nome")

    def test_delete_supplier(self):
        fornecedor = Fornecedor.objects.create(nome="Para excluir")
        response = self.client.delete(f"/api/suppliers/{fornecedor.pk}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Fornecedor.objects.filter(pk=fornecedor.pk).exists())

    def test_supplier_lists_linked_products(self):
        fornecedor = Fornecedor.objects.create(nome="Hortifruti")
        produto = make_produto(nome="Tomate")
        Vinculo.objects.create(produto=produto, fornecedor=fornecedor)
        response = self.client.get(f"/api/suppliers/{fornecedor.pk}/")
        data = response.json()
        self.assertEqual(data["total_produtos"], 1)
        self.assertEqual(data["produtos"][0]["nome"], "Tomate")


class DashboardTests(TestCase):
    def test_dashboard_summary(self):
        Fornecedor.objects.create(nome="Fornecedor 1")
        make_produto(nome="Vencido", validade=HOJE - timedelta(days=1), estoque=2)
        make_produto(nome="A vencer", validade=HOJE + timedelta(days=5), estoque=100)
        make_produto(nome="No prazo", validade=HOJE + timedelta(days=200), estoque=50)

        response = self.client.get("/api/dashboard/?threshold=10")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["resumo"]["produtos"], 3)
        self.assertEqual(data["resumo"]["fornecedores"], 1)
        self.assertEqual(data["resumo"]["vencidos"], 1)
        self.assertEqual(data["resumo"]["vencendo"], 1)
        self.assertEqual(data["resumo"]["estoque_baixo"], 1)
        self.assertEqual(data["validade"], {"vencido": 1, "proximo": 1, "ok": 1})
        self.assertEqual(data["estoque_baixo_lista"][0]["nome"], "Vencido")


class ExportTests(TestCase):
    def test_export_products_csv(self):
        fornecedor = Fornecedor.objects.create(nome="Distribuidora")
        produto = make_produto(nome="Macarrão 500g")
        Vinculo.objects.create(produto=produto, fornecedor=fornecedor)

        response = self.client.get("/api/products/export/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])
        content = response.content.decode("utf-8-sig")
        self.assertIn("Macarrão 500g", content)
        self.assertIn("Distribuidora", content)

    def test_export_suppliers_csv(self):
        Fornecedor.objects.create(nome="Atacado Norte")
        response = self.client.get("/api/suppliers/export/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Atacado Norte", response.content.decode("utf-8-sig"))


class SeedCommandTests(TestCase):
    def test_seed_demo_populates_database(self):
        from django.core.management import call_command

        call_command("seed_demo")
        self.assertEqual(Produto.objects.count(), 13)
        self.assertEqual(Fornecedor.objects.count(), 3)
        self.assertEqual(Vinculo.objects.count(), 9)

        call_command("seed_demo")
        self.assertEqual(Produto.objects.count(), 13)
