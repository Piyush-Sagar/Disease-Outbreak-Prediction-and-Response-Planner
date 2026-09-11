"use client";

import Image from "next/image";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import {
  Card,
  ErrorState,
  InfoPanel,
  Spinner,
  StatLine,
} from "@/components/ui";
import { FeatureImportanceChart } from "@/components/charts";

export default function ModelPage() {
  const perf = useApi(() => api.modelPerformance());

  if (perf.status === "loading") return <Spinner />;
  if (perf.status === "error" && !perf.data) return <ErrorState message={perf.error} />;

  const p = perf.data;
  const rows = p.metrics.models;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Model</h1>
        <p className="text-sm text-slate-500">
          Random Forest vs Logistic Regression for predicting high-incidence events 1 week ahead.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Card title="Evaluation (held-out test weeks)" className="xl:col-span-2" subtitle="time-based 80/20 split · last 20% of weeks held out">
          <div className="overflow-x-auto">
            <table className="w-full text-right text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                  <th className="py-2 text-left pr-4">Model</th>
                  <th className="py-2 pr-4">Acc</th>
                  <th className="py-2 pr-4">Prec</th>
                  <th className="py-2 pr-4">Rec</th>
                  <th className="py-2 pr-4">F1</th>
                  <th className="py-2">AUC</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((m) => (
                  <tr key={m.model} className="border-b border-slate-100 last:border-0">
                    <td className="py-2 pr-4 text-left font-semibold text-slate-800">{m.model}</td>
                    <td className="py-2 pr-4 tabular-nums">{m.accuracy.toFixed(3)}</td>
                    <td className="py-2 pr-4 tabular-nums">{m.precision.toFixed(3)}</td>
                    <td className="py-2 pr-4 tabular-nums">{m.recall.toFixed(3)}</td>
                    <td className="py-2 pr-4 tabular-nums">{m.f1.toFixed(3)}</td>
                    <td className="py-2 tabular-nums">{m.roc_auc.toFixed(3)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <StatLine label="Train rows" value={p.metadata.train_rows} />
            <StatLine label="Test rows" value={p.metadata.test_rows} />
            <StatLine label="OOB score (RF)" value={p.metadata.oob_score.toFixed(4)} />
            <StatLine label="Trained" value={p.metadata.trained_at} />
          </div>
        </Card>

        <Card title="Training metadata" subtitle="feature engineering details">
          <p className="mb-2 text-xs text-slate-500">Label: {p.metadata.label_column}</p>
          <p className="mb-3 text-xs leading-relaxed text-slate-600">
            {p.metadata.label_definition}
          </p>
          <p className="mb-1 text-xs font-semibold text-slate-600">Features ({p.metadata.features.length})</p>
          <p className="text-xs leading-relaxed text-slate-500">
            {p.metadata.features.join(", ")}
          </p>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card title="Feature importance" subtitle="Random Forest mean decrease in impurity">
          {p.feature_importance.length ? (
            <FeatureImportanceChart data={p.feature_importance} />
          ) : (
            <p className="text-sm text-slate-400">No importance data.</p>
          )}
        </Card>
        <Card title="Evaluation figures" subtitle="generated at training time">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {p.figures.map((fig) => (
              <div key={fig} className="overflow-hidden rounded-lg border border-slate-200">
                <Image
                  src={`${api.baseUrl}${fig}`}
                  alt={fig.split("/").pop()?.replace(".png", "") ?? fig}
                  width={640}
                  height={320}
                  unoptimized
                  className="h-40 w-full object-contain bg-white"
                />
              </div>
            ))}
          </div>
        </Card>
      </div>

      <InfoPanel title="Methodology">
        <p>{p.label_methodology}</p>
        <p className="pt-1">{p.severity_methodology}</p>
        <p className="pt-1">{p.priority_methodology}</p>
        <p className="pt-1">{p.explainability_methodology}</p>
      </InfoPanel>
    </div>
  );
}