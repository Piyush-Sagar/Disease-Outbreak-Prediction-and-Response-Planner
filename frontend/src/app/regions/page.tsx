"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { fmtInt, riskCategory } from "@/lib/format";
import {
  Card,
  ErrorState,
  RiskBadge,
  RiskBar,
  SeverityBadge,
  Spinner,
} from "@/components/ui";
import { RiskByRegionChart } from "@/components/charts";

const RiskMap = dynamic(() => import("@/components/RiskMap").then((m) => m.RiskMap), {
  ssr: false,
});

export default function RegionsPage() {
  const regions = useApi(() => api.regions());
  const predictions = useApi(() => api.predictions());
  const priority = useApi(() => api.priority());

  if (regions.status === "loading" || predictions.status === "loading") {
    return <Spinner />;
  }
  if (regions.status === "error" || predictions.status === "error") {
    return <ErrorState message={regions.error ?? predictions.error ?? "unknown"} />;
  }

  const predByRegion = new Map(predictions.data.map((p) => [p.region_name, p]));
  const priByRegion = new Map((priority.data ?? []).map((p) => [p.name, p]));
  const rows = regions.data
    .map((r) => {
      const pred = predByRegion.get(r.name);
      const pri = priByRegion.get(r.name);
      return {
        ...r,
        probability: pred?.probability ?? 0,
        severity: pred?.severity_band ?? ("LOW" as const),
        priorityScore: pri?.priority_score ?? 0,
      };
    })
    .sort((a, b) => b.probability - a.probability);

  const mapPoints = rows.map((r) => ({
    id: r.id,
    name: r.name,
    latitude: r.latitude,
    longitude: r.longitude,
    probability: r.probability,
    category: riskCategory(r.probability),
    population: r.population,
  }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Regions</h1>
        <p className="text-sm text-slate-500">
          {rows.length} Indian cities in the demo · population shown in units
        </p>
      </div>

      <Card title="Regional risk map" subtitle="predicted outbreak risk · next 7 days">
        <RiskMap points={mapPoints} height={420} />
      </Card>

      <Card title="Regions ranked by predicted risk">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                <th className="py-2 pr-4">Region</th>
                <th className="py-2 pr-4">Population</th>
                <th className="py-2 pr-4">Risk</th>
                <th className="py-2 pr-4">Category</th>
                <th className="py-2 pr-4">Severity</th>
                <th className="py-2 pr-4">Priority</th>
                <th className="py-2" />
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id} className="border-b border-slate-100 last:border-0">
                  <td className="py-2.5 pr-4 font-semibold text-slate-800">{r.name}</td>
                  <td className="py-2.5 pr-4 text-slate-600">{fmtInt(r.population)}</td>
                  <td className="py-2.5 pr-4 w-40">
                    <RiskBar probability={r.probability} />
                  </td>
                  <td className="py-2.5 pr-4">
                    <RiskBadge category={riskCategory(r.probability)} />
                  </td>
                  <td className="py-2.5 pr-4">
                    <SeverityBadge band={r.severity} />
                  </td>
                  <td className="py-2.5 pr-4 font-semibold text-slate-700">{r.priorityScore.toFixed(1)}</td>
                  <td className="py-2.5">
                    <Link
                      href={`/predictions/${r.id}`}
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

      <Card title="Risk comparison" subtitle="predicted risk (%) and priority score by region">
        {priority.data ? (
          <RiskByRegionChart data={priority.data} />
        ) : (
          <p className="text-sm text-slate-400">No data</p>
        )}
      </Card>
    </div>
  );
}