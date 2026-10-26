"use client";

import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { fmtDate, fmtInt } from "@/lib/format";
import {
  Card,
  DisclaimerBadge,
  ErrorState,
  InfoPanel,
  Spinner,
  StatLine,
} from "@/components/ui";

export default function DataPage() {
  const info = useApi(() => api.datasetInfo());
  const rows = useApi(() => api.datasetRows(15));

  if (info.status === "loading") return <Spinner />;
  if (info.status === "error" && !info.data) return <ErrorState message={info.error} />;

  const d = info.data;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Dataset</h1>
          <p className="text-sm text-slate-500"> {d.disease} surveillance dataset.</p>
        </div>
        <DisclaimerBadge />
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-5">
        <Card>
          <StatLine label="Disease" value={d.disease} />
          <StatLine label="Regions" value={d.regions} />
          <StatLine label="Observations" value={fmtInt(d.observations)} />
        </Card>
        <Card>
          <StatLine label="First week" value={fmtDate(d.date_range.first)} />
          <StatLine label="Last week" value={fmtDate(d.date_range.last)} />
          <StatLine label="Total cases" value={fmtInt(d.total_cases)} />
        </Card>
        <Card className="col-span-2">
          <p className="mb-2 text-xs font-semibold text-slate-600">Source files</p>
          <ul className="space-y-1 text-xs text-slate-500">
            {d.source_files.map((f) => (
              <li key={f} className="font-mono">{f}</li>
            ))}
          </ul>
        </Card>
        <Card>
          <p className="mb-2 text-xs font-semibold text-slate-600">dataset notice</p>
          <p className="text-xs leading-relaxed text-amber-700">{d.synthetic_notice}</p>
        </Card>
      </div>

      <Card title="Latest observations (sample)" subtitle="most recent rows across regions">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 uppercase tracking-wide text-slate-500">
                <th className="py-2 pr-4">Date</th>
                <th className="py-2 pr-4">Region</th>
                <th className="py-2 pr-4">Cases</th>
                <th className="py-2 pr-4">Prev wk</th>
                <th className="py-2 pr-4">Deaths</th>
                <th className="py-2 pr-4">Temp °C</th>
                <th className="py-2 pr-4">Rain mm</th>
                <th className="py-2 pr-4">Humidity %</th>
                <th className="py-2 pr-4">WAI</th>
                <th className="py-2">Pop/area</th>
              </tr>
            </thead>
            <tbody>
              {rows.data?.map((r, i) => (
                <tr key={i} className="border-b border-slate-100 last:border-0">
                  <td className="py-2 pr-4 text-slate-600">{r.date}</td>
                  <td className="py-2 pr-4 font-semibold text-slate-800">{r.region}</td>
                  <td className="py-2 pr-4 tabular-nums">{r.reported_cases}</td>
                  <td className="py-2 pr-4 tabular-nums">{r.previous_week_cases}</td>
                  <td className="py-2 pr-4 tabular-nums">{r.deaths}</td>
                  <td className="py-2 pr-4 tabular-nums">{r.temperature.toFixed(1)}</td>
                  <td className="py-2 pr-4 tabular-nums">{r.rainfall.toFixed(1)}</td>
                  <td className="py-2 pr-4 tabular-nums">{r.humidity.toFixed(1)}</td>
                  <td className="py-2 pr-4 tabular-nums">{r.water_accumulation_index.toFixed(2)}</td>
                  <td className="py-2 tabular-nums">{r.population_density.toFixed(0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {rows.status === "error" && <p className="mt-2 text-sm text-red-600">{rows.error}</p>}
      </Card>

      <InfoPanel title="Label methodology">
        <p>{d.label_methodology}</p>
        <p className="pt-1 text-amber-700">{d.demo_data_disclaimer}</p>
      </InfoPanel>
    </div>
  );
}