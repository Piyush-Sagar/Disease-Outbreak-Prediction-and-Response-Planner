"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { fmtInt, fmtPct } from "@/lib/format";
import {
  Card,
  ErrorState,
  InfoPanel,
  RiskBadge,
  RiskBar,
  SeverityBadge,
  Spinner,
  StatLine,
} from "@/components/ui";

export default function PredictionDetailPage() {
  const params = useParams<{ id: string }>();
  const id = Number(params.id);
  const detail = useApi(() => api.predictionDetail(id), [id]);
  const recommendations = useApi(() => api.recommendations(id), [id]);

  if (detail.status === "error" && detail.data == null) return <ErrorState message={detail.error} />;
  if (detail.status === "loading" || detail.data == null) return <Spinner />;

  const d = detail.data;
  const drivers = d.explainability.attributions ?? [];
  const topUp = drivers
    .filter((a) => a.direction === "pushes_risk_up")
    .sort((a, b) => b.delta_pp - a.delta_pp)
    .slice(0, 5);
  const topDown = drivers
    .filter((a) => a.direction === "pushes_risk_down")
    .sort((a, b) => a.delta_pp - b.delta_pp)
    .slice(0, 5);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <Link href="/predictions" className="text-xs font-medium text-emerald-700 hover:underline">
            ← All predictions
          </Link>
          <h1 className="mt-1 text-xl font-bold text-slate-900">{d.region_name}</h1>
          <p className="text-sm text-slate-500">
            Prediction for week of {d.prediction_date} · based on data through {d.observation_date}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <RiskBadge category={d.risk_category} />
          <SeverityBadge band={d.severity_band} />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card>
          <p className="text-xs font-medium uppercase text-slate-500">Predicted outbreak risk</p>
          <p className="mt-1 text-3xl font-bold text-slate-900">{fmtPct(d.probability)}</p>
          <p className="mt-1 text-xs text-slate-500">next 7 days</p>
          <div className="mt-2">
            <RiskBar probability={d.probability} />
          </div>
        </Card>
        <Card>
          <p className="text-xs font-medium uppercase text-slate-500">Severity score</p>
          <p className="mt-1 text-3xl font-bold text-slate-900">{d.severity_score.toFixed(2)}</p>
          <p className="mt-1 text-xs text-slate-500">
            band <strong>{d.severity_band}</strong> · composite 0–1
          </p>
        </Card>
        <Card>
          <p className="text-xs font-medium uppercase text-slate-500">Priority score</p>
          <p className="mt-1 text-3xl font-bold text-slate-900">{d.priority_score.toFixed(1)}</p>
          <p className="mt-1 text-xs text-slate-500">resource-allocation rank (0–100)</p>
        </Card>
        <Card>
          <p className="text-xs font-medium uppercase text-slate-500">Population</p>
          <p className="mt-1 text-3xl font-bold text-slate-900">{fmtInt(d.population)}</p>
          <p className="mt-1 text-xs text-slate-500">affected community size</p>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card title="Severity factor breakdown" subtitle="how the severity score is composed">
          {Object.entries(d.severity_factors ?? {}).map(([key, value]) => (
            <StatLine
              key={key}
              label={key.replaceAll("_", " ")}
              value={typeof value === "number" ? value.toFixed(3) : String(value)}
            />
          ))}
          <p className="mt-3 text-xs leading-relaxed text-slate-500">{d.severity_methodology}</p>
        </Card>

        <Card
          title="Recommended response actions"
          subtitle={`rule-based plan for ${d.severity_band} severity`}
        >
          {recommendations.status === "success" ? (
            <div className="space-y-2">
              {recommendations.data.map((r, i) => (
                <div key={i} className="rounded-lg border border-slate-200 p-2.5">
                  <p className="text-sm font-semibold text-slate-800">{r.action}</p>
                  <p className="mt-0.5 text-xs text-slate-500">{r.reason}</p>
                </div>
              ))}
            </div>
          ) : recommendations.status === "error" ? (
            <p className="text-sm text-red-600">{recommendations.error}</p>
          ) : (
            <Spinner />
          )}
        </Card>
      </div>

      <Card
        title="What drives this prediction?"
        subtitle="feature attribution via one-standard-deviation perturbation (demo)"
      >
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
              Pushing risk up
            </p>
            <div className="mt-2 space-y-2">
              {topUp.length === 0 && <p className="text-sm text-slate-400">None above threshold.</p>}
              {topUp.map((a) => (
                <div key={a.feature} className="flex items-center justify-between text-sm">
                  <span className="text-slate-700">{a.feature}</span>
                  <span className="tabular-nums text-emerald-700">
                    +{a.delta_pp.toFixed(1)} pp
                  </span>
                </div>
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-red-700">
              Pushing risk down
            </p>
            <div className="mt-2 space-y-2">
              {topDown.length === 0 && <p className="text-sm text-slate-400">None above threshold.</p>}
              {topDown.map((a) => (
                <div key={a.feature} className="flex items-center justify-between text-sm">
                  <span className="text-slate-700">{a.feature}</span>
                  <span className="tabular-nums text-red-700">
                    {a.delta_pp.toFixed(1)} pp
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
        <p className="mt-4 text-xs leading-relaxed text-slate-500">{d.explainability.methodology}</p>
      </Card>

      <InfoPanel title="Methodology">
        <p>{d.label_methodology}</p>
        <p className="pt-1 text-amber-700">{d.demo_data_disclaimer}</p>
      </InfoPanel>
    </div>
  );
}