import { getClassColor } from "../utils/classes.js";

export default function DetectionBox({
  imageUrl,
  imageWidth,
  imageHeight,
  detections = [],
  overlayOnly = false,
}) {
  if (!overlayOnly && !imageUrl) return null;

  const hasSize = imageWidth > 0 && imageHeight > 0;

  const overlay = (
    <>
      {hasSize &&
        detections.map((det, idx) => {
          const { x1, y1, x2, y2 } = det.bbox;
          const left = (x1 / imageWidth) * 100;
          const top = (y1 / imageHeight) * 100;
          const width = ((x2 - x1) / imageWidth) * 100;
          const height = ((y2 - y1) / imageHeight) * 100;
          const color = getClassColor(det.class_name);

          return (
            <div
              key={`${det.class_name}-${idx}`}
              className="detection-box"
              style={{
                left: `${left}%`,
                top: `${top}%`,
                width: `${width}%`,
                height: `${height}%`,
                borderColor: color,
              }}
            >
              <span
                className="detection-box-label"
                style={{ backgroundColor: color }}
              >
                {det.class_name} {(det.confidence * 100).toFixed(0)}%
              </span>
            </div>
          );
        })}
    </>
  );

  if (overlayOnly) {
    return <div className="detection-overlay">{overlay}</div>;
  }

  return (
    <div className="detection-canvas">
      <img src={imageUrl} alt="Preview" className="detection-image" />
      {overlay}
    </div>
  );
}