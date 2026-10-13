import { useMemo, useState } from "react";
import { api, formatBRL } from "../api.js";

export default function Alerts({ products, onChange }) {
  const [threshold, setThreshold] = useState(25);
  const [message, setMessage] = useState("");

  const expired = useMemo(() => products.filter((p) => p.status === "vencido"), [products]);
  const expiring = useMemo(() => products.filter((p) => p.status === "proximo"), [products]);
  const lowStock = useMemo(
    () => products.filter((p) => p.estoque < threshold).sort((a, b) => a.estoque - b.estoque),
    [products, threshold]
  );

  const notify = (text) => {
    setMessage(text);
    setTimeout(() => setMessage(""), 3000);
  };

  const updateStock = async (product, delta) => {
    await api.patch(`/api/products/${product.id}/`, { estoque: product.estoque + delta });
    notify(`Estoque de ${product.nome} atualizado.`);
    onChange();
  };

  const remove = async (product) => {
    if (!window.confirm(`Excluir o produto "${product.nome}"?`)) return;
    await api.del(`/api/products/${product.id}/`);
    notify("Produto excluído.");
    onChange();
  };

  const section = (title, items, className, emptyText) => (
    <section className="panel">
      <h2>
        {title} <span className="count">{items.length}</span>
      </h2>
      {items.length === 0 ? (
        <p className="muted">{emptyText}</p>
      ) : (
        <div className="alert-list">
          {items.map((product) => (
            <article key={product.id} className={`alert-item ${className}`}>
              <div>
                <strong>{product.nome}</strong>
                <small>
                  Validade {product.validade} · Estoque {product.estoque} un. ·{" "}
                  {formatBRL(product.preco)}
                </small>
              </div>
              <div className="actions">
                <button className="btn small" onClick={() => updateStock(product, 10)}>
                  +10 un.
                </button>
                <button
                  className="btn small ghost"
                  disabled={product.estoque === 0}
                  onClick={() => updateStock(product, -Math.min(10, product.estoque))}
                >
                  -10 un.
                </button>
                <button className="btn small danger" onClick={() => remove(product)}>
                  Excluir
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );

  return (
    <div className="dashboard">
      {message && <div className="banner info">{message}</div>}

      <div className="toolbar">
        <label className="inline">
          Estoque mínimo:
          <input
            className="input narrow"
            type="number"
            min="0"
            value={threshold}
            onChange={(event) => setThreshold(Number(event.target.value))}
          />
        </label>
        <span className="muted">Produtos abaixo do mínimo aparecem na lista de reposição.</span>
      </div>

      {section("Produtos vencidos", expired, "danger", "Nenhum produto vencido. Tudo em dia.")}
      {section("Vencendo em até 30 dias", expiring, "warning", "Nenhum produto perto do vencimento.")}
      {section("Reposição de estoque", lowStock, "warning", "Nenhum produto abaixo do mínimo.")}
    </div>
  );
}
