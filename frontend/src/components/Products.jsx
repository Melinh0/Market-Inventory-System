import { useMemo, useState } from "react";
import { api, formatBRL } from "../api.js";
import Modal from "./Modal.jsx";

const EMPTY = {
  nome: "",
  categoria: "alimento",
  data_compra: new Date().toISOString().slice(0, 10),
  validade: "",
  preco: "",
  descricao: "",
  estoque: "",
};

const STATUS_LABEL = { vencido: "Vencido", proximo: "A vencer", ok: "No prazo" };

export default function Products({ products, suppliers, onChange }) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [form, setForm] = useState(null);
  const [linkTarget, setLinkTarget] = useState(null);
  const [message, setMessage] = useState("");

  const filtered = useMemo(() => {
    return products.filter((product) => {
      const matchesQuery = product.nome.toLowerCase().includes(query.toLowerCase());
      const matchesStatus = !status || product.status === status;
      return matchesQuery && matchesStatus;
    });
  }, [products, query, status]);

  const notify = (text) => {
    setMessage(text);
    setTimeout(() => setMessage(""), 3000);
  };

  const submit = async (event) => {
    event.preventDefault();
    try {
      if (form.id) {
        await api.patch(`/api/products/${form.id}/`, form);
        notify("Produto atualizado com sucesso.");
      } else {
        await api.post("/api/products/", form);
        notify("Produto cadastrado com sucesso.");
      }
      setForm(null);
      onChange();
    } catch (err) {
      notify(err.message);
    }
  };

  const remove = async (product) => {
    if (!window.confirm(`Excluir o produto "${product.nome}"?`)) return;
    await api.del(`/api/products/${product.id}/`);
    notify("Produto excluído.");
    onChange();
  };

  const change = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const submitLink = async (event) => {
    event.preventDefault();
    const supplierId = event.target.supplier.value;
    if (!supplierId) return;
    await api.post(`/api/products/${linkTarget.id}/link/`, { supplier_id: Number(supplierId) });
    notify("Fornecedor vinculado.");
    setLinkTarget(null);
    onChange();
  };

  const unlink = async (product, supplierId) => {
    await api.del(`/api/products/${product.id}/link/${supplierId}/`);
    notify("Fornecedor desvinculado.");
    onChange();
  };

  return (
    <div>
      <div className="toolbar">
        <input
          className="input"
          placeholder="Buscar produto pelo nome..."
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <select className="input" value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="">Todas as situações</option>
          <option value="ok">No prazo</option>
          <option value="proximo">A vencer</option>
          <option value="vencido">Vencido</option>
        </select>
        <a className="btn ghost" href="/api/products/export/">
          Exportar CSV
        </a>
        <button className="btn primary" onClick={() => setForm({ ...EMPTY })}>
          + Novo produto
        </button>
      </div>

      {message && <div className="banner info">{message}</div>}

      <div className="panel">
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Produto</th>
              <th>Categoria</th>
              <th>Validade</th>
              <th>Preço</th>
              <th>Estoque</th>
              <th>Fornecedores</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((product) => (
              <tr key={product.id}>
                <td>{product.id}</td>
                <td>
                  <strong>{product.nome}</strong>
                  <small className="muted">{product.descricao}</small>
                </td>
                <td>
                  <span className="chip">{product.categoria}</span>
                </td>
                <td>
                  <span className={`chip ${product.status}`}>{STATUS_LABEL[product.status]}</span>
                  <small className="muted">{product.validade}</small>
                </td>
                <td>{formatBRL(product.preco)}</td>
                <td>{product.estoque} un.</td>
                <td>
                  <div className="chips">
                    {product.fornecedores.map((supplier) => (
                      <span key={supplier.id} className="chip link" title="Clique para desvincular">
                        {supplier.nome}
                        <button className="chip-x" onClick={() => unlink(product, supplier.id)}>
                          ✕
                        </button>
                      </span>
                    ))}
                    <button className="chip add" onClick={() => setLinkTarget(product)}>
                      + fornecedor
                    </button>
                  </div>
                </td>
                <td className="actions">
                  <button
                    className="btn small"
                    onClick={() =>
                      setForm({
                        ...product,
                        preco: product.preco,
                        estoque: product.estoque,
                      })
                    }
                  >
                    Editar
                  </button>
                  <button className="btn small danger" onClick={() => remove(product)}>
                    Excluir
                  </button>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan="8" className="muted center">
                  Nenhum produto encontrado.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {form && (
        <Modal title={form.id ? "Editar produto" : "Novo produto"} onClose={() => setForm(null)}>
          <form className="form" onSubmit={submit}>
            <label>
              Nome
              <input className="input" name="nome" value={form.nome} onChange={change} required />
            </label>
            <div className="row">
              <label>
                Categoria
                <select className="input" name="categoria" value={form.categoria} onChange={change}>
                  <option value="alimento">Alimento</option>
                  <option value="limpeza">Limpeza</option>
                  <option value="higiene">Higiene</option>
                  <option value="bebida">Bebida</option>
                  <option value="outros">Outros</option>
                </select>
              </label>
              <label>
                Preço (R$)
                <input
                  className="input"
                  name="preco"
                  type="number"
                  step="0.01"
                  min="0"
                  value={form.preco}
                  onChange={change}
                  required
                />
              </label>
            </div>
            <div className="row">
              <label>
                Data de compra
                <input
                  className="input"
                  name="data_compra"
                  type="date"
                  value={form.data_compra}
                  onChange={change}
                  required
                />
              </label>
              <label>
                Validade
                <input
                  className="input"
                  name="validade"
                  type="date"
                  value={form.validade}
                  onChange={change}
                  required
                />
              </label>
            </div>
            <div className="row">
              <label>
                Estoque
                <input
                  className="input"
                  name="estoque"
                  type="number"
                  min="0"
                  value={form.estoque}
                  onChange={change}
                  required
                />
              </label>
              <label>
                Descrição
                <input className="input" name="descricao" value={form.descricao} onChange={change} />
              </label>
            </div>
            <div className="form-actions">
              <button type="button" className="btn ghost" onClick={() => setForm(null)}>
                Cancelar
              </button>
              <button type="submit" className="btn primary">
                Salvar
              </button>
            </div>
          </form>
        </Modal>
      )}

      {linkTarget && (
        <Modal
          title={`Vincular fornecedor - ${linkTarget.nome}`}
          onClose={() => setLinkTarget(null)}
        >
          <form className="form" onSubmit={submitLink}>
            <label>
              Fornecedor
              <select className="input" name="supplier" required>
                <option value="">Selecione...</option>
                {suppliers.map((supplier) => (
                  <option key={supplier.id} value={supplier.id}>
                    {supplier.nome}
                  </option>
                ))}
              </select>
            </label>
            <div className="form-actions">
              <button type="button" className="btn ghost" onClick={() => setLinkTarget(null)}>
                Cancelar
              </button>
              <button type="submit" className="btn primary">
                Vincular
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
