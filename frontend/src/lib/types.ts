export type RiskCategory = "Low" | "Moderate" | "High" | "Very High";

export interface Region {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  population: number;
  population_density: number;
}

export interface HealthCenter {
  id: number;
  name: string;
  region_id: number | null;
  latitude: number;
  longitude: number;
}

export interface Prediction {
  region: string;
  region_name: string;
  observation_date: string;
  prediction_date: string;
  probability: number;
  probability_lr: number;
  risk_category: RiskCategory;
  severity_band: SeverityBand;
  severity_score: number;
  priority_score: number;
}

export type SeverityBand = "LOW" | "MODERATE" | "HIGH" | "CRITICAL";

export interface PriorityRow {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  population: number;
  assessment_date: string;
  severity: SeverityBand;
  severity_score: number;
  priority_score: number;
  factors: string;
  outbreak_probability: number;
  risk_category: RiskCategory;
}

export interface Alert {
  level: "critical" | "high";
  type: "risk" | "severity";
  region: string;
  message: string;
  probability: number;
}

export interface DashboardSummary {
  as_of_date: string;
  regions_count: number;
  high_risk_regions: number;
  critical_regions: number;
  latest_week_cases: number;
  latest_week_deaths: number;
  avg_probability: number;
  alerts_count: number;
  demo_data_disclaimer: string;
}

export interface Attribution {
  feature: string;
  value: number;
  shift_std: number;
  delta_pp: number;
  direction: "pushes_risk_up" | "pushes_risk_down";
}

export interface Explainability {
  region: string;
  base_probability_pct: number;
  attributions: Attribution[];
  methodology: string;
}

export interface PredictionDetail {
  region_id: number;
  region_name: string;
  latitude: number;
  longitude: number;
  population: number;
  observation_date: string;
  prediction_date: string;
  probability: number;
  risk_category: RiskCategory;
  severity_band: SeverityBand;
  severity_score: number;
  priority_score: number;
  severity_factors: Record<string, number>;
  label_methodology: string;
  severity_methodology: string;
  priority_methodology: string;
  demo_data_disclaimer: string;
  explainability: Explainability;
}

export interface Recommendation {
  action: string;
  reason: string;
  source_rule: string;
  date: string;
}

export interface ModelMetricsEntry {
  model: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  roc_auc: number;
  n_train: number;
  n_positive: number;
}

export interface ModelPerformance {
  metrics: { models: ModelMetricsEntry[] };
  metadata: {
    disease: string;
    label_column: string;
    label_definition: string;
    features: string[];
    trained_at: string;
    train_rows: number;
    test_rows: number;
    random_state: number;
    oob_score: number;
  };
  feature_importance: { feature: string; importance: string }[];
  figures: string[];
  label_methodology: string;
  severity_methodology: string;
  priority_methodology: string;
  explainability_methodology: string;
  risk_bands: { label: string; min: number; max: number; color: string }[];
}

export interface DatasetInfo {
  disease: string;
  demo_data_disclaimer: string;
  label_methodology: string;
  observations: number;
  regions: number;
  date_range: { first: string; last: string };
  total_cases: number;
  source_files: string[];
  synthetic_notice: string;
}

export interface CasePoint {
  date: string;
  total_cases: number;
  total_deaths: number;
}

export interface HistoryPoint {
  date: string;
  reported_cases: number;
  previous_week_cases: number;
  previous_month_cases: number;
  deaths: number;
  temperature: number;
  rainfall: number;
  humidity: number;
  water_accumulation_index: number;
}

export interface DatasetRow {
  date: string;
  region: string;
  reported_cases: number;
  previous_week_cases: number;
  deaths: number;
  temperature: number;
  rainfall: number;
  humidity: number;
  water_accumulation_index: number;
  population_density: number;
}

export interface GraphNode {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
}

export interface GraphEdge {
  from: string;
  to: string;
  distance_km: number;
  travel_time_min: number;
}

export interface RouteGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
  counts: { nodes: number; edges: number };
}

export interface RouteResult {
  start_node: string;
  goal_node: string;
  weight: "time" | "distance";
  dijkstra: RouteAlgorithmResult;
  astar: RouteAlgorithmResult;
  nodes: GraphNode[];
  edges: GraphEdge[];
  comparison: { dijkstra_explored: number | null; astar_explored: number | null };
}

export interface RouteAlgorithmResult {
  path: string[];
  total_weight: number | null;
  total_distance: number | null;
  total_time: number | null;
  unit: "time" | "distance";
  explored: number;
  nodes_visited?: number;
  error: string | null;
}