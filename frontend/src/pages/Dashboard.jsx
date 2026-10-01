import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import StatCard from "../components/StatCard.jsx";
import { getDashboardStats } from "../services/api.js";

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await getDashboardStats();
        if (!cancelled) setStats(data);
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <>
        <header className="page-header">
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">
            Ringkasan monitoring kepatuhan PPE di tempat kerja.
          </p>
        </header>
        <div className="placeholder">
          <p className="placeholder-title">Memuat statistik…</p>
          <span>Menghubungi server.</span>
        </div>
      </>
    );
  }

  if (error) {
    return (
      <>
        <header className="page-header">
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">
            Ringkasan monitoring kepatuhan PPE di tempat kerja.
          </p>
        </header>
        <div className="alert alert-error">
          Gagal memuat statistik: {error}
        </div>
      </>
    );
  }

  const hasData = stats?.total_detections > 0;

  return (
    <>
      <header className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">
          Ringkasan monitoring kepatuhan PPE di tempat kerja.
        </p>
      </header>

      <section className="grid-stats">
        <StatCard
          label="Total Detections"
          value={stats.total_detections}
          hint="Sesi deteksi tersimpan"
        />
        <StatCard
          label="Workers Detected"
          value={stats.total_workers}
          hint="Total person terdeteksi"
        />
        <StatCard
          label="Compliant"
          value={stats.total_compliant}
          hint="Pekerja patuh PPE"
        />
        <StatCard
          label="Violations"
          value={stats.total_violations}
          hint="Pelanggaran PPE"
        />
        <StatCard
          label="Compliance Rate"
          value={`${stats.compliance_rate}%`}
          hint="Rata-rata keseluruhan"
        />
      </section>

      <section className="card dashboard-chart-card">
        <h2 className="card-title">Aktivitas 7 Hari Terakhir</h2>
        <p className="card-description">
          Jumlah deteksi dan pelanggaran per hari.
        </p>
        {hasData ? (
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={stats.trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="label" stroke="#6b7280" fontSize={12} />
                <YAxis stroke="#6b7280" fontSize={12} allowDecimals={false} />
                <Tooltip
                  contentStyle={{
                    borderRadius: 8,
                    border: "1px solid #e5e7eb",
                    fontSize: 13,
                  }}
                />
                <Legend wrapperStyle={{ fontSize: 13 }} />
                <Bar
                  dataKey="total"
                  name="Detections"
                  fill="#2563eb"
                  radius={[4, 4, 0, 0]}
                />
                <Bar
                  dataKey="violations"
                  name="Violations"
                  fill="#ef4444"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="placeholder">
            <p className="placeholder-title">Belum ada data</p>
            <span>Mulai deteksi untuk melihat tren di sini.</span>
          </div>
        )}
      </section>

      <section className="card dashboard-recent-card">
        <h2 className="card-title">Deteksi Terbaru</h2>
        <p className="card-description">5 deteksi terakhir yang tersimpan.</p>
        {stats.recent.length === 0 ? (
          <div className="placeholder">
            <p className="placeholder-title">Belum ada deteksi</p>
            <span>History akan muncul setelah deteksi pertama.</span>
          </div>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Waktu</th>
                  <th>Workers</th>
                  <th>Compliant</th>
                  <th>Violations</th>
                  <th>Rate</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {stats.recent.map((row) => (
                  <tr key={row.id}>
                    <td>#{row.id}</td>
                    <td>{new Date(row.detected_at).toLocaleString()}</td>
                    <td>{row.total_person}</td>
                    <td>{row.compliant_count}</td>
                    <td>{row.violation_count}</td>
                    <td>{row.compliance_rate}%</td>
                    <td>
                      <span
                        className={
                          "badge " +
                          (row.overall_status === "Compliant"
                            ? "badge-success"
                            : row.overall_status === "Violation"
                            ? "badge-danger"
                            : "badge-warning")
                        }
                      >
                        {row.overall_status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}