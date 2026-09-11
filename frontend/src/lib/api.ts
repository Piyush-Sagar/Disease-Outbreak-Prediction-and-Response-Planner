import type {
  Alert,
  CasePoint,
  DatasetInfo,
  DatasetRow,
  DashboardSummary,
  GraphEdge,
  GraphNode,
  HealthCenter,
  HistoryPoint,
  ModelPerformance,
  Prediction,
  PredictionDetail,
  PriorityRow,
  Recommendation,
  Region,
  RouteGraph,
  RouteResult,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function get<T>(path: string): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!resp.ok) {
    throw new Error(`GET ${path} failed (${resp.status})`);
  }
  return resp.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });
  if (!resp.ok) {
    throw new Error(`POST ${path} failed (${resp.status})`);
  }
  return resp.json() as Promise<T>;
}

export const api = {
  baseUrl: API_BASE,
  regions: () => get<Region[]>("/api/regions"),
  healthCenters: () => get<HealthCenter[]>("/api/health-centers"),
  predictions: () => get<Prediction[]>("/api/predictions"),
  priority: () => get<PriorityRow[]>("/api/regions/priority"),
  alerts: () => get<Alert[]>("/api/alerts"),
  dashboardSummary: () => get<DashboardSummary>("/api/dashboard/summary"),
  predictionDetail: (id: number) =>
    get<PredictionDetail>(`/api/predictions/${id}?explain=true`),
  recommendations: (id: number) => get<Recommendation[]>(`/api/recommendations/${id}`),
  modelPerformance: () => get<ModelPerformance>("/api/model-performance"),
  datasetInfo: () => get<DatasetInfo>("/api/dataset-info"),
  datasetRows: (limit = 15) => get<DatasetRow[]>(`/api/dataset-rows?limit=${limit}`),
  casesTimeseries: () => get<CasePoint[]>("/api/timeseries/cases"),
  regionHistory: (id: number, limit = 52) =>
    get<{ region_id: number; history: HistoryPoint[] }>(
      `/api/regions/${id}/history?limit=${limit}`,
    ),
  routeGraph: () => get<RouteGraph>("/api/route/graph"),
  route: (start: string, goal: string, weight: "time" | "distance") =>
    post<RouteResult>("/api/route", { start, goal, weight }),
};

export function graphEdgesToPath(nodes: GraphNode[], edges: GraphEdge[]): {
  path: [number, number][];
} {
  const byId = new Map(nodes.map((n) => [n.id, n]));
  const used = new Set<string>();
  const pts: [number, number][] = [];
  for (const edge of edges) {
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
  return { path: pts };
}

export function routeResultPath(result: RouteResult): [number, number][] {
  const byId = new Map(result.nodes.map((n) => [n.id, n]));
  return result.dijkstra.path
    .map((id) => {
      const n = byId.get(id);
      return n ? ([n.latitude, n.longitude] as [number, number]) : null;
    })
    .filter((p): p is [number, number] => p !== null);
}