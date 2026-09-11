"use client";

import Link from "next/link";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { fmtPct, riskCategory } from "@/lib/format";
import {
  Card,
  ErrorState,
  RiskBadge,
  RiskBar,
  SeverityBadge,
  Spinner,
  StatLine,
} from "@/components/ui";
import { RiskByRegionChart } from "@/components/charts";

export default function PredictionsPage() {
  const predictions = useApi(() => api.predictions());
  const priority = useApi(() => api.priority());

  if (predictions.status === "loading") {
    return <Spinner />;
  }
  if (predictions.status === "error" && !predictions.data) {
    return <ErrorState message={predictions.error} />;
  }

  const rows = predictions.data.slice().sort((a, b) => b.probability - a.probability);
  const idByRegion = new Map((priority.data ?? []).map((r) => [r.name, r.id]));
  const regionId = (name: string) => idByRegion.get(name) ?? 1;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Predictions</h1>
        <p className="text-sm text-slate-500">
          1-week-ahead outbreak risk for each region · as of {rows[0]?.observation_date}
        </p>
      </div>

      <Card
        title="Predicted outbreak risk"
        subtitle="Random Forest serving model + Logistic Regression baseline"
      >
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                <th className="py-2 pr-4">Region</th>
                <th className="py-2 pr-4 w-44">Risk (RF)</th>
                <th className="py-2 pr-4 w-40">Risk (LR baseline)</th>
                <th className="py-2 pr-4">Category</th>
                <th className="py-2 pr-4">Severity</th>
                <th className="py-2 pr-4">Priority</th>
                <th className="py-2" />
              </tr>
            </thead>
            <tbody>
              {rows.map((p) => (
                <tr key={p.region} className="border-b border-slate-100 last:border-0">
                  <td className="py-2.5 pr-4 font-semibold text-slate-800">{p.region_name}</td>
                  <td className="py-2.5 pr-4">
                    <RiskBar probability={p.probability} />
                  </td>
                  <td className="py-2.5 pr-4 text-xs tabular-nums text-slate-600">
                    {fmtPct(p.probability_lr)}
                  </td>
                  <td className="py-2.5 pr-4">
                    <RiskBadge category={riskCategory(p.probability)} />
                  </td>
                  <td className="py-2.5 pr-4">
                    <SeverityBadge band={p.severity_band} />
                  </td>
                  <td className="py-2.5 pr-4 text-xs font-semibold text-slate-700">
                    {p.priority_score.toFixed(1)}
                  </td>
                  <td className="py-2.5">
                    <Link
                      href={`/predictions/${regionId(p.region)}`}
                      className="text-xs font-medium text-emerald-700 hover:underline"
                    >
                      Details →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card title="Risk across regions" subtitle="predicted probability (%)">
          {priority.status === "success" ? (
            <RiskByRegionChart data={priority.data} />
          ) : (
            <p className="text-sm text-slate-400">No data</p>
          )}
        </Card>
        <Card title="Model summary">
          {rows.length > 0 && (
            <>
              <StatLine label="Regions with High/Very High risk" value={rows.filter((r) => riskCategory(r.probability) === "High" || riskCategory(r.probability) === "Very High").length} />
              <StatLine label="Regions with first model (RF)" value={rows.length} />
              <StatLine label="Prediction horizon" value="next 7 days" />
              <StatLine label="Model" value="Random Forest (serving)" />
              <StatLine label="Baseline" value="Logistic Regression" />
              <p className="mt-3 text-xs leading-relaxed text-slate-500">
                Values are the model probability that the region enters a
                high-incidence event in the following week. See the Model page for
                training methodology and evaluation metrics.
              </p>
            </>
          )}
        </Card>
      </div>
    </div>
  );
}