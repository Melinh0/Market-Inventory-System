import tkinter as tk
from tkinter import simpledialog, messagebox
from SistemaInventario import Estoque
from tkinter.ttk import Treeview
import datetime
import matplotlib.pyplot as plt
import pandas as pd

class InterfaceGrafica:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Estoque")
        self.estoque = Estoque()

        self.label = tk.Label(root, text="Escolha uma opção:")
        self.label.pack()

        self.button_cadastrar_produto = tk.Button(root, text="Cadastrar Produto", command=self.cadastrar_produto)
        self.button_cadastrar_produto.pack()

        self.button_cadastrar_fornecedor = tk.Button(root, text="Cadastrar Fornecedor", command=self.cadastrar_fornecedor)
        self.button_cadastrar_fornecedor.pack()

        self.button_vincular_produto_a_fornecedor = tk.Button(root, text="Vincular Produto a Fornecedor", command=self.vincular_produto_a_fornecedor)
        self.button_vincular_produto_a_fornecedor.pack()

        self.button_desvincular_produto_de_fornecedor = tk.Button(root, text="Desvincular Produto de Fornecedor", command=self.desvincular_produto_de_fornecedor)
        self.button_desvincular_produto_de_fornecedor.pack()

        self.button_remover_produto = tk.Button(root, text="Remover Produto", command=self.remover_produto)
        self.button_remover_produto.pack()

        self.button_remover_fornecedor = tk.Button(root, text="Remover Fornecedor", command=self.remover_fornecedor)
        self.button_remover_fornecedor.pack()

        self.button_atualizar_estoque = tk.Button(root, text="Atualizar Estoque", command=self.atualizar_estoque)
        self.button_atualizar_estoque.pack()

        self.button_ver_tabela_produtos = tk.Button(root, text="Ver Tabela de Produtos Cadastrados", command=self.ver_tabela_produtos)
        self.button_ver_tabela_produtos.pack()

        self.button_ver_tabela_fornecedores = tk.Button(root, text="Ver Tabela de Fornecedores Cadastrados", command=self.ver_tabela_fornecedores)
        self.button_ver_tabela_fornecedores.pack()

        self.button_produtos_vencidos = tk.Button(root, text="Produtos Vencidos", command=self.produtos_vencidos)
        self.button_produtos_vencidos.pack()

        self.button_produtos_estoque_baixo = tk.Button(root, text="Produtos com Estoque Baixo", command=self.produtos_estoque_baixo)
        self.button_produtos_estoque_baixo.pack()

    def cadastrar_produto(self):
        nome_produto = simpledialog.askstring("Cadastrar Produto", "Nome do produto:")
        data_compra = simpledialog.askstring("Cadastrar Produto", "Data de compra (AAAA-MM-DD):")
        data_validade = simpledialog.askstring("Cadastrar Produto", "Data de validade (AAAA-MM-DD):")
        preco = float(simpledialog.askstring("Cadastrar Produto", "Preço:"))
        descricao = simpledialog.askstring("Cadastrar Produto", "Descrição:")
        estoque_inicial = int(simpledialog.askstring("Cadastrar Produto", "Estoque Inicial:"))
        
        if nome_produto and data_compra and data_validade:
            try:
                data_compra = datetime.datetime.strptime(data_compra, "%Y-%m-%d").date()
                data_validade = datetime.datetime.strptime(data_validade, "%Y-%m-%d").date()
                self.estoque.cadastro_produto(nome_produto, data_compra, data_validade, preco, descricao, estoque_inicial)
                messagebox.showinfo("Sucesso", f"Produto {nome_produto} cadastrado com sucesso.")
            except ValueError:
                messagebox.showerror("Erro", "Data em formato inválido.")
        else:
            messagebox.showerror("Erro", "Nome, data de compra e data de validade são obrigatórios.")

    def cadastrar_fornecedor(self):
        nome_fornecedor = simpledialog.askstring("Cadastrar Fornecedor", "Nome do fornecedor:")
        endereco_fornecedor = simpledialog.askstring("Cadastrar Fornecedor", "Endereço do fornecedor:")
        contato_fornecedor = simpledialog.askstring("Cadastrar Fornecedor", "Contato do fornecedor:")

        if nome_fornecedor:
            fornecedor = {
                'Nome': nome_fornecedor,
                'Endereco': endereco_fornecedor,
                'Contato': contato_fornecedor
            }
            self.estoque.cadastro_fornecedor(fornecedor)
            messagebox.showinfo("Sucesso", f"Fornecedor {nome_fornecedor} cadastrado com sucesso.")
        else:
            messagebox.showerror("Erro", "Nome do fornecedor é obrigatório.")

    def vincular_produto_a_fornecedor(self):
        produto_id = simpledialog.askinteger("Vincular Produto a Fornecedor", "ID do produto:")
        fornecedor_id = simpledialog.askinteger("Vincular Produto a Fornecedor", "ID do fornecedor:")
        if produto_id and fornecedor_id:
            self.estoque.vincular_produto_a_fornecedor(produto_id, fornecedor_id)
            produto = self.estoque.produtos.get(produto_id, {})
            fornecedor = self.estoque.fornecedores.get(fornecedor_id, {})
            messagebox.showinfo("Sucesso", f"Produto {produto.get('Nome')} vinculado ao fornecedor {fornecedor.get('Nome')} com sucesso.")
        else:
            messagebox.showerror("Erro", "ID do produto e do fornecedor são obrigatórios.")

    def desvincular_produto_de_fornecedor(self):
        produto_id = simpledialog.askinteger("Desvincular Produto de Fornecedor", "ID do produto:")
        fornecedor_id = simpledialog.askinteger("Desvincular Produto de Fornecedor", "ID do fornecedor:")
        if produto_id and fornecedor_id:
            self.estoque.desvincular_produto_de_fornecedor(produto_id, fornecedor_id)
            produto = self.estoque.produtos.get(produto_id, {})
            fornecedor = self.estoque.fornecedores.get(fornecedor_id, {})
            messagebox.showinfo("Sucesso", f"Produto {produto.get('Nome')} desvinculado do fornecedor {fornecedor.get('Nome')} com sucesso.")
        else:
            messagebox.showerror("Erro", "ID do produto e do fornecedor são obrigatórios.")

    def remover_produto(self):
        produto_id = simpledialog.askinteger("Remover Produto", "ID do produto a ser removido:")
        if produto_id:
            self.estoque.remover_produto(produto_id)
        else:
            messagebox.showerror("Erro", "ID do produto é obrigatório.")

    def remover_fornecedor(self):
        fornecedor_id = simpledialog.askinteger("Remover Fornecedor", "ID do fornecedor a ser removido:")
        if fornecedor_id:
            self.estoque.remover_fornecedor(fornecedor_id)
        else:
            messagebox.showerror("Erro", "ID do fornecedor é obrigatório.")

    def atualizar_estoque(self):
        produto_id = simpledialog.askinteger("Atualizar Estoque", "ID do produto:")
        quantidade = simpledialog.askinteger("Atualizar Estoque", "Quantidade a ser adicionada/retirada:")
        if produto_id and quantidade:
            self.estoque.atualizar_estoque(produto_id, quantidade)
            produto = self.estoque.produtos.get(produto_id, {})
            messagebox.showinfo("Sucesso", f"Estoque do produto {produto.get('Nome')} atualizado com sucesso.")
        else:
            messagebox.showerror("Erro", "ID do produto e quantidade são obrigatórios.")

    def ver_tabela_produtos(self):
        produtos = self.estoque.consultar_produtos_com_fornecedores()

        if not produtos:
            messagebox.showinfo("Tabela de Produtos Cadastrados", "Nenhum produto cadastrado.")
            return

        result = "Tabela de Produtos Cadastrados:\n\n"
        for produto in produtos:
            result += f"ID: {produto['ID_Produtos']}\n"
            result += f"Produto: {produto['Nome']}\n"
            result += f"Data de Compra: {produto['DataCompra']}\n"
            result += f"Validade: {produto['Validade']}\n"
            result += f"Preço: {produto['Preco']}\n"
            result += f"Descrição: {produto['Descricao']}\n"
            result += f"Estoque: {produto['Estoque']}\n"
            if produto['Fornecedores']:
                fornecedores_nomes = [self.estoque.fornecedores.get(fid, {}).get('Nome') for fid in produto['Fornecedores']]
                result += f"Fornecedores: {', '.join(fornecedores_nomes)}\n"
            else:
                result += "Fornecedores: Nenhum fornecedor vinculado\n"
            result += "\n"

        messagebox.showinfo("Tabela de Produtos Cadastrados", result)

    def ver_tabela_fornecedores(self):
        fornecedores = self.estoque.consultar_fornecedores()

        if not fornecedores:
            messagebox.showinfo("Tabela de Fornecedores Cadastrados", "Nenhum fornecedor cadastrado.")
            return

        result = "Tabela de Fornecedores Cadastrados:\n\n"
        for id_fornecedor, fornecedor_data in fornecedores.items():
            result += f"ID: {id_fornecedor}\n"
            result += f"Nome: {fornecedor_data['Nome']}\n"
            result += f"Endereco: {fornecedor_data['Endereco']}\n"
            result += f"Contato: {fornecedor_data['Contato']}\n"

            if 'Produtos' in fornecedor_data and fornecedor_data['Produtos']:
                result += f"Produtos vinculados: {', '.join(map(str, fornecedor_data['Produtos']))}\n"
            else:
                result += "Produtos vinculados: Nenhum produto vinculado\n"
            result += "\n"

        messagebox.showinfo("Tabela de Fornecedores Cadastrados", result)

    def produtos_vencidos(self):
        produtos_vencidos = self.estoque.produtos_vencidos()

        if not produtos_vencidos:
            messagebox.showinfo("Produtos Vencidos", "Nenhum produto vencido encontrado.")
        else:
            result = "Produtos Vencidos:\n\n"
            for produto in produtos_vencidos:
                result += f"ID: {produto[0]}\n"
                result += f"Nome: {produto[1]}\n"
                result += f"Data de Validade: {produto[2]}\n\n"
            messagebox.showinfo("Produtos Vencidos", result)

    def produtos_estoque_baixo(self):
        estoque_minimo = simpledialog.askinteger("Produtos com Estoque Baixo", "Estoque mínimo desejado:")

        if estoque_minimo is not None:
            produtos_estoque_baixo = self.estoque.produtos_estoque_baixo(estoque_minimo)
            
            if not produtos_estoque_baixo:
                messagebox.showinfo("Produtos com Estoque Baixo", "Nenhum produto com estoque baixo encontrado.")
            else:
                self.mostrar_tabela_produtos_estoque_baixo(produtos_estoque_baixo)
        else:
            messagebox.showerror("Erro", "Estoque mínimo é obrigatório.")

    def mostrar_tabela_produtos_estoque_baixo(self, produtos_estoque_baixo):
        window = tk.Toplevel()
        window.title("Produtos com Estoque Baixo")
        treeview = Treeview(window, columns=("ID_Produtos", "Nome", "Estoque"))
        treeview.heading("#1", text="ID")
        treeview.heading("#2", text="Nome")
        treeview.heading("#3", text="Estoque")
        treeview.pack()

        for produto in produtos_estoque_baixo:
            treeview.insert("", "end", values=(produto['ID_Produtos'], produto['Nome'], produto['Estoque']))

def main():
    root = tk.Tk()
    app = InterfaceGrafica(root)
    root.mainloop()

if __name__ == '__main__':
    main()
