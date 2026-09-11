"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import {
  fmtInt,
  fmtPct,
  riskCategory,
  riskColor,
} from "@/lib/format";
import {
  Card,
  ErrorState,
  InfoPanel,
  MetricCard,
  RiskBadge,
  Spinner,
  SeverityBadge,
} from "@/components/ui";
import { CasesLineChart, RiskByRegionChart } from "@/components/charts";

const RiskMap = dynamic(() => import("@/components/RiskMap").then((m) => m.RiskMap), {
  ssr: false,
});

export default function DashboardPage() {
  const summary = useApi(() => api.dashboardSummary());
  const predictions = useApi(() => api.predictions());
  const priority = useApi(() => api.priority());
  const series = useApi(() => api.casesTimeseries());
  const alerts = useApi(() => api.alerts());

  if (summary.status === "loading" || predictions.status === "loading") {
    return <Spinner />;
  }
  if (summary.status === "error" || predictions.status === "error") {
    return <ErrorState message={summary.error ?? predictions.error ?? "unknown"} />;
  }

  const s = summary.data;
  const priRows = priority.data ?? [];
  const alertRows = alerts.data ?? [];
  const mapPoints = priRows.map((row) => ({
    id: row.id,
    name: row.name,
    latitude: row.latitude,
    longitude: row.longitude,
    probability: row.outbreak_probability,
    category: riskCategory(row.outbreak_probability),
    severity: row.severity,
    population: row.population,
  }));
  const sorted = priRows.slice().sort((a, b) => b.priority_score - a.priority_score);
  const critical = alertRows.filter((a) => a.level === "critical").slice(0, 6);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">National Outbreak Dashboard</h1>
        <p className="text-sm text-slate-500">
          Synthetic dengue surveillance, India · latest week ending {s.as_of_date} ·{" "}
          {s.demo_data_disclaimer}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
        <MetricCard label="Regions" value={fmtInt(s.regions_count)} hint="monitored" />
        <MetricCard
          label="High risk (≥50%)"
          value={fmtInt(s.high_risk_regions)}
          color="text-red-600"
          hint="predicted next week"
        />
        <MetricCard
          label="Critical severity"
          value={fmtInt(s.critical_regions)}
          color="text-orange-600"
          hint="composite score"
        />
        <MetricCard
          label="Latest week cases"
          value={fmtInt(s.latest_week_cases)}
          color="text-emerald-700"
          hint="reported"
        />
        <MetricCard
          label="Avg risk"
          value={fmtPct(s.avg_probability)}
          color="text-slate-900"
          hint="across regions"
        />
        <MetricCard label="Critical alerts" value={fmtInt(s.alerts_count)} color="text-red-600" hint="actionable" />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-5">
        <Card
          title="Predicted outbreak risk by region"
          subtitle={`next 7 days · risk from Random Forest (probabilities reflect base rates)`}
          className="xl:col-span-3"
        >
          <RiskMap points={mapPoints} height={460} />
        </Card>

        <Card title="Top priority regions" subtitle="ranked for resource allocation" className="xl:col-span-2">
          <div className="space-y-3">
            {sorted.slice(0, 6).map((row) => (
              <div key={row.id} className="rounded-lg border border-slate-200 p-3">
                <div className="flex items-center justify-between">
                  <Link href={`/predictions/${row.id}`} className="text-sm font-semibold text-slate-800 hover:text-emerald-700">
                    {row.name}
                  </Link>
                  <span className="text-sm font-bold text-slate-900">{row.priority_score}</span>
                </div>
                <div className="mt-1 flex items-center gap-2 text-xs">
                  <RiskBadge category={riskCategory(row.outbreak_probability)} />
                  <SeverityBadge band={row.severity} />
                  <span className="text-slate-500">{(row.outbreak_probability * 100).toFixed(1)}% risk</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card title="Weekly reported cases (national)" subtitle="synthetic dengue cases per week">
          {series.status === "success" ? (
            <CasesLineChart data={series.data} />
          ) : (
            <p className="text-sm text-slate-400">No data</p>
          )}
        </Card>

        <Card title="Critical alerts" subtitle="auto-generated from predicted risk and severity">
          {critical.length === 0 ? (
            <p className="text-sm text-slate-400">No critical alerts.</p>
          ) : (
            <div className="space-y-2">
              {critical.map((a, i) => (
                <div key={i} className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-2.5">
                  <span
                    className="mt-0.5 h-2 w-2 shrink-0 rounded-full"
                    style={{ backgroundColor: riskColor(riskCategory(a.probability)) }}
                  />
                  <p className="text-xs text-red-800">{a.message}</p>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card title="Predicted risk by region" subtitle="% probability of a high-incidence event next week">
          {priRows.length ? (
            <RiskByRegionChart data={priRows} />
          ) : (
            <p className="text-sm text-slate-400">No data</p>
          )}
        </Card>
        <div className="space-y-4">
          <InfoPanel title="How risk is computed">
            <p>
              A Random Forest predicts the probability that a region will experience a{" "}
              <em>high-incidence event</em> one week ahead using only data available up to
              the current week (rolling case averages, growth, climate and population
              features). The probability is converted to a risk category using the bands
              Low (0–29%), Moderate (30–49%), High (50–69%) and Very High (70–100%).
            </p>
          </InfoPanel>
          <Card title="Risk legend">
            <div className="flex flex-wrap gap-3">
              {(["Low", "Moderate", "High", "Very High"] as const).map((c) => (
                <span key={c} className="inline-flex items-center gap-1.5 text-xs text-slate-600">
                  <span className="h-3 w-3 rounded-full" style={{ backgroundColor: riskColor(c) }} />
                  {c}
                </span>
              ))}
            </div>
            <div className="mt-3 text-xs text-slate-500">
              Bubble size on the map reflects the predicted probability; colour is the risk
              category. Severity is a composite score (see the Predictions page).
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}