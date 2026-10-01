import { useCallback, useEffect, useState } from "react";

import {
  deleteDetection,
  getDetectionDetail,
  getHistory,
} from "../services/api.js";

const PAGE_SIZE = 10;

export default function History() {
  const [page, setPage] = useState(1);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  const load = useCallback(async (p) => {
    setLoading(true);
    setError(null);
    try {
      const res = await getHistory(p, PAGE_SIZE);
      setData(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(page);
  }, [page, load]);

  const handleOpenDetail = async (id) => {
    setDetailLoading(true);
    try {
      const res = await getDetectionDetail(id);
      setDetail(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCloseDetail = () => setDetail(null);

  const handleDelete = async (id) => {
    if (!window.confirm(`Hapus deteksi #${id}?`)) return;
    setDeletingId(id);
    try {
      await deleteDetection(id);
      // Reload current page; kalau sudah kosong dan bukan page 1, mundur
      const newData = await getHistory(page, PAGE_SIZE);
      if (newData.items.length === 0 && page > 1) {
        setPage(page - 1);
      } else {
        setData(newData);
      }
      if (detail?.id === id) setDetail(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setDeletingId(null);
    }
  };

  const totalPages = data?.total_pages ?? 0;
  const items = data?.items ?? [];

  return (
    <>
      <header className="page-header">
        <h1 className="page-title">History</h1>
        <p className="page-subtitle">
          Riwayat deteksi PPE yang tersimpan di database.
        </p>
      </header>

      {error && <div className="alert alert-error">{error}</div>}

      <section className="card">
        <div className="history-header">
          <div>
            <h2 className="card-title">Riwayat Deteksi</h2>
            <p className="card-description">
              Total {data?.total ?? 0} deteksi tersimpan.
            </p>
          </div>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => load(page)}
            disabled={loading}
          >
            {loading ? "Memuat…" : "Refresh"}
          </button>
        </div>

        {loading && !data ? (
          <div className="placeholder">
            <p className="placeholder-title">Memuat data…</p>
          </div>
        ) : items.length === 0 ? (
          <div className="placeholder">
            <p className="placeholder-title">Belum ada data</p>
            <span>Lakukan deteksi untuk melihat riwayat.</span>
          </div>
        ) : (
          <>
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
                    <th className="table-actions-col">Aksi</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((row) => (
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
                      <td className="table-actions-col">
                        <button
                          type="button"
                          className="btn-link"
                          onClick={() => handleOpenDetail(row.id)}
                        >
                          Detail
                        </button>
                        <button
                          type="button"
                          className="btn-link btn-link-danger"
                          onClick={() => handleDelete(row.id)}
                          disabled={deletingId === row.id}
                        >
                          {deletingId === row.id ? "…" : "Hapus"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="pagination">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1 || loading}
              >
                ← Sebelumnya
              </button>
              <span className="pagination-info">
                Halaman {page} dari {Math.max(1, totalPages)}
              </span>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() =>
                  setPage((p) => Math.min(totalPages, p + 1))
                }
                disabled={page >= totalPages || loading}
              >
                Berikutnya →
              </button>
            </div>
          </>
        )}
      </section>

      {(detail || detailLoading) && (
        <div className="modal-backdrop" onClick={handleCloseDetail}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            {detailLoading ? (
              <div className="placeholder">
                <p className="placeholder-title">Memuat detail…</p>
              </div>
            ) : (
              <>
                <div className="modal-header">
                  <h3 className="modal-title">Deteksi #{detail.id}</h3>
                  <button
                    type="button"
                    className="modal-close"
                    onClick={handleCloseDetail}
                  >
                    ✕
                  </button>
                </div>
                <div className="modal-body">
                  <div className="modal-meta">
                    <span>
                      <strong>Waktu:</strong>{" "}
                      {new Date(detail.detected_at).toLocaleString()}
                    </span>
                    <span>
                      <strong>Status:</strong>{" "}
                      <span
                        className={
                          "badge " +
                          (detail.overall_status === "Compliant"
                            ? "badge-success"
                            : detail.overall_status === "Violation"
                            ? "badge-danger"
                            : "badge-warning")
                        }
                      >
                        {detail.overall_status}
                      </span>
                    </span>
                    <span>
                      <strong>Workers:</strong> {detail.total_person}
                    </span>
                    <span>
                      <strong>Compliant:</strong> {detail.compliant_count}
                    </span>
                    <span>
                      <strong>Violations:</strong> {detail.violation_count}
                    </span>
                    <span>
                      <strong>Rate:</strong> {detail.compliance_rate}%
                    </span>
                  </div>

                  <h4 className="modal-subtitle">
                    Objects ({detail.objects.length})
                  </h4>
                  {detail.objects.length === 0 ? (
                    <p className="result-empty">Tidak ada objek.</p>
                  ) : (
                    <ul className="detection-list">
                      {detail.objects.map((obj) => (
                        <li key={obj.id} className="detection-list-item">
                          <span className="detection-list-class">
                            {obj.class_name}
                          </span>
                          <span className="detection-list-conf">
                            {(obj.confidence * 100).toFixed(1)}%
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
}