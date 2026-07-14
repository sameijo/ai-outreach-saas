'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

export default function SettingsPage() {
  const [smtpConfigs, setSmtpConfigs] = useState<any[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [form, setForm] = useState({
    name: '', provider: 'sendgrid', from_email: '', from_name: '', reply_to: '',
    api_key: '', smtp_host: '', smtp_port: '587', smtp_username: '', smtp_password: '', daily_limit: '100',
  });

  useEffect(() => { api.getSmtpConfigs().then(setSmtpConfigs).catch(console.error); }, []);

  const handleAdd = async () => {
    setError(''); setSuccess('');
    try {
      const config = await api.createSmtpConfig({
        ...form,
        smtp_port: parseInt(form.smtp_port),
        daily_limit: parseInt(form.daily_limit),
      });
      setSmtpConfigs([config, ...smtpConfigs]);
      setShowAdd(false);
      setSuccess('SMTP config added!');
    } catch (e: any) { setError(e.message); }
  };

  const handleDelete = async (id: number) => {
    try {
      await api.deleteSmtpConfig(id);
      setSmtpConfigs(smtpConfigs.filter(c => c.id !== id));
    } catch (e: any) { setError(e.message); }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <button onClick={() => setShowAdd(!showAdd)} className="bg-primary-600 text-white px-5 py-2.5 rounded-lg hover:bg-primary-700 font-medium">
          + Add SMTP Config
        </button>
      </div>

      {error && <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm">{error}</div>}
      {success && <div className="bg-green-50 text-green-700 p-3 rounded-lg text-sm">{success}</div>}

      {/* Add SMTP Config */}
      {showAdd && (
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 space-y-4">
          <h2 className="text-lg font-semibold">Add Email Provider</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full border rounded-lg px-3 py-2" placeholder="My SendGrid" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Provider</label>
              <select value={form.provider} onChange={(e) => setForm({ ...form, provider: e.target.value })} className="w-full border rounded-lg px-3 py-2">
                <option value="sendgrid">SendGrid</option>
                <option value="ses">Amazon SES</option>
                <option value="mailgun">Mailgun</option>
                <option value="resend">Resend</option>
                <option value="smtp">Custom SMTP</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">From Email</label>
              <input type="email" value={form.from_email} onChange={(e) => setForm({ ...form, from_email: e.target.value })} className="w-full border rounded-lg px-3 py-2" placeholder="hello@yourdomain.com" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">From Name</label>
              <input type="text" value={form.from_name} onChange={(e) => setForm({ ...form, from_name: e.target.value })} className="w-full border rounded-lg px-3 py-2" placeholder="Your Company" />
            </div>
            {(form.provider === 'sendgrid' || form.provider === 'resend' || form.provider === 'mailgun') && (
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">API Key</label>
                <input type="password" value={form.api_key} onChange={(e) => setForm({ ...form, api_key: e.target.value })} className="w-full border rounded-lg px-3 py-2" placeholder="SG.… or re.…" />
              </div>
            )}
            {form.provider === 'smtp' && (
              <>
                <div><label className="block text-sm font-medium text-gray-700 mb-1">SMTP Host</label><input type="text" value={form.smtp_host} onChange={(e) => setForm({ ...form, smtp_host: e.target.value })} className="w-full border rounded-lg px-3 py-2" /></div>
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Port</label><input type="text" value={form.smtp_port} onChange={(e) => setForm({ ...form, smtp_port: e.target.value })} className="w-full border rounded-lg px-3 py-2" /></div>
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Username</label><input type="text" value={form.smtp_username} onChange={(e) => setForm({ ...form, smtp_username: e.target.value })} className="w-full border rounded-lg px-3 py-2" /></div>
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Password</label><input type="password" value={form.smtp_password} onChange={(e) => setForm({ ...form, smtp_password: e.target.value })} className="w-full border rounded-lg px-3 py-2" /></div>
              </>
            )}
            {form.provider === 'mailgun' && (
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Domain</label><input type="text" value={form.smtp_host} onChange={(e) => setForm({ ...form, smtp_host: e.target.value })} className="w-full border rounded-lg px-3 py-2" placeholder="mg.yourdomain.com" /></div>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Daily Limit</label>
              <input type="number" value={form.daily_limit} onChange={(e) => setForm({ ...form, daily_limit: e.target.value })} className="w-full border rounded-lg px-3 py-2" />
            </div>
          </div>
          <div className="flex gap-3">
            <button onClick={handleAdd} className="bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700">Save Config</button>
            <button onClick={() => setShowAdd(false)} className="text-gray-500 px-4 py-2 rounded-lg hover:bg-gray-100">Cancel</button>
          </div>
        </div>
      )}

      {/* SMTP Configs List */}
      <div className="space-y-3">
        {smtpConfigs.map((config) => (
          <div key={config.id} className="bg-white rounded-xl p-5 shadow-sm border border-gray-100 flex items-center justify-between">
            <div>
              <h3 className="font-semibold">{config.name}</h3>
              <p className="text-sm text-gray-500">{config.provider} · {config.from_email} · Limit: {config.daily_limit}/day</p>
            </div>
            <div className="flex items-center gap-3">
              {config.is_default && <span className="text-xs bg-primary-100 text-primary-700 px-2 py-1 rounded-full">Default</span>}
              <button onClick={() => handleDelete(config.id)} className="text-red-500 hover:bg-red-50 p-2 rounded-lg">🗑️</button>
            </div>
          </div>
        ))}
        {smtpConfigs.length === 0 && (
          <div className="bg-white rounded-xl p-8 shadow-sm border border-gray-100 text-center">
            <p className="text-gray-400">No email configs yet. Add one to start sending.</p>
          </div>
        )}
      </div>

      {/* Quick Setup Guide */}
      <div className="bg-blue-50 rounded-xl p-6 border border-blue-100">
        <h3 className="font-semibold text-blue-900 mb-3">📖 Quick Setup Guide</h3>
        <div className="space-y-2 text-sm text-blue-800">
          <p><strong>SendGrid:</strong> Get API key from <a href="https://app.sendgrid.com/settings/api_keys" target="_blank" className="underline">SendGrid Dashboard</a></p>
          <p><strong>Amazon SES:</strong> Set up in <a href="https://console.aws.amazon.com/ses/" target="_blank" className="underline">AWS SES Console</a> (sandbox → production)</p>
          <p><strong>Resend:</strong> Get key from <a href="https://resend.com/api-keys" target="_blank" className="underline">Resend Dashboard</a></p>
          <p><strong>Important:</strong> Set up SPF, DKIM, and DMARC DNS records for your domain to maximize deliverability.</p>
        </div>
      </div>
    </div>
  );
}
