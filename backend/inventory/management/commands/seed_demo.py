from datetime import date, timedelta

from django.core.management.base import BaseCommand

from backend.inventory.models import Fornecedor, Produto, Vinculo

PRODUTOS = [
    (219, "Sabão em pó Omo", "limpeza", 5.00, 10, -150, "Desengordura roupas brancas e coloridas"),
    (232, "Banana prata (kg)", "alimento", 3.00, 60, 8, "Fruta fresca da feira"),
    (333, "Manga rosa (kg)", "alimento", 3.00, 20, -30, "Fruta doce madura"),
    (410, "Chocolate Cacau Show 90g", "alimento", 10.50, 50, 180, "Chocolate meio amargo"),
    (411, "Chocolate Nestlé 80g", "alimento", 8.00, 80, 180, "Chocolate ao leite"),
    (444, "Pera (kg)", "alimento", 3.00, 40, -10, "Fruta europeia"),
    (555, "Detergente Ypê 500ml", "limpeza", 5.00, 50, 300, "Detergente neutro"),
    (667, "Mamão papaya (un)", "alimento", 4.00, 30, 15, "Fruta rica em fibras"),
    (678, "Pimentão verde (kg)", "alimento", 4.50, 45, -60, "Legume fresco"),
    (777, "Cebola (kg)", "alimento", 3.50, 80, 120, "Legume de longa conservação"),
    (778, "Melancia (kg)", "alimento", 5.00, 40, 5, "Fruta da estação"),
    (876, "Pimentão colorido (kg)", "alimento", 4.00, 40, -90, "Legume fresco"),
    (909, "Abacate (un)", "alimento", 4.00, 35, 20, "Fruta madura"),
]

FORNECEDORES = [
    (111, "Lucas", "Rua 7, 120 - Centro", "(85) 8888-1111"),
    (777, "Yago", "Rua UECE, s/n", "(85) 7777-6666"),
    (888, "Mauro", "Rua 3, 45 - Mercado", "(85) 4444-5555"),
]

VINCULOS = [
    (333, 888),
    (444, 111),
    (777, 777),
    (219, 111),
    (555, 888),
    (410, 777),
    (232, 777),
    (909, 111),
    (667, 777),
]


class Command(BaseCommand):
    help = "Popula o banco com os dados de demonstração do trabalho"

    def handle(self, *args, **options):
        if Produto.objects.exists() or Fornecedor.objects.exists():
            self.stdout.write("Banco já populado, seed ignorado.")
            return

        hoje = date.today()
        produtos = {}
        for pid, nome, categoria, preco, estoque, validade_offset, descricao in PRODUTOS:
            produto = Produto.objects.create(
                id=pid,
                nome=nome,
                categoria=categoria,
                data_compra=hoje - timedelta(days=abs(validade_offset) // 3 + 20),
                validade=hoje + timedelta(days=validade_offset),
                preco=preco,
                descricao=descricao,
                estoque=estoque,
            )
            produtos[pid] = produto

        fornecedores = {}
        for fid, nome, endereco, contato in FORNECEDORES:
            fornecedores[fid] = Fornecedor.objects.create(
                id=fid, nome=nome, endereco=endereco, contato=contato
            )

        for pid, fid in VINCULOS:
            Vinculo.objects.create(produto=produtos[pid], fornecedor=fornecedores[fid])

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed concluído: {len(produtos)} produtos, "
                f"{len(fornecedores)} fornecedores, {len(VINCULOS)} vínculos."
            )
        )
