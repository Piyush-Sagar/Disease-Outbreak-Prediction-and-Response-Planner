"use client";

import { CircleMarker, MapContainer, Polyline, Popup, TileLayer, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { riskColor } from "@/lib/format";
import type { SeverityBand } from "@/lib/types";

export interface MapPoint {
  id: number | string;
  name: string;
  latitude: number;
  longitude: number;
  probability?: number;
  category?: "Low" | "Moderate" | "High" | "Very High";
  severity?: SeverityBand;
  popupLines?: { label: string; value: string }[];
  population?: number;
}

export function RiskMap({
  points,
  paths = [],
  center = [22.5, 79],
  zoom = 5,
  height = 480,
  polylineColor = "#2563eb",
}: {
  points: MapPoint[];
  paths?: [number, number][][];
  center?: [number, number];
  zoom?: number;
  height?: number;
  polylineColor?: string;
}) {
  const maxP = Math.max(1, ...points.map((p) => p.probability ?? 0));

  return (
    <div style={{ height, width: "100%" }} className="overflow-hidden rounded-xl border border-slate-200">
      <MapContainer
        center={center}
        zoom={zoom}
        scrollWheelZoom={false}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {paths.map((path, i) => (
          <Polyline
            key={i}
            positions={path as [number, number][]}
            pathOptions={{ color: polylineColor, weight: 3, opacity: 0.8 }}
          />
        ))}
        {points.map((p) => {
          const prob = p.probability ?? 0;
          const radius = 9 + Math.max(4, (prob / Math.max(maxP, 1)) * 26);
          const fill = p.category ? riskColor(p.category) : p.probability != null ? riskColor(
            prob < 0.3 ? "Low" : prob < 0.5 ? "Moderate" : prob < 0.7 ? "High" : "Very High",
          ) : "#64748b";
          return (
            <CircleMarker
              key={String(p.id)}
              center={[p.latitude, p.longitude]}
              radius={radius}
              pathOptions={{ color: "#ffffff", weight: 1.5, fillColor: fill, fillOpacity: 0.85 }}
            >
              <Tooltip direction="top" offset={[0, -6]}>
                <strong>{p.name}</strong>
              </Tooltip>
              <Popup>
                <div className="text-sm">
                  <p className="font-semibold">{p.name}</p>
                  {p.population && (
                    <p className="text-xs text-slate-500">Pop: {p.population.toLocaleString("en-IN")}</p>
                  )}
                  {p.probability != null && (
                    <p className="text-xs">
                      Risk: <strong>{(p.probability * 100).toFixed(1)}%</strong>
                    </p>
                  )}
                  {p.category && <p className="text-xs">Category: {p.category}</p>}
                  {p.severity && <p className="text-xs">Severity: {p.severity}</p>}
                  {p.popupLines?.map((l) => (
                    <p key={l.label} className="text-xs">
                      {l.label}: <strong>{l.value}</strong>
                    </p>
                  ))}
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
}