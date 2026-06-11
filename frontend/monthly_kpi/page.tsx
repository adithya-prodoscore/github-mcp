/**
 * Monthly KPI Report Page - Next.js Component
 * Type-safe React page with Tailwind CSS for KPI dashboard.
 */

"use client";

import { useEffect, useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

interface Metric {
  section: string;
  label: string;
  value: number;
  roleAvg?: number;
  companyAvg?: number;
}

interface Employee {
  employee_id: string;
  name: string;
  role: string;
  department?: string;
  email?: string;
  score: number;
  activeMinutes: number;
  status: "inactive" | "needs-attention" | "most-engaged" | "on-track";
  metrics: Metric[];
}

interface MonthlyKPIReport {
  header: { title: string; company: string; startDate: string; endDate: string; generatedAt: string };
  employees: Employee[];
  filter_options: { departments: string[]; roles: string[]; managers: string[]; employees: Array<{ id: string; name: string }> };
  statusCounts: { inactive: number; "needs-attention": number; "most-engaged": number; "on-track": number };
}

const statusColors = {
  "most-engaged": { bg: "bg-green-50", border: "border-green-200", badge: "bg-green-100 text-green-800" },
  "needs-attention": { bg: "bg-red-50", border: "border-red-200", badge: "bg-red-100 text-red-800" },
  "on-track": { bg: "bg-blue-50", border: "border-blue-200", badge: "bg-blue-100 text-blue-800" },
  inactive: { bg: "bg-gray-50", border: "border-gray-200", badge: "bg-gray-100 text-gray-800" },
};

export default function MonthlyKPIPage() {
  const [report, setReport] = useState<MonthlyKPIReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedEmployee, setExpandedEmployee] = useState<string | null>(null);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const response = await fetch("/api/monthly-kpi/report?domain_id=9");
        const data = await response.json();
        setReport(data);
      } catch (error) {
        console.error("Failed to fetch report:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchReport();
  }, []);

  if (loading) return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  if (!report) return <div className="flex items-center justify-center min-h-screen">Failed to load report</div>;

  const formatMinutes = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0) return `${hours}h ${mins}min`;
    return `${mins}min`;
  };

  const statusLabelMap = { "most-engaged": "Most Engaged", "needs-attention": "Needs Attention", "on-track": "On Track", inactive: "Inactive" };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b border-gray-200 px-6 py-8">
        <h1 className="text-3xl font-bold text-gray-900">{report.header.title}</h1>
        <p className="text-gray-600 mt-2">{report.header.startDate} to {report.header.endDate}</p>
      </div>

      <div className="px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {Object.entries(report.statusCounts).map(([status, count]) => {
            const colors = statusColors[status as keyof typeof statusColors];
            return (
              <div key={status} className={`rounded-lg border-2 ${colors.border} ${colors.bg} p-6`}>
                <div className="text-sm font-semibold text-gray-600 mb-2">{statusLabelMap[status as keyof typeof statusLabelMap]}</div>
                <div className="text-3xl font-bold text-gray-900">{count}</div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="px-6 py-8">
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Name</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Role</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Score</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Active Time</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Status</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {report.employees.map((emp) => {
                const colors = statusColors[emp.status];
                const isExpanded = expandedEmployee === emp.employee_id;
                return (
                  <div key={emp.employee_id}>
                    <tr onClick={() => setExpandedEmployee(isExpanded ? null : emp.employee_id)} className="cursor-pointer hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm text-gray-900">{emp.name}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{emp.role}</td>
                      <td className="px-6 py-4 text-sm font-semibold text-gray-900">{emp.score.toFixed(1)}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{formatMinutes(emp.activeMinutes)}</td>
                      <td className="px-6 py-4"><span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium ${colors.badge}`}>{statusLabelMap[emp.status]}</span></td>
                      <td className="px-6 py-4 text-right">{isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}</td>
                    </tr>
                    {isExpanded && (
                      <tr>
                        <td colSpan={6} className="px-6 py-4 bg-gray-50">
                          <div className="space-y-4">
                            <h4 className="font-semibold text-gray-900">Detailed Metrics</h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              {emp.metrics.map((metric, idx) => (
                                <div key={idx} className="bg-white rounded-lg p-4 border border-gray-200">
                                  <div className="text-sm font-semibold text-gray-600 mb-2">{metric.section}</div>
                                  <div className="text-lg font-bold text-gray-900">{metric.label}</div>
                                  <div className="text-2xl font-bold text-gray-900 mt-2">{metric.value.toFixed(1)}</div>
                                  {metric.roleAvg && <div className="text-xs text-gray-600 mt-2">Role Avg: {metric.roleAvg.toFixed(1)}</div>}
                                </div>
                              ))}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </div>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
