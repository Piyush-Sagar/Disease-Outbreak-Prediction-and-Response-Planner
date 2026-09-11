"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { fmtPct, fmtInt } from "@/lib/format";
import {
  Card,
  ErrorState,
  InfoPanel,
  RiskBadge,
  RiskBar,
  SeverityBadge,
  Spinner,
} from "@/components/ui";

export default function ResponsePage() {
  const predictions = useApi(() => api.predictions());
  const priority = useApi(() => api.priority());

  const options = useMemo(() => {
    if (priority.status !== "success") return [];
    return priority.data
      .slice()
      .sort((a, b) => b.priority_score - a.priority_score)
      .map((r) => ({ id: r.id, name: r.name }));
  }, [priority.status, priority.data]);

  const [selected, setSelected] = useState<number | null>(null);
  const selId = selected ?? options[0]?.id ?? null;
  const regionDetail = useApi(() => (selId != null ? api.predictionDetail(selId) : Promise.reject("no region")), [selId]);
  const recommendations = useApi(() => (selId != null ? api.recommendations(selId) : Promise.reject("no region")), [selId]);
  const history = useApi(() => (selId != null ? api.regionHistory(selId, 52) : Promise.reject("no region")), [selId]);

  if (priority.status === "loading") return <Spinner />;
  if (priority.status === "error") return <ErrorState message={priority.error} />;

  const idByName = new Map((predictions.data ?? []).map((p) => [p.region_name, p]));

  const d = regionDetail.data;
  const recs = recommendations.data ?? [];
  const hist = history.data?.history ?? [];

  const renderDetail = d && (
    <div className="space-y-6">
      <Card
        title="Region snapshot"
        subtitle={`assessment date ${d.prediction_date}`}
      >
        <div className="flex flex-wrap items-center gap-4">
          <div>
            <p className="text-xs text-slate-500">Predicted risk</p>
            <p className="text-2xl font-bold text-slate-900">{fmtPct(d.probability)}</p>
            <div className="mt-1 w-52">
              <RiskBar probability={d.probability} />
            </div>
          </div>
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2 text-sm">
              <span className="text-slate-500">Category</span>
              <RiskBadge category={d.risk_category} />
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className="text-slate-500">Severity</span>
              <SeverityBadge band={d.severity_band} />
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className="text-slate-500">Priority</span>
              <span className="font-semibold text-slate-800">{d.priority_score.toFixed(1)}</span>
            </div>
          </div>
          <div className="text-sm text-slate-600">
            <p>Population: {fmtInt(d.population)}</p>
            <p>Cases last week: {fmtInt(hist.at(-1)?.reported_cases ?? 0)}</p>
          </div>
        </div>
      </Card>

      <Card
        title="Recommended response actions"
        subtitle={`rule-based plan · ${d.severity_band} severity activation`}
      >
        {recs.length === 0 ? (
          <p className="text-sm text-slate-400">No active recommendations.</p>
        ) : (
          <div className="divide-y divide-slate-100">
            {recs.map((r, i) => (
              <div key={i} className="flex items-start gap-3 py-2.5">
                <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-emerald-500" />
                <div>
                  <p className="text-sm font-semibold text-slate-800">{r.action}</p>
                  <p className="text-xs text-slate-500">{r.reason}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card title="Last 12 weeks in this region" subtitle="weekly reported cases">
        <div className="flex items-end gap-1" style={{ height: 140 }}>
          {hist.slice(-12).map((h) => (
            <div key={h.date} className="group flex flex-1 flex-col items-center gap-1">
              <div
                className="w-full rounded-t bg-emerald-600/70 transition group-hover:bg-emerald-600"
                style={{
                  height: `${Math.max(4, (h.reported_cases / Math.max(...hist.slice(-12).map((x) => x.reported_cases), 1)) * 120)}px`,
                }}
              />
            </div>
          ))}
        </div>
        <div className="mt-1 flex justify-between text-[10px] text-slate-400">
          {hist.slice(-12).map((h) => (
            <span key={h.date}>{h.date.slice(5)}</span>
          ))}
        </div>
      </Card>

      <InfoPanel title="Methodology">
        <p>{d.label_methodology}</p>
        <p className="pt-1 text-amber-700">{d.demo_data_disclaimer}</p>
      </InfoPanel>
    </div>
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Response Plan</h1>
        <p className="text-sm text-slate-500">
          Select a region to view its recommended response actions and context.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-4">
        <Card title="Regions (by priority)" className="xl:col-span-1">
          <select
            value={selId ?? ""}
            onChange={(e) => setSelected(Number(e.target.value))}
            className="mb-3 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          >
            {options.map((o) => (
              <option key={o.id} value={o.id}>
                {o.name}
              </option>
            ))}
          </select>
          <div className="space-y-2">
            {options.map((o) => {
              const row = priority.data.find((r) => r.id === o.id);
              const pred = row ? idByName.get(row.name) : undefined;
              return (
                <button
                  key={o.id}
                  onClick={() => setSelected(o.id)}
                  className={`w-full rounded-lg border px-3 py-2 text-left text-sm transition ${
                    selId === o.id
                      ? "border-emerald-500 bg-emerald-50 text-emerald-900"
                      : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{o.name}</span>
                    <span className="text-xs font-bold">{row?.priority_score ?? "—"}</span>
                  </div>
                  <div className="mt-1 flex items-center justify-between text-xs text-slate-500">
                    <span>{pred ? fmtPct(pred.probability) : "—"} risk</span>
                    <span>{row?.severity}</span>
                  </div>
                </button>
              );
            })}
          </div>
          <p className="mt-3 text-[10px] leading-relaxed text-slate-400">
            Sorted by priority score (probability 50% + severity 30% + population 20%).
          </p>
        </Card>

        <div className="xl:col-span-3">
          {regionDetail.status === "loading" ? (
            <Spinner />
          ) : regionDetail.status === "error" || !d ? (
            <ErrorState message={regionDetail.error ?? "unknown"} />
          ) : (
            renderDetail
          )}
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {options.map((o) => (
          <Link
            key={o.id}
            href={`/predictions/${o.id}`}
            className="rounded-full border border-slate-300 bg-white px-3 py-1 text-xs text-slate-600 hover:bg-slate-50"
          >
            {o.name}
          </Link>
        ))}
      </div>
    </div>
  );
}