export const CLASS_COLORS = {
  person: "#2563eb",
  helmet: "#10b981",
  "no-helmet": "#ef4444",
  vest: "#8b5cf6",
  "no-vest": "#f59e0b",
};

export function getClassColor(name) {
  return CLASS_COLORS[name] || "#6b7280";
}