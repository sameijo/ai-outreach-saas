'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [leadLists, setLeadLists] = useState<any[]>([]);
  const [smtpConfigs, setSmtpConfigs] = useState<any[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Create form
  const [form, setForm] = useState({
    name: '', lead_list_id: '', smtp_config_id: '', subject: '', body_html: '',
    personalize_with_ai: true, ai_tone: 'professional',
    send_rate_per_hour: 30, send_rate_per_day: 200,
  });

  useEffect(() => {
    Promise.all([api.getCampaigns(), api.getLeadLists(), api.getSmtpConfigs()])
      .then(([c, l, s]) => { setCampaigns(c); setLeadLists(l); setSmtpConfigs(s); })
      .catch(console.error).finally(() => setLoading(false));
  }, []);

  const handleCreate = async () => {
    setError(''); setSuccess('');
    try {
      await api.createCampaign({
        ...form,
        lead_list_id: parseInt(form.lead_list_id),
        smtp_config_id: form.smtp_config_id ? parseInt(form.smtp_config_id) : null,
      });
      setSuccess('Campaign created!');
      setShowCreate(false);
      setCampaigns(await api.getCampaigns());
    } catch (e: any) { setError(e.message); }
  };

  const handleAction = async (id: number, action: 'start' | 'pause' | 'resume' | 'delete') => {
    setError(''); setSuccess('');
    try {
      if (action === 'start') await api.startCampaign(id);
      else if (action === 'pause') await api.pauseCampaign(id);
      else if (action === 'resume') await api.resumeCampaign(id);
      else if (action === 'delete') { await api.deleteCampaign(id); }
      setSuccess(`Campaign ${action}ed!`);
      setCampaigns(await api.getCampaigns());
    } catch (e: any) { setError(e.message); }
  };

  const statusColor = (s: string) => {
    switch (s) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'completed': return 'bg-blue-100 text-blue-800';
      case 'paused': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Campaigns</h1>
        <button onClick={() => setShowCreate(!showCreate)} className="bg-primary-600 text-white px-5 py-2.5 rounded-lg hover:bg-primary-700 font-medium">
          + New Campaign
        </button>
      </div>

      {error && <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm">{error}</div>}
      {success && <div className="bg-green-50 text-green-700 p-3 rounded-lg text-sm">{success}</div>}

      {/* Create Form */}
      {showCreate && (
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 space-y-4">
          <h2 className="text-lg font-semibold">Create Campaign</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Campaign Name</label>
              <input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full border rounded-lg px-3 py-2" placeholder="Q1 Outreach" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Lead List</label>
              <select value={form.lead_list_id} onChange={(e) => setForm({ ...form, lead_list_id: e.target.value })} className="w-full border rounded-lg px-3 py-2">
                <option value="">Select list...</option>
                {leadLists.map(l => <option key={l.id} value={l.id}>{l.name} ({l.total_leads} leads)</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">SMTP Config</label>
              <select value={form.smtp_config_id} onChange={(e) => setForm({ ...form, smtp_config_id: e.target.value })} className="w-full border rounded-lg px-3 py-2">
                <option value="">Default</option>
                {smtpConfigs.map(s => <option key={s.id} value={s.id}>{s.name} ({s.from_email})</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">AI Tone</label>
              <select value={form.ai_tone} onChange={(e) => setForm({ ...form, ai_tone: e.target.value })} className="w-full border rounded-lg px-3 py-2">
                <option value="professional">Professional</option>
                <option value="casual">Casual</option>
                <option value="persuasive">Persuasive</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Subject Line</label>
            <input type="text" value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} className="w-full border rounded-lg px-3 py-2" placeholder="Hi {{first_name}}, quick question about {{company}}" />
            <p className="text-xs text-gray-400 mt-1">Variables: {'{{first_name}}'}, {'{{last_name}}'}, {'{{company}}'}, {'{{job_title}}'}, {'{{ai_intro}}'}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email Body (HTML)</label>
            <textarea value={form.body_html} onChange={(e) => setForm({ ...form, body_html: e.target.value })} rows={8} className="w-full border rounded-lg px-3 py-2 font-mono text-sm" placeholder={`<p>Hi {{first_name}},</p>\n<p>{{ai_intro}}</p>\n<p>I'd love to discuss how we can help {{company}} grow.</p>\n<p>Best regards</p>`} />
          </div>
          <div className="flex items-center gap-6">
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={form.personalize_with_ai} onChange={(e) => setForm({ ...form, personalize_with_ai: e.target.checked })} className="rounded" />
              <span className="text-sm">AI Personalization</span>
            </label>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">Rate:</span>
              <input type="number" value={form.send_rate_per_hour} onChange={(e) => setForm({ ...form, send_rate_per_hour: parseInt(e.target.value) })} className="w-20 border rounded px-2 py-1 text-sm" />
              <span className="text-sm text-gray-500">/hour</span>
            </div>
          </div>
          <div className="flex gap-3">
            <button onClick={handleCreate} className="bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700">Create Campaign</button>
            <button onClick={() => setShowCreate(false)} className="text-gray-500 px-4 py-2 rounded-lg hover:bg-gray-100">Cancel</button>
          </div>
        </div>
      )}

      {/* Campaigns Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {campaigns.map((c) => (
          <div key={c.id} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-start justify-between mb-3">
              <h3 className="font-semibold text-gray-900 truncate">{c.name}</h3>
              <span className={`text-xs font-semibold px-2 py-1 rounded-full ${statusColor(c.status)}`}>{c.status}</span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-sm mb-4">
              <div><span className="text-gray-400">Sent:</span> <span className="font-medium">{c.emails_sent}</span></div>
              <div><span className="text-gray-400">Opened:</span> <span className="font-medium text-green-600">{c.open_rate}%</span></div>
              <div><span className="text-gray-400">Clicked:</span> <span className="font-medium text-blue-600">{c.click_rate}%</span></div>
              <div><span className="text-gray-400">Replied:</span> <span className="font-medium text-purple-600">{c.reply_rate}%</span></div>
            </div>

            <div className="flex gap-2">
              {c.status === 'draft' && <button onClick={() => handleAction(c.id, 'start')} className="flex-1 bg-green-600 text-white text-sm py-1.5 rounded-lg hover:bg-green-700">▶ Start</button>}
              {c.status === 'active' && <button onClick={() => handleAction(c.id, 'pause')} className="flex-1 bg-yellow-500 text-white text-sm py-1.5 rounded-lg hover:bg-yellow-600">⏸ Pause</button>}
              {c.status === 'paused' && <button onClick={() => handleAction(c.id, 'resume')} className="flex-1 bg-green-600 text-white text-sm py-1.5 rounded-lg hover:bg-green-700">▶ Resume</button>}
              {(c.status === 'draft' || c.status === 'paused' || c.status === 'completed') && (
                <button onClick={() => handleAction(c.id, 'delete')} className="text-red-500 text-sm px-3 py-1.5 rounded-lg hover:bg-red-50">🗑️</button>
              )}
            </div>
          </div>
        ))}
        {campaigns.length === 0 && (
          <div className="col-span-full bg-white rounded-xl p-12 shadow-sm border border-gray-100 text-center">
            <p className="text-gray-400">No campaigns yet. Create your first one!</p>
          </div>
        )}
      </div>
    </div>
  );
}
