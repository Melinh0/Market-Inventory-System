import { useCallback, useEffect, useState } from "react";
import { api } from "./api.js";
import Alerts from "./components/Alerts.jsx";
import Dashboard from "./components/Dashboard.jsx";
import Products from "./components/Products.jsx";
import Suppliers from "./components/Suppliers.jsx";

const TABS = [
  { id: "dashboard", label: "Dashboard" },
  { id: "produtos", label: "Produtos" },
  { id: "fornecedores", label: "Fornecedores" },
  { id: "alertas", label: "Alertas" },
];

export default function App() {
  const [tab, setTab] = useState("dashboard");
  const [dashboard, setDashboard] = useState(null);
  const [products, setProducts] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [error, setError] = useState("");

  const loadDashboard = useCallback(async () => {
    try {
      setDashboard(await api.get("/api/dashboard/"));
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }, []);

  const loadProducts = useCallback(async () => {
    try {
      const data = await api.get("/api/products/");
      setProducts(data.results);
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }, []);

  const loadSuppliers = useCallback(async () => {
    try {
      const data = await api.get("/api/suppliers/");
      setSuppliers(data.results);
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }, []);

  const reload = () => {
    loadDashboard();
    loadProducts();
    loadSuppliers();
  };

  useEffect(() => {
    reload();
  }, []);

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">MI</span>
          <div>
            <h1>Market Inventory System</h1>
            <p>Gestão de estoque de mercado</p>
          </div>
        </div>
        <nav className="tabs">
          {TABS.map((t) => (
            <button
              key={t.id}
              className={tab === t.id ? "tab active" : "tab"}
              onClick={() => setTab(t.id)}
            >
              {t.label}
              {t.id === "alertas" && dashboard?.resumo?.vencidos > 0 && (
                <span className="badge">{dashboard.resumo.vencidos}</span>
              )}
            </button>
          ))}
        </nav>
      </header>

      {error && <div className="banner error">{error}</div>}

      <main className="content">
        {tab === "dashboard" && <Dashboard dashboard={dashboard} />}
        {tab === "produtos" && (
          <Products
            products={products}
            suppliers={suppliers}
            onChange={reload}
          />
        )}
        {tab === "fornecedores" && (
          <Suppliers
            suppliers={suppliers}
            products={products}
            onChange={reload}
          />
        )}
        {tab === "alertas" && <Alerts products={products} onChange={reload} />}
      </main>

      <footer className="footer">
        Market Inventory System — Django + React — MIT License
      </footer>
    </div>
  );
}
