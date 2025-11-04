from flask import Flask, render_template, request
import sqlite3
import re

app = Flask(__name__)


def criar_tabela():
    conn = sqlite3.connect("estoque.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS produto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fornecedor TEXT NOT NULL,
            nome TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            preco REAL NOT NULL
        )
    """
    )
    conn.commit()
    conn.close()


def buscar_produtos():
    conn = sqlite3.connect("estoque.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nome, fornecedor, quantidade FROM produto WHERE quantidade > 0"
    )
    produtos = cursor.fetchall()
    conn.close()
    return produtos


criar_tabela()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/inserir", methods=["GET", "POST"])
def inserir():
    mensagem = ""
    tipo_mensagem = ""

    if request.method == "POST":
        fornecedor = request.form.get("fornecedor")
        nome = request.form.get("produto")
        quantidade = request.form.get("quantidade")
        preco = request.form.get("preco")

        if not fornecedor or not nome or not quantidade or not preco:
            mensagem = "Todos os campos devem ser preenchidos."
            tipo_mensagem = "erro"
        else:
            try:
                preco_formatado = float(re.sub(r"[^\d]", "", preco)) / 100
                conn = sqlite3.connect("estoque.db")
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO produto (fornecedor, nome, quantidade, preco) VALUES (?, ?, ?, ?)",
                    (fornecedor, nome, int(quantidade), preco_formatado),
                )
                conn.commit()
                conn.close()
                mensagem = "Produto inserido com sucesso!"
                tipo_mensagem = "sucesso"
            except Exception as e:
                mensagem = f"Erro ao inserir: {e}"
                tipo_mensagem = "erro"

    return render_template(
        "inserir.html", mensagem=mensagem, tipo_mensagem=tipo_mensagem
    )


@app.route("/remover", methods=["GET", "POST"])
def remover():
    mensagem = ""
    tipo_mensagem = ""
    produtos = buscar_produtos()

    if request.method == "POST":
        produto_id = request.form.get("produto_id")
        quantidade_remover = request.form.get("quantidade")

        if not produto_id or not quantidade_remover:
            mensagem = "Preencha todos os campos."
            tipo_mensagem = "erro"
        else:
            try:
                conn = sqlite3.connect("estoque.db")
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT quantidade FROM produto WHERE id = ?", (produto_id,)
                )
                resultado = cursor.fetchone()
                if resultado:
                    quantidade_atual = resultado[0]
                    if int(quantidade_remover) > quantidade_atual:
                        mensagem = f"Erro: Apenas {quantidade_atual} em estoque."
                        tipo_mensagem = "erro"
                    else:
                        nova_qtd = quantidade_atual - int(quantidade_remover)
                        cursor.execute(
                            "UPDATE produto SET quantidade = ? WHERE id = ?",
                            (nova_qtd, produto_id),
                        )
                        conn.commit()
                        mensagem = "Produto removido com sucesso!"
                        tipo_mensagem = "sucesso"
                else:
                    mensagem = "Produto não encontrado."
                    tipo_mensagem = "erro"
                conn.close()
            except Exception as e:
                mensagem = f"Erro ao remover: {e}"
                tipo_mensagem = "erro"

    produtos = buscar_produtos()
    return render_template(
        "remover.html",
        produtos=produtos,
        mensagem=mensagem,
        tipo_mensagem=tipo_mensagem,
    )


@app.route("/visualizar")
def visualizar():
    conn = sqlite3.connect("estoque.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT fornecedor, nome, quantidade, preco FROM produto WHERE quantidade > 0"
    )
    produtos = cursor.fetchall()
    conn.close()

    total_qtd = sum(p[2] for p in produtos)
    total_valor = sum(p[2] * p[3] for p in produtos)
    total_valor = (
        f"{total_valor:.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )

    resumo_produto = {}
    for p in produtos:
        resumo_produto[p[1]] = resumo_produto.get(p[1], 0) + p[2]

    resumo_fornecedor = {}
    for p in produtos:
        resumo_fornecedor[p[0]] = resumo_fornecedor.get(p[0], 0) + p[2]

    grafico_produto_labels = list(resumo_produto.keys())
    grafico_produto_values = list(resumo_produto.values())

    grafico_fornecedor_labels = list(resumo_fornecedor.keys())
    grafico_fornecedor_values = list(resumo_fornecedor.values())

    produto_mais_caro = max(produtos, key=lambda x: x[3]) if produtos else None
    produto_mais_barato = min(produtos, key=lambda x: x[3]) if produtos else None
    produto_maior_qtd = max(produtos, key=lambda x: x[2]) if produtos else None
    produto_menor_qtd = min(produtos, key=lambda x: x[2]) if produtos else None

    return render_template(
        "visualizar.html",
        produtos=produtos,
        total_qtd=total_qtd,
        total_valor=total_valor,
        resumo_produto=resumo_produto,
        resumo_fornecedor=resumo_fornecedor,
        produto_mais_caro=produto_mais_caro,
        produto_mais_barato=produto_mais_barato,
        produto_maior_qtd=produto_maior_qtd,
        produto_menor_qtd=produto_menor_qtd,
        grafico_produto_labels=grafico_produto_labels,
        grafico_produto_values=grafico_produto_values,
        grafico_fornecedor_labels=grafico_fornecedor_labels,
        grafico_fornecedor_values=grafico_fornecedor_values,
    )


if __name__ == "__main__":
    app.run(debug=True)
