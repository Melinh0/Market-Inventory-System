import { useState } from "react";
import { api } from "../api.js";
import Modal from "./Modal.jsx";

const EMPTY = { nome: "", endereco: "", contato: "" };

export default function Suppliers({ suppliers, products, onChange }) {
  const [form, setForm] = useState(null);
  const [message, setMessage] = useState("");

  const notify = (text) => {
    setMessage(text);
    setTimeout(() => setMessage(""), 3000);
  };

  const submit = async (event) => {
    event.preventDefault();
    try {
      if (form.id) {
        await api.patch(`/api/suppliers/${form.id}/`, form);
        notify("Fornecedor atualizado com sucesso.");
      } else {
        await api.post("/api/suppliers/", form);
        notify("Fornecedor cadastrado com sucesso.");
      }
      setForm(null);
      onChange();
    } catch (err) {
      notify(err.message);
    }
  };

  const remove = async (supplier) => {
    if (!window.confirm(`Excluir o fornecedor "${supplier.nome}"?`)) return;
    await api.del(`/api/suppliers/${supplier.id}/`);
    notify("Fornecedor excluído.");
    onChange();
  };

  const change = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  return (
    <div>
      <div className="toolbar">
        <span className="muted">
          {suppliers.length} fornecedores cadastrados
        </span>
        <a className="btn ghost" href="/api/suppliers/export/">
          Exportar CSV
        </a>
        <button className="btn primary" onClick={() => setForm({ ...EMPTY })}>
          + Novo fornecedor
        </button>
      </div>

      {message && <div className="banner info">{message}</div>}

      <div className="panel">
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Nome</th>
              <th>Endereço</th>
              <th>Contato</th>
              <th>Produtos vinculados</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            {suppliers.map((supplier) => (
              <tr key={supplier.id}>
                <td>{supplier.id}</td>
                <td>
                  <strong>{supplier.nome}</strong>
                </td>
                <td>{supplier.endereco}</td>
                <td>{supplier.contato}</td>
                <td>
                  <div className="chips">
                    {supplier.produtos.length === 0 && <span className="muted">Sem vínculos</span>}
                    {supplier.produtos.map((product) => (
                      <span key={product.id} className="chip">
                        {product.nome}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="actions">
                  <button className="btn small" onClick={() => setForm({ ...supplier })}>
                    Editar
                  </button>
                  <button className="btn small danger" onClick={() => remove(supplier)}>
                    Excluir
                  </button>
                </td>
              </tr>
            ))}
            {suppliers.length === 0 && (
              <tr>
                <td colSpan="6" className="muted center">
                  Nenhum fornecedor cadastrado.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <p className="muted">
        Total de {products.length} produtos no catálogo.
      </p>

      {form && (
        <Modal title={form.id ? "Editar fornecedor" : "Novo fornecedor"} onClose={() => setForm(null)}>
          <form className="form" onSubmit={submit}>
            <label>
              Nome
              <input className="input" name="nome" value={form.nome} onChange={change} required />
            </label>
            <label>
              Endereço
              <input className="input" name="endereco" value={form.endereco} onChange={change} />
            </label>
            <label>
              Contato
              <input className="input" name="contato" value={form.contato} onChange={change} />
            </label>
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
    </div>
  );
}
