import sqlite3
import os
import sys
import datetime
import pandas as pd
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

    def cadastro_produto(self):
        cursor = self.conn.cursor()

        num_produtos = int(input('Quantos produtos deseja cadastrar? '))

        for i in range(num_produtos):
            id_produto = int(input('ID do produto: '))
            nome_produto = input('Nome do produto: ')
            data_compra = input('Data de compra (AAAA-MM-DD): ')
            data_validade = input('Data de validade (AAAA-MM-DD): ')
            preco = float(input('Preço: '))
            descricao = input('Descrição: ')
            estoque_inicial = int(input('Estoque Inicial: '))

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
        print(f'{num_produtos} produtos cadastrados com sucesso.')

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
            SELECT f.ID_Fornecedor, f.Nome, f.Endereco, f.Contato, pf.ProdutoID
            FROM fornecedores f
            LEFT JOIN produtos_fornecedores pf ON f.ID_Fornecedor = pf.FornecedorID
        ''')
        dados = cursor.fetchall()

        fornecedores = {}

        for dado in dados:
            id_fornecedor = dado[0]
            nome_fornecedor = dado[1]
            endereco_fornecedor = dado[2]
            contato_fornecedor = dado[3]
            id_produto = dado[4]

            if id_fornecedor not in fornecedores:
                fornecedores[id_fornecedor] = {
                    'Nome': nome_fornecedor,
                    'Endereco': endereco_fornecedor,
                    'Contato': contato_fornecedor,
                    'Produtos': []
                }

            if id_produto is not None:
                fornecedores[id_fornecedor]['Produtos'].append(id_produto)

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
        12 - Buscar Produtos por Nome                  
        13 - Sair
        >>> '''))

        os.system('cls')

        if opcao == 1:
            estoque.cadastro_produto()
        elif opcao == 2:
            id_fornecedor = int(input('ID do fornecedor: '))
            nome_fornecedor = input('Nome do fornecedor: ')
            endereco_fornecedor = input('Endereço do fornecedor: ')
            contato_fornecedor = input('Contato do fornecedor: ')
            fornecedor = {
                'ID_Fornecedor': id_fornecedor,
                'Nome': nome_fornecedor,
                'Endereco': endereco_fornecedor,
                'Contato': contato_fornecedor
            }
            estoque.cadastrar_fornecedor(fornecedor)
        elif opcao == 3:
            id_produto = int(input('ID do produto: '))
            id_fornecedor = int(input('ID do fornecedor: '))
            estoque.vincular_produto_a_fornecedor(id_produto, id_fornecedor)
        elif opcao == 4:
            id_produto = int(input('ID do produto: '))
            id_fornecedor = int(input('ID do fornecedor: '))
            estoque.desvincular_produto_de_fornecedor(id_produto, id_fornecedor)
        elif opcao == 5:
            id_produto = int(input('ID do produto a ser removido: '))
            estoque.remover_produto(id_produto)
        elif opcao == 6:
            id_fornecedor = int(input('ID do fornecedor a ser removido: '))
            estoque.remover_fornecedor(id_fornecedor)
        elif opcao == 7:
            id_produto = int(input('ID do produto: '))
            quantidade = int(input('Quantidade: '))
            estoque.atualizar_estoque(id_produto, quantidade)
        elif opcao == 8:
            estoque.ver_tabela_produtos()
        elif opcao == 9:
            estoque.ver_tabela_fornecedores()
        if opcao == 10:
            produtos_vencidos = estoque.produtos_vencidos()
            if produtos_vencidos:
                table = PrettyTable()
                table.field_names = ["ID", "Nome", "Data de Validade"]
                for produto in produtos_vencidos:
                    table.add_row(produto)
                print("Produtos vencidos:")
                print(table)
            else:
                print('Nenhum produto vencido encontrado.')
        elif opcao == 11:
            estoque_minimo = int(input('Estoque mínimo desejado: '))
            produtos_estoque_baixo = estoque.produtos_estoque_baixo(estoque_minimo)
            if produtos_estoque_baixo:
                print('Produtos com estoque baixo:')
                for produto in produtos_estoque_baixo:
                    print(f'ID: {produto["ID_Produtos"]}, Nome: {produto["Nome"]}, Estoque: {produto["Estoque"]}')
            else:
                print('Nenhum produto com estoque baixo encontrado.')
        elif opcao == 12:
            substring = input('Digite a substring que deseja buscar nos nomes dos produtos: ')
            estoque.buscar_produtos_por_nome(substring)        
        elif opcao == 13:
            estoque.conn.close()
            sys.exit(0)
