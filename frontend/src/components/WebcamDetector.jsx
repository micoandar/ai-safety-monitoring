import { useCallback, useEffect, useRef, useState } from "react";

import DetectionBox from "./DetectionBox.jsx";
import DetectionResult from "./DetectionResult.jsx";
import { detectFrame } from "../services/api.js";

// Throttle: kirim frame ke backend setiap X ms
// 400 ms ≈ 2.5 FPS (sesuai spec Phase 6, batas aman untuk CPU backend)
const FRAME_INTERVAL_MS = 400;

export default function WebcamDetector() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const intervalRef = useRef(null);
  const streamRef = useRef(null);
  const inFlightRef = useRef(false);
  const frameTimestampsRef = useRef([]);

  const [active, setActive] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [fps, setFps] = useState(0);
  const [videoSize, setVideoSize] = useState({ width: 0, height: 0 });

  const stopCamera = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    frameTimestampsRef.current = [];
    setActive(false);
    setFps(0);
  }, []);

  useEffect(() => {
    return () => stopCamera();
  }, [stopCamera]);

  const captureAndSend = useCallback(async () => {
    if (inFlightRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.readyState < 2) return;

    const w = video.videoWidth;
    const h = video.videoHeight;
    if (!w || !h) return;

    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, w, h);

    inFlightRef.current = true;

    canvas.toBlob(
      async (blob) => {
        if (!blob) {
          inFlightRef.current = false;
          return;
        }
        try {
          const data = await detectFrame(blob);
          data.image = { width: w, height: h };
          setResult(data);

          // Hitung throughput sebenarnya: jumlah frame yang selesai diproses
          // dalam 1 detik terakhir (bukan 1/inference_time)
          const now = performance.now();
          frameTimestampsRef.current.push(now);
          frameTimestampsRef.current = frameTimestampsRef.current.filter(
            (t) => now - t <= 1000
          );
          setFps(frameTimestampsRef.current.length);
        } catch (err) {
          setError(err.message || "Gagal memproses frame.");
        } finally {
          inFlightRef.current = false;
        }
      },
      "image/jpeg",
      0.7
    );
  }, []);

  const startCamera = useCallback(async () => {
    setError(null);
    setStarting(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setActive(true);
      intervalRef.current = setInterval(captureAndSend, FRAME_INTERVAL_MS);
    } catch (err) {
      const msg =
        err.name === "NotAllowedError"
          ? "Izin kamera ditolak. Buka setting browser → izinkan akses kamera."
          : err.name === "NotFoundError"
          ? "Kamera tidak ditemukan di perangkat ini."
          : err.message || "Gagal mengakses kamera.";
      setError(msg);
    } finally {
      setStarting(false);
    }
  }, [captureAndSend]);

  const handleVideoLoaded = () => {
    const v = videoRef.current;
    if (v) setVideoSize({ width: v.videoWidth, height: v.videoHeight });
  };

  return (
    <div className="webcam-layout">
      <div className="webcam-column">
        <div className="webcam-stage">
          <video
            ref={videoRef}
            className="webcam-video"
            playsInline
            muted
            onLoadedMetadata={handleVideoLoaded}
          />
          {active && result && (
            <DetectionBox
              imageUrl={null}
              imageWidth={videoSize.width}
              imageHeight={videoSize.height}
              detections={result.detections ?? []}
              overlayOnly
            />
          )}

          {!active && (
            <div className="webcam-placeholder">
              <p className="placeholder-title">Kamera belum aktif</p>
              <span>Klik "Start Camera" untuk memulai deteksi real-time.</span>
            </div>
          )}

          {active && (
            <div className="webcam-overlay-status">
              <span className="badge badge-success">● LIVE</span>
              <span className="webcam-fps">
                {fps} FPS · {result?.inference_time_ms?.toFixed(0) ?? "—"} ms
              </span>
            </div>
          )}
        </div>

        <canvas ref={canvasRef} style={{ display: "none" }} />

        <div className="upload-actions">
          {!active ? (
            <button
              type="button"
              className="btn btn-primary"
              onClick={startCamera}
              disabled={starting}
            >
              {starting ? "Menyiapkan…" : "Start Camera"}
            </button>
          ) : (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={stopCamera}
            >
              Stop Camera
            </button>
          )}
        </div>

        {error && <div className="alert alert-error">{error}</div>}
      </div>

      <div className="result-column">
        {result ? (
          <DetectionResult result={result} />
        ) : (
          <div className="placeholder">
            <p className="placeholder-title">Belum ada frame</p>
            <span>Hasil deteksi akan muncul setelah kamera aktif.</span>
          </div>
        )}
      </div>
    </div>
  );
}