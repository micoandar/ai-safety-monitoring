import { getClassColor } from "../utils/classes.js";

function statusBadgeClass(status) {
  switch (status) {
    case "Compliant":
      return "badge badge-success";
    case "Violation":
      return "badge badge-danger";
    default:
      return "badge badge-warning";
  }
}

export default function DetectionResult({ result }) {
  if (!result) return null;

  const { safety, detections, image, inference_time_ms, id } = result;

  return (
    <div className="result-panel">
      <div className="result-header">
        <div className="result-header-item">
          <span className="result-label">Status</span>
          <span className={statusBadgeClass(safety.overall_status)}>
            {safety.overall_status}
          </span>
        </div>
        <div className="result-header-item">
          <span className="result-label">Detection ID</span>
          <span className="result-value">#{id ?? "—"}</span>
        </div>
        <div className="result-header-item">
          <span className="result-label">Inference</span>
          <span className="result-value">
            {inference_time_ms?.toFixed(0)} ms
          </span>
        </div>
      </div>

      <div className="result-stats">
        <div className="result-stat">
          <span className="result-stat-label">Workers</span>
          <span className="result-stat-value">{safety.total_person}</span>
        </div>
        <div className="result-stat">
          <span className="result-stat-label">Compliant</span>
          <span className="result-stat-value" style={{ color: "#047857" }}>
            {safety.compliant_count}
          </span>
        </div>
        <div className="result-stat">
          <span className="result-stat-label">Violations</span>
          <span className="result-stat-value" style={{ color: "#b91c1c" }}>
            {safety.violation_count}
          </span>
        </div>
        <div className="result-stat">
          <span className="result-stat-label">Compliance</span>
          <span className="result-stat-value">{safety.compliance_rate}%</span>
        </div>
      </div>

      {safety.violation_types?.length > 0 && (
        <div className="result-section">
          <span className="result-label">Violation Types</span>
          <div className="badges-row">
            {safety.violation_types.map((v) => (
              <span key={v} className="badge badge-danger">
                {v}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="result-section">
        <span className="result-label">
          Detected Objects ({detections.length})
        </span>
        {detections.length === 0 ? (
          <p className="result-empty">Tidak ada objek terdeteksi.</p>
        ) : (
          <ul className="detection-list">
            {detections.map((det, idx) => (
              <li key={idx} className="detection-list-item">
                <span
                  className="detection-list-dot"
                  style={{ backgroundColor: getClassColor(det.class_name) }}
                />
                <span className="detection-list-class">{det.class_name}</span>
                <span className="detection-list-conf">
                  {(det.confidence * 100).toFixed(1)}%
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="result-section">
        <span className="result-label">Image Info</span>
        <p className="result-meta">
          {image?.filename || "—"} · {image?.width}×{image?.height}px
        </p>
      </div>
    </div>
  );
}