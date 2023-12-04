import sqlite3
import os
import sys
import datetime
import pandas as pd
from prettytable import PrettyTable
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog, ttk
from SistemaInventario import Estoque
from tkinter.ttk import Treeview, Scrollbar
import matplotlib.pyplot as plt

class Estoque(object):
    def __init__(self):
        self.conn = sqlite3.connect('estoque.db')
        self.criar_tabelas()
        self.produtos = {}
        self.fornecedores = {}
        self.carregar_dados()

    def criar_tabelas(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS produtos (
                ID_Produtos INTEGER PRIMARY KEY,
                Nome TEXT,
                DataCompra DATE,
                Validade DATE,
                Preco REAL,
                Descricao TEXT,
                Estoque INTEGER
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fornecedores (
                ID_Fornecedor INTEGER PRIMARY KEY,
                Nome TEXT,
                Endereco TEXT,
                Contato TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS produtos_fornecedores (
                ProdutoID INTEGER,
                FornecedorID INTEGER,
                FOREIGN KEY (ProdutoID) REFERENCES produtos (ID_Produtos),
                FOREIGN KEY (FornecedorID) REFERENCES fornecedores (ID_Fornecedor)
            )
        ''')
        self.conn.commit()

    def carregar_dados(self):
        cursor = self.conn.cursor()

        cursor.execute('SELECT * FROM produtos')
        produtos = cursor.fetchall()
        cursor.execute('SELECT * FROM fornecedores')
        fornecedores = cursor.fetchall()
        cursor.execute('SELECT * FROM produtos_fornecedores')
        vinculos = cursor.fetchall()

        for produto in produtos:
            self.produtos[produto[0]] = {
                'ID_Produtos': produto[0],
                'Nome': produto[1],
                'DataCompra': produto[2],
                'Validade': produto[3],
                'Preco': produto[4],
                'Descricao': produto[5],
                'Estoque': produto[6]
            }

        for fornecedor in fornecedores:
            self.fornecedores[fornecedor[0]] = {
                'ID_Fornecedor': fornecedor[0],
                'Nome': fornecedor[1],
                'Endereco': fornecedor[2],
                'Contato': fornecedor[3]
            }

        for vinculo in vinculos:
            produto_id, fornecedor_id = vinculo[0], vinculo[1]
            if produto_id in self.produtos:
                if 'fornecedores_vinculados' not in self.produtos[produto_id]:
                    self.produtos[produto_id]['fornecedores_vinculados'] = []
                self.produtos[produto_id]['fornecedores_vinculados'].append(fornecedor_id)
            if fornecedor_id in self.fornecedores:
                if 'produtos_vinculados' not in self.fornecedores[fornecedor_id]:
                    self.fornecedores[fornecedor_id]['produtos_vinculados'] = []
                self.fornecedores[fornecedor_id]['produtos_vinculados'].append(produto_id)

    def cadastro_produto(self, id_produto, nome_produto, data_compra, data_validade, preco, descricao, estoque_inicial):
        cursor = self.conn.cursor()

        cursor.execute('''
            INSERT INTO produtos (ID_Produtos, Nome, DataCompra, Validade, Preco, Descricao, Estoque)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (id_produto, nome_produto, data_compra, data_validade, preco, descricao, estoque_inicial))

        self.conn.commit()
        self.produtos[id_produto] = {
            'ID_Produtos': id_produto,
            'Nome': nome_produto,
            'DataCompra': data_compra,
            'Validade': data_validade,
            'Preco': preco,
            'Descricao': descricao,
            'Estoque': estoque_inicial
        }
        print(f'Produto {nome_produto} cadastrado com sucesso. ID: {id_produto}')

    def cadastrar_fornecedor(self, fornecedor):
        cursor = self.conn.cursor()

        cursor.execute('''
            INSERT INTO fornecedores (ID_Fornecedor, Nome, Endereco, Contato)
            VALUES (?, ?, ?, ?)
        ''', (fornecedor['ID_Fornecedor'], fornecedor['Nome'], fornecedor['Endereco'], fornecedor['Contato']))

        self.conn.commit()
        self.fornecedores[fornecedor['ID_Fornecedor']] = fornecedor
        print(f'Fornecedor {fornecedor["Nome"]} cadastrado com sucesso.')

    def vincular_produto_a_fornecedor(self, id_produto, id_fornecedor):
        cursor = self.conn.cursor()

        cursor.execute('''
            INSERT INTO produtos_fornecedores (ProdutoID, FornecedorID)
            VALUES (?, ?)
        ''', (id_produto, id_fornecedor))

        self.conn.commit()

        if id_produto in self.produtos:
            if 'fornecedores_vinculados' not in self.produtos[id_produto]:
                self.produtos[id_produto]['fornecedores_vinculados'] = []
            self.produtos[id_produto]['fornecedores_vinculados'].append(id_fornecedor)
        if id_fornecedor in self.fornecedores:
            if 'produtos_vinculados' not in self.fornecedores[id_fornecedor]:
                self.fornecedores[id_fornecedor]['produtos_vinculados'] = []
            self.fornecedores[id_fornecedor]['produtos_vinculados'].append(id_produto)
        print(f'Produto {self.produtos[id_produto]["Nome"]} vinculado ao fornecedor {self.fornecedores[id_fornecedor]["Nome"]} com sucesso.')

    def desvincular_produto_de_fornecedor(self, id_produto, id_fornecedor):
        cursor = self.conn.cursor()

        cursor.execute('''
            DELETE FROM produtos_fornecedores WHERE ProdutoID = ? AND FornecedorID = ?
        ''', (id_produto, id_fornecedor))

        self.conn.commit()

        if id_produto in self.produtos:
            if 'fornecedores_vinculados' in self.produtos[id_produto]:
                self.produtos[id_produto]['fornecedores_vinculados'].remove(id_fornecedor)
        if id_fornecedor in self.fornecedores:
            if 'produtos_vinculados' in self.fornecedores[id_fornecedor]:
                self.fornecedores[id_fornecedor]['produtos_vinculados'].remove(id_produto)
        print(f'Produto {self.produtos[id_produto]["Nome"]} desvinculado do fornecedor {self.fornecedores[id_fornecedor]["Nome"]} com sucesso.')

    def remover_produto(self, id_produto):
        cursor = self.conn.cursor()

        cursor.execute('DELETE FROM produtos WHERE ID_Produtos = ?', (id_produto,))
        cursor.execute('DELETE FROM produtos_fornecedores WHERE ProdutoID = ?', (id_produto,))

        self.conn.commit()

        if id_produto in self.produtos:
            del self.produtos[id_produto]
            print(f'Produto com ID {id_produto} removido com sucesso.')
        else:
            print(f'Produto com ID {id_produto} não encontrado.')

    def remover_fornecedor(self, id_fornecedor):
        cursor = self.conn.cursor()

        cursor.execute('DELETE FROM fornecedores WHERE ID_Fornecedor = ?', (id_fornecedor,))
        cursor.execute('DELETE FROM produtos_fornecedores WHERE FornecedorID = ?', (id_fornecedor,))

        self.conn.commit()

        if id_fornecedor in self.fornecedores:
            del self.fornecedores[id_fornecedor]
            print(f'Fornecedor com ID {id_fornecedor} removido com sucesso.')
        else:
            print(f'Fornecedor com ID {id_fornecedor} não encontrado.')

    def atualizar_estoque(self, id_produto, quantidade):
        cursor = self.conn.cursor()

        cursor.execute('UPDATE produtos SET Estoque = Estoque + ? WHERE ID_Produtos = ?', (quantidade, id_produto))

        self.conn.commit()

        if id_produto in self.produtos:
            self.produtos[id_produto]['Estoque'] += quantidade
            print(f'Estoque do produto com ID {id_produto} atualizado para {self.produtos[id_produto]["Estoque"]}.')
        else:
            print(f'Produto com ID {id_produto} não encontrado.')

    def consultar_produtos_com_fornecedores(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT p.ID_Produtos, p.Nome AS Produto, p.DataCompra, p.Validade, p.Preco, p.Descricao, p.Estoque, GROUP_CONCAT(pf.FornecedorID) AS Fornecedores
            FROM produtos p
            LEFT JOIN produtos_fornecedores pf ON p.ID_Produtos = pf.ProdutoID
            GROUP BY p.ID_Produtos
        ''')
        produtos = cursor.fetchall()

        produtos_com_fornecedores = []

        for produto in produtos:
            produtos_com_fornecedores.append({
                'ID_Produtos': produto[0],
                'Nome': produto[1],
                'DataCompra': produto[2],
                'Validade': produto[3],
                'Preco': produto[4],
                'Descricao': produto[5],
                'Estoque': produto[6],
                'Fornecedores': [int(fid) for fid in produto[7].split(',')] if produto[7] else []
            })

        return produtos_com_fornecedores

    def consultar_fornecedores(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT f.ID_Fornecedor, f.Nome, f.Endereco, f.Contato, GROUP_CONCAT(pf.ProdutoID) AS Produtos
            FROM fornecedores f
            LEFT JOIN produtos_fornecedores pf ON f.ID_Fornecedor = pf.FornecedorID
            GROUP BY f.ID_Fornecedor
        ''')
        dados = cursor.fetchall()

        fornecedores = []

        for dado in dados:
            id_fornecedor, nome_fornecedor, endereco_fornecedor, contato_fornecedor, produtos_str = dado

            fornecedor = {
                'ID_Fornecedor': id_fornecedor,
                'Nome': nome_fornecedor,
                'Endereco': endereco_fornecedor,
                'Contato': contato_fornecedor,
                'Produtos': [int(pid) for pid in produtos_str.split(',')] if produtos_str else []
            }

            fornecedores.append(fornecedor)

        return fornecedores

    def ver_tabela_produtos(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT p.ID_Produtos, p.Nome AS Produto, p.DataCompra, p.Validade, p.Preco, p.Descricao, p.Estoque, GROUP_CONCAT(f.Nome) AS Fornecedores
            FROM produtos p
            LEFT JOIN produtos_fornecedores pf ON p.ID_Produtos = pf.ProdutoID
            LEFT JOIN fornecedores f ON pf.FornecedorID = f.ID_Fornecedor
            GROUP BY p.ID_Produtos
        ''')
        produtos = cursor.fetchall()

        df_produtos = pd.DataFrame(produtos, columns=["ID_Produtos", "Produto", "DataCompra", "Validade", "Preco", "Descricao", "Estoque", "Fornecedores"])
        print("Tabela de Produtos Cadastrados:")
        print(df_produtos)

    def ver_tabela_fornecedores(self):
        df_fornecedores = pd.DataFrame(list(self.fornecedores.values()))
        print("Tabela de Fornecedores Cadastrados:")
        print(df_fornecedores)

    def produtos_vencidos(self):
        data_atual = datetime.date.today()
        produtos_vencidos = []
        for id_produto, produto in self.produtos.items():
            data_validade = datetime.datetime.strptime(str(produto['Validade']), "%Y-%m-%d").date()
            if data_validade < data_atual:
                produtos_vencidos.append([produto['ID_Produtos'], produto['Nome'], produto['Validade']])

        if produtos_vencidos:
            table = PrettyTable()
            table.field_names = ["ID", "Nome", "Data de Validade"]

            for produto in produtos_vencidos:
                table.add_row(produto)

            print("Produtos Vencidos:")
            print(table)
            return produtos_vencidos
        else:
            print('Nenhum produto vencido encontrado.')
            return []

    def produtos_estoque_baixo(self, estoque_minimo):
        produtos_estoque_baixo = [produto for produto in self.produtos.values() if produto['Estoque'] < estoque_minimo]
        if produtos_estoque_baixo:
            table = PrettyTable()
            table.field_names = ["ID", "Nome", "Estoque"]
            for produto in produtos_estoque_baixo:
                table.add_row([produto['ID_Produtos'], produto['Nome'], produto['Estoque']])
            print("Produtos com Estoque Baixo:")
            print(table)
            return produtos_estoque_baixo
        else:
            print('Nenhum produto com estoque baixo encontrado.')
            return []

    def buscar_produtos_por_nome(self, substring):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM produtos WHERE Nome LIKE ?', (f'%{substring}%',))
        produtos_encontrados = cursor.fetchall()
        if produtos_encontrados:
            df_produtos = pd.DataFrame(produtos_encontrados, columns=["ID_Produtos", "Nome", "DataCompra", "Validade", "Preco", "Descricao", "Estoque"])
            print(f'Produtos com a substring "{substring}" no nome:')
            print(df_produtos)
            return produtos_encontrados  
        else:
            print(f'Nenhum produto encontrado com a substring "{substring}" no nome.')
            return None   
        
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

        self.button_baixar_tabela_produtos = tk.Button(root, text="Baixar Tabela de Produtos (Excel)", command=self.baixar_tabela_produtos)
        self.button_baixar_tabela_produtos.pack()

        self.button_ver_tabela_fornecedores = tk.Button(root, text="Ver Tabela de Fornecedores Cadastrados", command=self.ver_tabela_fornecedores)
        self.button_ver_tabela_fornecedores.pack()

        self.button_baixar_tabela_fornecedores = tk.Button(root, text="Baixar Tabela de Fornecedores (Excel)", command=self.baixar_tabela_fornecedores)
        self.button_baixar_tabela_fornecedores.pack()

        self.button_produtos_vencidos = tk.Button(root, text="Produtos Vencidos", command=self.produtos_vencidos)
        self.button_produtos_vencidos.pack()

        self.button_produtos_estoque_baixo = tk.Button(root, text="Produtos com Estoque Baixo", command=self.produtos_estoque_baixo)
        self.button_produtos_estoque_baixo.pack()

        self.button_produtos_estoque_baixo = tk.Button(root, text="Buscar Produtos por Nome", command=self.buscar_produtos_por_nome)
        self.button_produtos_estoque_baixo.pack()

    def cadastrar_produto(self):
        num_produtos = int(simpledialog.askstring("Cadastrar Produto", "Quantos produtos deseja cadastrar?"))

        for i in range(num_produtos):
            id_produto = int(simpledialog.askstring("Cadastrar Produto", "ID do produto:"))
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
                    self.estoque.cadastro_produto(id_produto, nome_produto, data_compra, data_validade, preco, descricao, estoque_inicial)
                    messagebox.showinfo("Sucesso", f"Produto {nome_produto} cadastrado com sucesso. ID: {id_produto}")
                except ValueError:
                    messagebox.showerror("Erro", "Data em formato inválido.")
            else:
                messagebox.showerror("Erro", "Nome, data de compra e data de validade são obrigatórios.")

    def cadastrar_fornecedor(self):
        id_fornecedor = int(simpledialog.askstring("Cadastrar Fornecedor", "ID do fornecedor:"))
        nome_fornecedor = simpledialog.askstring("Cadastrar Fornecedor", "Nome do fornecedor:")
        endereco_fornecedor = simpledialog.askstring("Cadastrar Fornecedor", "Endereço do fornecedor:")
        contato_fornecedor = simpledialog.askstring("Cadastrar Fornecedor", "Contato do fornecedor:")

        if nome_fornecedor:
            fornecedor = {
                'ID_Fornecedor': id_fornecedor,
                'Nome': nome_fornecedor,
                'Endereco': endereco_fornecedor,
                'Contato': contato_fornecedor
            }
            self.estoque.cadastrar_fornecedor(fornecedor)
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
        self.mostrar_tabela_scrollable("Tabela de Produtos Cadastrados", produtos)

        if not produtos:
            messagebox.showinfo("Tabela de Produtos Cadastrados", "Nenhum produto cadastrado.")
            return

    def baixar_tabela_produtos(self):
            produtos = self.estoque.consultar_produtos_com_fornecedores()
            if not produtos:
                messagebox.showinfo("Tabela de Produtos Cadastrados", "Nenhum produto cadastrado.")
                return

            df_produtos = pd.DataFrame(produtos)

            file_path = tk.filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])

            if file_path:
                df_produtos.to_excel(file_path, index=False)
                messagebox.showinfo("Tabela de Produtos Cadastrados", f"Arquivo Excel salvo em: {file_path}")

    def ver_tabela_fornecedores(self):
            fornecedores = self.estoque.consultar_fornecedores()
            if not fornecedores:
                messagebox.showinfo("Tabela de Fornecedores Cadastrados", "Nenhum fornecedor cadastrado.")
                return

            self.mostrar_tabela_scrollable("Tabela de Fornecedores Cadastrados", fornecedores)

    def baixar_tabela_fornecedores(self):
        fornecedores = self.estoque.consultar_fornecedores()
        if not fornecedores:
            messagebox.showinfo("Baixar Tabela de Fornecedores", "Nenhum fornecedor disponível.")
            return

        df_fornecedores = pd.DataFrame(fornecedores)

        file_path = tk.filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])

        if file_path:
            df_fornecedores.to_excel(file_path, index=False)
            messagebox.showinfo("Tabela de Fornecedores Cadastrados", f"Arquivo Excel salvo em: {file_path}")

    def produtos_vencidos(self):
        produtos_vencidos = self.estoque.produtos_vencidos()

        if not produtos_vencidos:
            messagebox.showinfo("Produtos Vencidos", "Nenhum produto vencido encontrado.")
            return

        window = tk.Toplevel()
        window.title("Produtos Vencidos")
        treeview = ttk.Treeview(window, columns=("ID", "Nome", "Data de Validade"))
        treeview.heading("#1", text="ID")
        treeview.heading("#2", text="Nome")
        treeview.heading("#3", text="Data de Validade")
        treeview.pack()

        for produto in produtos_vencidos:
            treeview.insert("", "end", values=(produto[0], produto[1], produto[2]))

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

    def buscar_produtos_por_nome(self):
        substring = simpledialog.askstring("Buscar Produtos por Nome", "Substring do Nome do Produto:")
        if substring:
            print(f"Chamando self.estoque.buscar_produtos_por_nome com substring: {substring}")
            produtos_encontrados = self.estoque.buscar_produtos_por_nome(substring)
            if produtos_encontrados is not None:
                if produtos_encontrados:
                    self.mostrar_tabela_produtos_por_nome(produtos_encontrados, f"Produtos com a substring '{substring}' no nome")
                else:
                    messagebox.showinfo("Produtos Encontrados", f"Nenhum produto encontrado com a substring '{substring}' no nome.")
            else:
                messagebox.showerror("Erro", "Ocorreu um problema ao buscar os produtos.")
        else:
            messagebox.showerror("Erro", "Substring do nome do produto é obrigatória.")

    def mostrar_tabela_produtos_por_nome(self, produtos, titulo):
        window = tk.Toplevel()
        window.title(titulo)

        treeview = Treeview(window, columns=("ID_Produtos", "Nome", "Data de Compra", "Validade", "Preço", "Descrição"))
        treeview.heading("#1", text="ID")
        treeview.heading("#2", text="Nome")
        treeview.heading("#3", text="Data de Compra")
        treeview.heading("#4", text="Validade")
        treeview.heading("#5", text="Preço")
        treeview.heading("#6", text="Descrição")
        treeview.pack()

        for produto in produtos:
            treeview.insert("", "end", values=(
                produto[0],  
                produto[1], 
                produto[2],  
                produto[3],  
                produto[4],  
                produto[5]  
            ))

    def mostrar_tabela_scrollable(self, titulo, dados):
        window = tk.Toplevel()
        window.title(titulo)

        if not dados or not dados[0]:
            messagebox.showinfo(titulo, "Nenhum dado disponível para exibir.")
            return

        treeview = ttk.Treeview(window, columns=list(dados[0].keys()), show="headings")

        for col in dados[0].keys():
            treeview.heading(col, text=col)
            treeview.column(col, anchor=tk.CENTER)

        for row in dados:
            treeview.insert("", "end", values=list(row.values()))

        horizontal_scrollbar = tk.Scrollbar(window, orient="horizontal", command=treeview.xview)
        horizontal_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        treeview.configure(xscrollcommand=horizontal_scrollbar.set)

        scrollbar = tk.Scrollbar(window, command=treeview.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        treeview.config(yscrollcommand=scrollbar.set)

        treeview.pack(expand=tk.YES, fill=tk.BOTH)

def main():
    root = tk.Tk()
    app = InterfaceGrafica(root)
    app.buscar_produtos_por_nome
    root.mainloop()

if __name__ == '__main__':
    main()
