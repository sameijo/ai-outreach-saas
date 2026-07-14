'use client';

import { useState, useEffect, useRef } from 'react';
import { api } from '@/lib/api';

export default function LeadsPage() {
  const [lists, setLists] = useState<any[]>([]);
  const [selectedList, setSelectedList] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchSource, setSearchSource] = useState('apollo');
  const [searching, setSearching] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [enriching, setEnriching] = useState(false);
  const [tone, setTone] = useState('professional');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => { loadLists(); }, []);

  const loadLists = async () => {
    try {
      const data = await api.getLeadLists();
      setLists(data);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true); setError(''); setSuccess('');
    try {
      const result = await api.searchLeads(searchQuery, searchSource, 50);
      setSuccess(`Found ${result.total_leads} leads!`);
      loadLists();
    } catch (e: any) { setError(e.message); }
    finally { setSearching(false); }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true); setError(''); setSuccess('');
    try {
      const name = file.name.replace('.csv', '');
      const result = await api.uploadCSV(file, name);
      setSuccess(`Imported ${result.total_imported} leads (${result.total_skipped} skipped)`);
      loadLists();
    } catch (e: any) { setError(e.message); }
    finally { setUploading(false); if (fileRef.current) fileRef.current.value = ''; }
  };

  const handleEnrich = async () => {
    if (!selectedList?.leads?.length) return;
    setEnriching(true); setError(''); setSuccess('');
    try {
      const leadIds = selectedList.leads.map((l: any) => l.id);
      await api.enrichLeads(leadIds, tone);
      setSuccess(`AI enrichment started for ${leadIds.length} leads`);
    } catch (e: any) { setError(e.message); }
    finally { setEnriching(false); }
  };

  const handleVerify = async () => {
    if (!selectedList?.leads?.length) return;
    try {
      const leadIds = selectedList.leads.map((l: any) => l.id);
      await api.verifyLeads(leadIds);
      setSuccess(`Verification started for ${leadIds.length} leads`);
    } catch (e: any) { setError(e.message); }
  };

  const loadListDetail = async (id: number) => {
    try {
      const data = await api.getLeadList(id);
      setSelectedList(data);
    } catch (e: any) { setError(e.message); }
  };

  const handleExport = async () => {
    try {
      const data = await api.exportLeads(selectedList?.id);
      const csv = [Object.keys(data.data[0] || {}).join(','), ...data.data.map((r: any) => Object.values(r).join(','))].join('\n');
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = 'leads.csv'; a.click();
    } catch (e: any) { setError(e.message); }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Lead Management</h1>

      {error && <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm">{error}</div>}
      {success && <div className="bg-green-50 text-green-700 p-3 rounded-lg text-sm">{success}</div>}

      {/* Search / Upload Bar */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 space-y-4">
        <h2 className="text-lg font-semibold">Find New Leads</h2>
        <div className="flex gap-3">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="e.g. Real Estate Agents in New York"
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
          <select value={searchSource} onChange={(e) => setSearchSource(e.target.value)} className="border border-gray-300 rounded-lg px-3 py-2.5">
            <option value="apollo">Apollo.io</option>
            <option value="hunter">Hunter.io</option>
          </select>
          <button onClick={handleSearch} disabled={searching} className="bg-primary-600 text-white px-6 py-2.5 rounded-lg hover:bg-primary-700 disabled:opacity-50 font-medium">
            {searching ? 'Searching...' : '🔍 Search'}
          </button>
          <span className="text-gray-400 self-center">or</span>
          <input type="file" accept=".csv" ref={fileRef} onChange={handleUpload} className="hidden" id="csv-upload" />
          <label htmlFor="csv-upload" className="bg-gray-100 text-gray-700 px-4 py-2.5 rounded-lg hover:bg-gray-200 cursor-pointer font-medium">
            {uploading ? 'Uploading...' : '📁 Upload CSV'}
          </label>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Lead Lists Sidebar */}
        <div className="space-y-3">
          <h3 className="font-semibold text-gray-700">Lead Lists ({lists.length})</h3>
          {lists.map((list) => (
            <div
              key={list.id}
              onClick={() => loadListDetail(list.id)}
              className={`bg-white rounded-lg p-4 border cursor-pointer transition-all ${
                selectedList?.id === list.id ? 'border-primary-500 ring-1 ring-primary-500' : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <p className="font-medium text-sm truncate">{list.name}</p>
              <p className="text-xs text-gray-400 mt-1">{list.total_leads} leads · {list.source}</p>
              <p className="text-xs text-gray-400">{new Date(list.created_at).toLocaleDateString()}</p>
            </div>
          ))}
          {lists.length === 0 && <p className="text-sm text-gray-400">No lead lists yet. Search or upload CSV above.</p>}
        </div>

        {/* Lead Detail */}
        <div className="lg:col-span-3">
          {selectedList ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100">
              <div className="p-6 border-b border-gray-100 flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold">{selectedList.name}</h3>
                  <p className="text-sm text-gray-500">{selectedList.total_leads} leads · {selectedList.source}</p>
                </div>
                <div className="flex gap-2">
                  <select value={tone} onChange={(e) => setTone(e.target.value)} className="text-sm border rounded-lg px-2 py-1.5">
                    <option value="professional">Professional</option>
                    <option value="casual">Casual</option>
                    <option value="persuasive">Persuasive</option>
                  </select>
                  <button onClick={handleEnrich} disabled={enriching} className="bg-purple-600 text-white text-sm px-4 py-1.5 rounded-lg hover:bg-purple-700 disabled:opacity-50">
                    {enriching ? 'Enriching...' : '✨ AI Enrich'}
                  </button>
                  <button onClick={handleVerify} className="bg-green-600 text-white text-sm px-4 py-1.5 rounded-lg hover:bg-green-700">
                    ✓ Verify Emails
                  </button>
                  <button onClick={handleExport} className="bg-gray-100 text-gray-700 text-sm px-4 py-1.5 rounded-lg hover:bg-gray-200">
                    📥 Export
                  </button>
                  <button onClick={() => api.deleteLeadList(selectedList.id).then(() => { setSelectedList(null); loadLists(); })} className="text-red-500 text-sm px-3 py-1.5 rounded-lg hover:bg-red-50">
                    🗑️
                  </button>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Title</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Company</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">AI Intro</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {selectedList.leads?.map((lead: any) => (
                      <tr key={lead.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm">{lead.email}</td>
                        <td className="px-4 py-3 text-sm">{lead.first_name} {lead.last_name}</td>
                        <td className="px-4 py-3 text-sm text-gray-500">{lead.job_title}</td>
                        <td className="px-4 py-3 text-sm text-gray-500">{lead.company}</td>
                        <td className="px-4 py-3 text-xs text-gray-400 max-w-xs truncate">{lead.ai_intro || '—'}</td>
                        <td className="px-4 py-3">
                          <div className="flex gap-1">
                            {lead.email_verified && <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded">✓</span>}
                            {lead.ai_enriched && <span className="text-xs bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded">AI</span>}
                            {lead.is_contacted && <span className="text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">📧</span>}
                            {lead.is_replied && <span className="text-xs bg-yellow-100 text-yellow-700 px-1.5 py-0.5 rounded">💬</span>}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-xl p-12 shadow-sm border border-gray-100 text-center">
              <p className="text-gray-400 text-lg">👈 Select a lead list to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
