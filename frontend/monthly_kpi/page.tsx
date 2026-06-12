/**
 * Monthly KPI Report Dashboard Page
 */

'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';

interface Employee {
  id: string;
  name: string;
  dept: string;
  role: string;
  manager: string;
  score: number;
  roleAvg: number;
  delta: string;
  activeTime: string;
  trendCy: number[];
  trendColor: string;
  status: string;
  metrics: Array<{section: string; label: string; value: string; roleAvg?: string}>;
}

interface FilterOptions {
  dept: string[];
  role: string[];
  manager: string[];
  employee: string[];
}

interface KPIReport {
  header: {title: string; breadcrumb: string; dateRange: string; dateFrom: string; dateTo: string};
  employees: Employee[];
  filter_options: FilterOptions;
  statusCounts: {[key: string]: number};
}

export default function MonthlyKPIPage() {
  const [report, setReport] = useState<KPIReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({dept: '', role: '', manager: '', employee: ''});
  const searchParams = useSearchParams();

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const res = await fetch('/api/monthly-kpi/report', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({domain_id: 9, start_date: '2026-05-01', end_date: '2026-05-29'}),
        });
        if (!res.ok) throw new Error(`${res.statusText}`);
        setReport(await res.json());
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed');
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, []);

  if (loading) return <div className="flex items-center justify-center h-screen"><p>Loading...</p></div>;
  if (error || !report) return <div className="p-8"><p className="text-red-600">Error: {error}</p></div>;

  const filtered = report.employees.filter((emp) => {
    if (filters.dept && emp.dept !== filters.dept) return false;
    if (filters.role && emp.role !== filters.role) return false;
    return true;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b border-gray-200 px-6 py-6">
        <h1 className="text-3xl font-bold">{report.header.title}</h1>
        <p className="text-blue-600 font-medium">{report.header.breadcrumb}</p>
        <p className="text-gray-600">{report.header.dateRange}</p>
      </div>
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-6 rounded border border-gray-200"><div className="text-3xl font-bold text-blue-600">{report.statusCounts['most-engaged'] || 0}</div><p className="text-sm text-gray-600 mt-2">MOST ENGAGED</p></div>
          <div className="bg-white p-6 rounded border border-gray-200"><div className="text-3xl font-bold text-red-600">{report.statusCounts['needs-attention'] || 0}</div><p className="text-sm text-gray-600 mt-2">NEEDS ATTENTION</p></div>
          <div className="bg-white p-6 rounded border border-gray-200"><div className="text-3xl font-bold text-yellow-600">{report.statusCounts['inactive'] || 0}</div><p className="text-sm text-gray-600 mt-2">INACTIVE</p></div>
          <div className="bg-white p-6 rounded border border-gray-200"><div className="text-3xl font-bold text-gray-600">{report.statusCounts['on-track'] || 0}</div><p className="text-sm text-gray-600 mt-2">ON TRACK</p></div>
        </div>
        <div className="bg-white rounded border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-3 text-left font-semibold">Name</th>
                <th className="px-6 py-3 text-left font-semibold">Dept</th>
                <th className="px-6 py-3 text-left font-semibold">Role</th>
                <th className="px-6 py-3 text-center font-semibold">Score</th>
                <th className="px-6 py-3 text-center font-semibold">Avg</th>
                <th className="px-6 py-3 text-left font-semibold">Status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((emp) => (
                <tr key={emp.id} className="border-b hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium">{emp.name}</td>
                  <td className="px-6 py-4">{emp.dept}</td>
                  <td className="px-6 py-4">{emp.role}</td>
                  <td className="px-6 py-4 text-center font-semibold">{emp.score}</td>
                  <td className="px-6 py-4 text-center">{emp.roleAvg}</td>
                  <td className="px-6 py-4"><span className="px-3 py-1 rounded text-xs font-semibold bg-blue-100 text-blue-800">{emp.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
