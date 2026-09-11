"use client";

import { useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { useApi } from "@/hooks/useApi";
import { api, routeResultPath } from "@/lib/api";
import { Card, ErrorState, Spinner } from "@/components/ui";
import type { RouteResult } from "@/lib/types";

const RiskMap = dynamic(() => import("@/components/RiskMap").then((m) => m.RiskMap), {
  ssr: false,
});

export default function RoutesPage() {
  const graph = useApi(() => api.routeGraph());
  const predictions = useApi(() => api.predictions());

  const cityNodes = useMemo(() => {
    if (graph.status !== "success") return [];
    return graph.data.nodes
      .filter((n) => n.id.startsWith("city-"))
      .map((n) => ({ id: n.id, label: n.name }));
  }, [graph.status, graph.data]);

  const [start, setStart] = useState("");
  const [goal, setGoal] = useState("");
  const [weight, setWeight] = useState<"time" | "distance">("time");
  const [route, setRoute] = useState<RouteResult | null>(null);
  const [computing, setComputing] = useState(false);
  const [routeError, setRouteError] = useState("");

  const g = graph.data;

  const fullNetworkPaths: [number, number][][] = useMemo(() => {
    if (!g) return [];
    const used = new Set<string>();
    const pts: [number, number][] = [];
    const byId = new Map(g.nodes.map((n) => [n.id, n]));
    for (const edge of g.edges) {
      const key = [edge.from, edge.to].sort().join("|");
      if (used.has(key)) continue;
      used.add(key);
      const a = byId.get(edge.from);
      const b = byId.get(edge.to);
      if (a && b) {
        pts.push([a.latitude, a.longitude]);
        pts.push([b.latitude, b.longitude]);
      }
    }
    return [pts];
  }, [g]);

  const runRoute = () => {
    if (!start || !goal) return;
    setComputing(true);
    setRouteError("");
    api
      .route(start, goal, weight)
      .then((res) => setRoute(res))
      .catch((e: unknown) => setRouteError(e instanceof Error ? e.message : String(e)))
      .finally(() => setComputing(false));
  };

  if (graph.status === "loading") return <Spinner />;
  if (graph.status === "error" && !graph.data) return <ErrorState message={graph.error} />;
  if (!g) return <ErrorState message="No graph data" />;

  const predByRegion = new Map((predictions.data ?? []).map((p) => [p.region_name, p]));
  const regionPoints = g.nodes
    .filter((n) => n.id.startsWith("city-"))
    .map((n) => {
      const pred = predByRegion.get(n.name);
      return {
        id: n.id,
        name: n.name,
        latitude: n.latitude,
        longitude: n.longitude,
        probability: pred?.probability,
        category: pred?.risk_category ?? undefined,
      };
    });

  const routePaths = route ? [routeResultPath(route)] : [];

  const d = route?.dijkstra;
  const a = route?.astar;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Response Routes</h1>
        <p className="text-sm text-slate-500">
          Shortest logistics path between regions using the demo road network — Dijkstra vs A*.
        </p>
      </div>

      <Card title="Route planner" subtitle={`${g.counts.nodes} nodes · ${g.counts.edges} edges`}>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
          <label className="text-sm">
            <span className="mb-1 block text-xs text-slate-500">From</span>
            <select
              value={start}
              onChange={(e) => setStart(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
            >
              <option value="">Select…</option>
              {cityNodes.map((n) => (
                <option key={n.id} value={n.id}>
                  {n.label}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            <span className="mb-1 block text-xs text-slate-500">To</span>
            <select
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
            >
              <option value="">Select…</option>
              {cityNodes.map((n) => (
                <option key={n.id} value={n.id}>
                  {n.label}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            <span className="mb-1 block text-xs text-slate-500">Optimize for</span>
            <select
              value={weight}
              onChange={(e) => setWeight(e.target.value as "time" | "distance")}
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
            >
              <option value="time">Fastest travel time</option>
              <option value="distance">Shortest distance</option>
            </select>
          </label>
          <div className="flex items-end">
            <button
              onClick={runRoute}
              disabled={!start || !goal || computing}
              className="w-full rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:opacity-40"
            >
              {computing ? "Computing…" : "Compute route"}
            </button>
          </div>
        </div>
        {routeError && <p className="mt-3 text-sm text-red-600">{routeError}</p>}
      </Card>

      <Card title="Route map" subtitle="blue = shortest path · thin lines = full road network">
        <RiskMap
          points={regionPoints}
          paths={[...routePaths, ...fullNetworkPaths]}
          polylineColor="#2563eb"
          height={460}
        />
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card title="Dijkstra result">
          {d ? (
            <div className="space-y-1 text-sm">
              <p className="flex justify-between"><span className="text-slate-500">Path length</span><span className="font-semibold">{d.path.length} nodes</span></p>
              <p className="flex justify-between"><span className="text-slate-500">Total time</span><span className="font-semibold">{d.total_time?.toFixed(0) ?? "—"} min</span></p>
              <p className="flex justify-between"><span className="text-slate-500">Total distance</span><span className="font-semibold">{d.total_distance?.toFixed(0) ?? "—"} km</span></p>
              <p className="flex justify-between"><span className="text-slate-500">Nodes explored</span><span className="font-semibold">{d.explored}</span></p>
              <div className="mt-3 rounded-lg bg-slate-50 p-2 text-xs text-slate-600">
                {d.path.join(" → ")}
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-400">No route computed yet.</p>
          )}
        </Card>

        <Card title="A* result">
          {a ? (
            <div className="space-y-1 text-sm">
              <p className="flex justify-between"><span className="text-slate-500">Path length</span><span className="font-semibold">{a.path.length} nodes</span></p>
              <p className="flex justify-between"><span className="text-slate-500">Total time</span><span className="font-semibold">{a.total_time?.toFixed(0) ?? "—"} min</span></p>
              <p className="flex justify-between"><span className="text-slate-500">Total distance</span><span className="font-semibold">{a.total_distance?.toFixed(0) ?? "—"} km</span></p>
              <p className="flex justify-between"><span className="text-slate-500">Nodes explored</span><span className="font-semibold">{a.explored}</span></p>
              <div className="mt-3 rounded-lg bg-slate-50 p-2 text-xs text-slate-600">
                {a.path.join(" → ")}
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-400">No route computed yet.</p>
          )}
        </Card>

        <Card title="Algorithm comparison">
          {d && a ? (
            <div className="space-y-2 text-sm">
              <div className="rounded-lg border border-slate-200 p-3">
                <p className="text-xs text-slate-500">Same optimal route?</p>
                <p className="mt-1 font-semibold text-slate-800">
                  {d.total_weight === a.total_weight ? "Yes — equal cost" : "No"}
                </p>
              </div>
              <div className="rounded-lg border border-slate-200 p-3">
                <p className="text-xs text-slate-500">Nodes explored</p>
                <p className="mt-1 font-semibold text-slate-800">
                  Dijkstra {d.explored} vs A* {a.explored}
                  {a.explored < d.explored ? " (A* more efficient)" : " (similar)"}
                </p>
              </div>
              <p className="text-xs leading-relaxed text-slate-500">
                Both algorithms return the provably shortest path. A* uses a
                haversine lower-bound heuristic (fastest edge speed) so it
                typically visits fewer nodes.
              </p>
            </div>
          ) : (
            <p className="text-sm text-slate-400">Compute a route to compare.</p>
          )}
        </Card>
      </div>
    </div>
  );
}