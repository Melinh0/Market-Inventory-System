import sqlite3
import os
import sys
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from prettytable import PrettyTable

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
                ID INTEGER PRIMARY KEY,
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
                ID INTEGER PRIMARY KEY,
                Nome TEXT,
                Endereco TEXT,
                Contato TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS produtos_fornecedores (
                ProdutoID INTEGER,
                FornecedorID INTEGER,
                FOREIGN KEY (ProdutoID) REFERENCES produtos (ID),
                FOREIGN KEY (FornecedorID) REFERENCES fornecedores (ID)
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
                'ID': produto[0],
                'Nome': produto[1],
                'DataCompra': produto[2],
                'Validade': produto[3],
                'Preco': produto[4],
                'Descricao': produto[5],
                'Estoque': produto[6]
            }

        for fornecedor in fornecedores:
            self.fornecedores[fornecedor[0]] = {
                'ID': fornecedor[0],
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

    def cadastro_produto(self, nome_produto, data_compra, data_validade, preco, descricao, estoque_inicial):
        cursor = self.conn.cursor()

        cursor.execute('''
            INSERT INTO produtos (Nome, DataCompra, Validade, Preco, Descricao, Estoque)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (nome_produto, data_compra, data_validade, preco, descricao, estoque_inicial))

        self.conn.commit()
        produto_id = cursor.lastrowid
        self.produtos[produto_id] = {
            'ID': produto_id,
            'Nome': nome_produto,
            'DataCompra': data_compra,
            'Validade': data_validade,
            'Preco': preco,
            'Descricao': descricao,
            'Estoque': estoque_inicial
        }
        print(f'Produto {nome_produto} cadastrado com sucesso. ID: {produto_id}')

    def cadastro_fornecedor(self, fornecedor):
        cursor = self.conn.cursor()

        cursor.execute('''
            INSERT INTO fornecedores (Nome, Endereco, Contato)
            VALUES (?, ?, ?)
        ''', (fornecedor['Nome'], fornecedor['Endereco'], fornecedor['Contato']))

        self.conn.commit()
        fornecedor_id = cursor.lastrowid
        fornecedor['ID'] = fornecedor_id
        self.fornecedores[fornecedor_id] = fornecedor
        print(f'Fornecedor {fornecedor["Nome"]} cadastrado com sucesso.')

    def vincular_produto_a_fornecedor(self, produto_id, fornecedor_id):
        cursor = self.conn.cursor()

        cursor.execute('''
            INSERT INTO produtos_fornecedores (ProdutoID, FornecedorID)
            VALUES (?, ?)
        ''', (produto_id, fornecedor_id))

        self.conn.commit()

        if produto_id in self.produtos:
            if 'fornecedores_vinculados' not in self.produtos[produto_id]:
                self.produtos[produto_id]['fornecedores_vinculados'] = []
            self.produtos[produto_id]['fornecedores_vinculados'].append(fornecedor_id)
        if fornecedor_id in self.fornecedores:
            if 'produtos_vinculados' not in self.fornecedores[fornecedor_id]:
                self.fornecedores[fornecedor_id]['produtos_vinculados'] = []
            self.fornecedores[fornecedor_id]['produtos_vinculados'].append(produto_id)
        print(f'Produto {self.produtos[produto_id]["Nome"]} vinculado ao fornecedor {self.fornecedores[fornecedor_id]["Nome"]} com sucesso.')

    def desvincular_produto_de_fornecedor(self, produto_id, fornecedor_id):
        cursor = self.conn.cursor()

        cursor.execute('''
            DELETE FROM produtos_fornecedores WHERE ProdutoID = ? AND FornecedorID = ?
        ''', (produto_id, fornecedor_id))

        self.conn.commit()

        if produto_id in self.produtos:
            if 'fornecedores_vinculados' in self.produtos[produto_id]:
                self.produtos[produto_id]['fornecedores_vinculados'].remove(fornecedor_id)
        if fornecedor_id in self.fornecedores:
            if 'produtos_vinculados' in self.fornecedores[fornecedor_id]:
                self.fornecedores[fornecedor_id]['produtos_vinculados'].remove(produto_id)
        print(f'Produto {self.produtos[produto_id]["Nome"]} desvinculado do fornecedor {self.fornecedores[fornecedor_id]["Nome"]} com sucesso.')

    def remover_produto(self, produto_id):
        cursor = self.conn.cursor()

        cursor.execute('DELETE FROM produtos WHERE ID = ?', (produto_id,))
        cursor.execute('DELETE FROM produtos_fornecedores WHERE ProdutoID = ?', (produto_id,))

        self.conn.commit()

        if produto_id in self.produtos:
            del self.produtos[produto_id]
            print(f'Produto com ID {produto_id} removido com sucesso.')
        else:
            print(f'Produto com ID {produto_id} não encontrado.')

    def remover_fornecedor(self, fornecedor_id):
        cursor = self.conn.cursor()

        cursor.execute('DELETE FROM fornecedores WHERE ID = ?', (fornecedor_id,))
        cursor.execute('DELETE FROM produtos_fornecedores WHERE FornecedorID = ?', (fornecedor_id,))

        self.conn.commit()

        if fornecedor_id in self.fornecedores:
            del self.fornecedores[fornecedor_id]
            print(f'Fornecedor com ID {fornecedor_id} removido com sucesso.')
        else:
            print(f'Fornecedor com ID {fornecedor_id} não encontrado.')

    def atualizar_estoque(self, produto_id, quantidade):
        cursor = self.conn.cursor()

        cursor.execute('UPDATE produtos SET Estoque = Estoque + ? WHERE ID = ?', (quantidade, produto_id))

        self.conn.commit()

        if produto_id in self.produtos:
            self.produtos[produto_id]['Estoque'] += quantidade
            print(f'Estoque do produto com ID {produto_id} atualizado para {self.produtos[produto_id]["Estoque"]}.')
        else:
            print(f'Produto com ID {produto_id} não encontrado.')

    def ver_tabela_produtos(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT p.ID, p.Nome AS Produto, p.DataCompra, p.Validade, p.Preco, p.Descricao, p.Estoque, GROUP_CONCAT(f.Nome) AS Fornecedores
            FROM produtos p
            LEFT JOIN produtos_fornecedores pf ON p.ID = pf.ProdutoID
            LEFT JOIN fornecedores f ON pf.FornecedorID = f.ID
            GROUP BY p.ID
        ''')
        produtos = cursor.fetchall()

        df_produtos = pd.DataFrame(produtos, columns=["ID", "Produto", "DataCompra", "Validade", "Preco", "Descricao", "Estoque", "Fornecedores"])
        print("Tabela de Produtos Cadastrados:")
        print(df_produtos)

    def ver_tabela_fornecedores(self):
        df_fornecedores = pd.DataFrame(list(self.fornecedores.values()))
        print("Tabela de Fornecedores Cadastrados:")
        print(df_fornecedores)

    def produtos_vencidos(self):
        data_atual = datetime.date.today()
        produtos_vencidos = []
        for produto_id, produto in self.produtos.items():
            data_validade = datetime.datetime.strptime(str(produto['Validade']), "%Y-%m-%d").date()
            if data_validade < data_atual:
                produtos_vencidos.append(produto)

        if produtos_vencidos:
            table = PrettyTable()
            table.field_names = ["ID", "Nome", "Data de Validade"]
            
            for produto in produtos_vencidos:
                table.add_row([produto['ID'], produto['Nome'], produto['Validade']])

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
                table.add_row([produto['ID'], produto['Nome'], produto['Estoque']])

            print("Produtos com Estoque Baixo:")
            print(table)
            return produtos_estoque_baixo
        else:
            print('Nenhum produto com estoque baixo encontrado.')
            return []

if __name__ == '__main__':
    estoque = Estoque()

    while True:
        opcao = int(input('''Escolha uma opção:
        1 - Cadastrar Produto
        2 - Cadastrar Fornecedor
        3 - Vincular Produto e Fornecedor
        4 - Desvincular Produto de Fornecedor
        5 - Remover Produto
        6 - Remover Fornecedor
        7 - Atualizar Estoque
        8 - Ver Tabela dos Produtos Cadastrados
        9 - Ver Tabela dos Fornecedores Cadastrados
        10 - Produtos Vencidos
        11 - Produtos com Estoque Baixo
        12 - Sair
        >>> '''))

        os.system('cls')

        if opcao == 1:
            nome_produto = input('Nome do produto: ')
            data_compra = input('Data de compra (AAAA-MM-DD): ')
            data_validade = input('Data de validade (AAAA-MM-DD): ')
            preco = float(input('Preço: '))
            descricao = input('Descrição: ')
            estoque_inicial = int(input('Estoque Inicial: '))
            estoque.cadastro_produto(nome_produto, data_compra, data_validade, preco, descricao, estoque_inicial)
        elif opcao == 2:
            fornecedor_id = int(input('ID do fornecedor: '))
            nome_fornecedor = input('Nome do fornecedor: ')
            endereco_fornecedor = input('Endereço do fornecedor: ')
            contato_fornecedor = input('Contato do fornecedor: ')
            fornecedor = {
                'ID': fornecedor_id,
                'Nome': nome_fornecedor,
                'Endereco': endereco_fornecedor,
                'Contato': contato_fornecedor
            }
            estoque.cadastro_fornecedor(fornecedor)
        elif opcao == 3:
            produto_id = int(input('ID do produto: '))
            fornecedor_id = int(input('ID do fornecedor: '))
            estoque.vincular_produto_a_fornecedor(produto_id, fornecedor_id)
        elif opcao == 4:
            produto_id = int(input('ID do produto: '))
            fornecedor_id = int(input('ID do fornecedor: '))
            estoque.desvincular_produto_de_fornecedor(produto_id, fornecedor_id)
        elif opcao == 5:
            produto_id = int(input('ID do produto a ser removido: '))
            estoque.remover_produto(produto_id)
        elif opcao == 6:
            fornecedor_id = int(input('ID do fornecedor a ser removido: '))
            estoque.remover_fornecedor(fornecedor_id)
        elif opcao == 7:
            produto_id = int(input('ID do produto: '))
            quantidade = int(input('Quantidade: '))
            estoque.atualizar_estoque(produto_id, quantidade)
        elif opcao == 8:
            estoque.ver_tabela_produtos()
        elif opcao == 9:
            estoque.ver_tabela_fornecedores()
        elif opcao == 10:
            produtos_vencidos = estoque.produtos_vencidos()
            if produtos_vencidos:
                print('Produtos vencidos:')
                for produto in produtos_vencidos:
                    print(f'ID: {produto["ID"]}, Nome: {produto["Nome"]}')
            else:
                print('Nenhum produto vencido encontrado.')
        elif opcao == 11:
            estoque_minimo = int(input('Estoque mínimo desejado: '))
            produtos_estoque_baixo = estoque.produtos_estoque_baixo(estoque_minimo)
            if produtos_estoque_baixo:
                print('Produtos com estoque baixo:')
                for produto in produtos_estoque_baixo:
                    print(f'ID: {produto["ID"]}, Nome: {produto["Nome"]}, Estoque: {produto["Estoque"]}')
            else:
                print('Nenhum produto com estoque baixo encontrado.')
        elif opcao == 12:
            estoque.conn.close()
            sys.exit(0)
