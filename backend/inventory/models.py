from django.db import models


class Categoria(models.TextChoices):
    ALIMENTO = "alimento", "Alimento"
    LIMPEZA = "limpeza", "Limpeza"
    HIGIENE = "higiene", "Higiene"
    BEBIDA = "bebida", "Bebida"
    OUTROS = "outros", "Outros"


class Fornecedor(models.Model):
    nome = models.CharField(max_length=120)
    endereco = models.CharField(max_length=200, blank=True)
    contato = models.CharField(max_length=60, blank=True)

    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Produto(models.Model):
    nome = models.CharField(max_length=120)
    categoria = models.CharField(max_length=20, choices=Categoria.choices, default=Categoria.OUTROS)
    data_compra = models.DateField()
    validade = models.DateField()
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    descricao = models.CharField(max_length=255, blank=True)
    estoque = models.PositiveIntegerField(default=0)
    fornecedores = models.ManyToManyField(Fornecedor, through="Vinculo", related_name="produtos")

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Vinculo(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Vínculo"
        verbose_name_plural = "Vínculos"
        constraints = [models.UniqueConstraint(fields=["produto", "fornecedor"], name="vinculo_unico")]

    def __str__(self):
        return f"{self.produto} -> {self.fornecedor}"
