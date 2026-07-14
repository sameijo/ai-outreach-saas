'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

function StatCard({ label, value, subtext, color = 'text-gray-900' }: { label: string; value: string | number; subtext?: string; color?: string }) {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <p className="text-sm text-gray-500 mb-1">{label}</p>
      <p className={`text-3xl font-bold ${color}`}>{value}</p>
      {subtext && <p className="text-xs text-gray-400 mt-1">{subtext}</p>}
    </div>
  );
}

export default function DashboardPage() {
  const [overview, setOverview] = useState<any>(null);
  const [activity, setActivity] = useState<any[]>([]);
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getDashboardOverview(),
      api.getDashboardActivity(30),
      api.getCampaignsSummary(),
    ]).then(([ov, act, camp]) => {
      setOverview(ov);
      setActivity(act);
      setCampaigns(camp);
    }).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="animate-pulse space-y-6"><div className="h-32 bg-gray-200 rounded-xl" /><div className="h-64 bg-gray-200 rounded-xl" /></div>;

  const pieData = overview ? [
    { name: 'Opened', value: overview.emails_opened },
    { name: 'Clicked', value: overview.emails_clicked },
    { name: 'Replied', value: overview.emails_replied },
    { name: 'Bounced', value: overview.emails_bounced },
  ].filter(d => d.value > 0) : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <span className="text-sm text-gray-500">Last 30 days</span>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Leads" value={overview?.total_leads || 0} subtext={`${overview?.credits_remaining || 0} credits left`} />
        <StatCard label="Emails Sent" value={overview?.emails_sent || 0} subtext={`${overview?.active_campaigns || 0} active campaigns`} />
        <StatCard label="Open Rate" value={`${overview?.open_rate || 0}%`} subtext={`${overview?.emails_opened || 0} opened`} color="text-green-600" />
        <StatCard label="Reply Rate" value={`${overview?.reply_rate || 0}%`} subtext={`${overview?.emails_replied || 0} replies`} color="text-blue-600" />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Activity Chart */}
        <div className="lg:col-span-2 bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h2 className="text-lg font-semibold mb-4">Email Activity</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={activity}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Line type="monotone" dataKey="sent" stroke="#3b82f6" strokeWidth={2} name="Sent" />
              <Line type="monotone" dataKey="opened" stroke="#10b981" strokeWidth={2} name="Opened" />
              <Line type="monotone" dataKey="clicked" stroke="#f59e0b" strokeWidth={2} name="Clicked" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Pie Chart */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h2 className="text-lg font-semibold mb-4">Engagement Breakdown</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" outerRadius={100} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Campaigns Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-6 border-b border-gray-100">
          <h2 className="text-lg font-semibold">Recent Campaigns</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Campaign</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Sent</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Open %</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Click %</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reply %</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {campaigns.map((c) => (
                <tr key={c.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{c.name}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      c.status === 'active' ? 'bg-green-100 text-green-800' :
                      c.status === 'completed' ? 'bg-blue-100 text-blue-800' :
                      c.status === 'paused' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>{c.status}</span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">{c.emails_sent}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{c.open_rate}%</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{c.click_rate}%</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{c.reply_rate}%</td>
                </tr>
              ))}
              {campaigns.length === 0 && (
                <tr><td colSpan={6} className="px-6 py-8 text-center text-gray-400">No campaigns yet</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
