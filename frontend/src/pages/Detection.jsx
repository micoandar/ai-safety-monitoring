import { useCallback, useEffect, useRef, useState } from "react";

import DetectionBox from "../components/DetectionBox.jsx";
import DetectionResult from "../components/DetectionResult.jsx";
import WebcamDetector from "../components/WebcamDetector.jsx";
import { detectImage } from "../services/api.js";

const TABS = {
  UPLOAD: "upload",
  CAMERA: "camera",
};

export default function Detection() {
  const [tab, setTab] = useState(TABS.UPLOAD);

  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);

  const inputRef = useRef(null);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const applyFile = useCallback(
    (f) => {
      if (!f) return;
      if (!f.type.startsWith("image/")) {
        setError("File harus berupa gambar (JPG, PNG, atau WEBP).");
        return;
      }
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setFile(f);
      setPreviewUrl(URL.createObjectURL(f));
      setResult(null);
      setError(null);
    },
    [previewUrl]
  );

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files?.[0];
    applyFile(f);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => setDragOver(false);

  const handlePick = (e) => applyFile(e.target.files?.[0]);

  const handleDetect = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const data = await detectImage(file);
      setResult(data);
    } catch (err) {
      setError(err.message || "Gagal melakukan deteksi.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setFile(null);
    setPreviewUrl(null);
    setResult(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <>
      <header className="page-header">
        <h1 className="page-title">Detection</h1>
        <p className="page-subtitle">
          Deteksi penggunaan PPE melalui gambar yang diunggah atau kamera laptop.
        </p>
      </header>

      <section className="card">
        <div className="tab-row">
          <button
            type="button"
            className={"navbar-link" + (tab === TABS.UPLOAD ? " active" : "")}
            onClick={() => setTab(TABS.UPLOAD)}
          >
            Upload Image
          </button>
          <button
            type="button"
            className={"navbar-link" + (tab === TABS.CAMERA ? " active" : "")}
            onClick={() => setTab(TABS.CAMERA)}
          >
            Live Camera
          </button>
        </div>

        {tab === TABS.UPLOAD ? (
          <div className="upload-layout">
            <div className="upload-column">
              {!previewUrl ? (
                <div
                  className={
                    "dropzone" + (dragOver ? " dropzone-active" : "")
                  }
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onClick={() => inputRef.current?.click()}
                >
                  <p className="dropzone-title">Drop image di sini</p>
                  <p className="dropzone-hint">atau klik untuk memilih file</p>
                  <p className="dropzone-meta">JPG · PNG · WEBP — maks 5 MB</p>
                  <input
                    ref={inputRef}
                    type="file"
                    accept="image/*"
                    hidden
                    onChange={handlePick}
                  />
                </div>
              ) : (
                <DetectionBox
                  imageUrl={previewUrl}
                  imageWidth={result?.image?.width ?? 0}
                  imageHeight={result?.image?.height ?? 0}
                  detections={result?.detections ?? []}
                />
              )}

              <div className="upload-actions">
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={handleDetect}
                  disabled={!file || loading}
                >
                  {loading ? "Mendeteksi…" : "Detect"}
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={handleReset}
                  disabled={!file || loading}
                >
                  Reset
                </button>
                {file && (
                  <span className="file-name">
                    {file.name} · {(file.size / 1024).toFixed(0)} KB
                  </span>
                )}
              </div>

              {error && <div className="alert alert-error">{error}</div>}
            </div>

            <div className="result-column">
              {result ? (
                <DetectionResult result={result} />
              ) : (
                <div className="placeholder">
                  <p className="placeholder-title">Belum ada hasil</p>
                  <span>Upload gambar dan klik Detect untuk memulai.</span>
                </div>
              )}
            </div>
          </div>
        ) : (
          <WebcamDetector />
        )}
      </section>
    </>
  );
}