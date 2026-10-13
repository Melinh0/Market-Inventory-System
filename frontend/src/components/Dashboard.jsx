import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatBRL } from "../api.js";

const PALETTE = ["#22d3ee", "#a78bfa", "#f472b6", "#facc15", "#34d399", "#fb923c"];
const STATUS_LABEL = { vencido: "Vencidos", proximo: "A vencer", ok: "No prazo" };

export default function Dashboard({ dashboard }) {
  const [hover, setHover] = useState(null);

  if (!dashboard) return <p className="muted">Carregando dados...</p>;

  const { resumo, validade, categorias, top_valor, fornecedores, estoque_baixo_lista } = dashboard;
  const statusData = Object.entries(validade).map(([key, value]) => ({
    name: STATUS_LABEL[key],
    value,
    key,
  }));

  const cards = [
    { label: "Produtos", value: resumo.produtos },
    { label: "Fornecedores", value: resumo.fornecedores },
    { label: "Unidades em estoque", value: resumo.unidades },
    { label: "Valor do estoque", value: formatBRL(resumo.valor_estoque) },
    { label: "Produtos vencidos", value: resumo.vencidos, danger: resumo.vencidos > 0 },
    { label: "Estoque baixo", value: resumo.estoque_baixo, danger: resumo.estoque_baixo > 0 },
  ];

  return (
    <div className="dashboard">
      <section className="cards">
        {cards.map((card) => (
          <article key={card.label} className={card.danger ? "card danger" : "card"}>
            <span>{card.label}</span>
            <strong>{card.value}</strong>
          </article>
        ))}
      </section>

      <section className="grid">
        <article className="panel">
          <h2>Valor imobilizado por produto</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={top_valor}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="nome" stroke="#94a3b8" tick={{ fontSize: 11 }} />
              <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
              <Tooltip
                formatter={(value, name) =>
                  name === "valor" ? [formatBRL(value), "Valor"] : [value, name]
                }
                contentStyle={{ background: "#0f172a", border: "1px solid #334155" }}
              />
              <Bar dataKey="valor" fill="#22d3ee" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </article>

        <article className="panel">
          <h2>Situação das validades</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={statusData}
                dataKey="value"
                nameKey="name"
                innerRadius={70}
                outerRadius={110}
                paddingAngle={4}
                onMouseEnter={(_, index) => setHover(index)}
                onMouseLeave={() => setHover(null)}
              >
                {statusData.map((entry, index) => (
                  <Cell
                    key={entry.key}
                    fill={PALETTE[index % PALETTE.length]}
                    opacity={hover === null || hover === index ? 1 : 0.35}
                  />
                ))}
              </Pie>
              <Legend />
              <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155" }} />
            </PieChart>
          </ResponsiveContainer>
        </article>

        <article className="panel">
          <h2>Estoque por categoria</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={categorias}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="categoria" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip
                formatter={(value, name) =>
                  name === "valor" ? [formatBRL(value), "Valor em estoque"] : [value, name]
                }
                contentStyle={{ background: "#0f172a", border: "1px solid #334155" }}
              />
              <Legend />
              <Bar dataKey="estoque" fill="#a78bfa" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </article>

        <article className="panel">
          <h2>Produtos por fornecedor</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={fornecedores}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="nome" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" allowDecimals={false} />
              <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155" }} />
              <Bar dataKey="produtos" fill="#f472b6" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </article>
      </section>

      <section className="panel">
        <h2>Itens com estoque baixo</h2>
        {estoque_baixo_lista.length === 0 ? (
          <p className="muted">Nenhum item abaixo do mínimo.</p>
        ) : (
          <div className="chips">
            {estoque_baixo_lista.map((item) => (
              <span key={item.id} className="chip warning">
                {item.nome}: {item.estoque} un.
              </span>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
