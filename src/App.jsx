import React, { useState } from 'react';
import { Search, Network, FileText, Filter } from 'lucide-react';

export default function App() {
  const [query, setQuery] = useState('');

  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <header style={{ borderBottom: '1px solid #334155', paddingBottom: '1rem', marginBottom: '2rem' }}>
        <h1 style={{ color: '#ef4444', display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0 }}>
          <FileText size={32} /> MSF Document Vault
        </h1>
        <p style={{ color: '#94a3b8', marginTop: '0.5rem' }}>
          On-Premises Medical & Administrative Protocol Retrieval System
        </p>
      </header>

      <main style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        {/* Search Panel */}
        <section style={{ background: '#1e293b', padding: '1.5rem', borderRadius: '8px' }}>
          <h2 style={{ marginTop: 0, fontSize: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Search size={20} /> Document Search
          </h2>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
            <input
              type="text"
              placeholder="Search protocols (e.g. malaria treatment, logistics)..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              style={{
                flex: 1,
                padding: '0.75rem',
                borderRadius: '6px',
                border: '1px solid #475569',
                background: '#0f172a',
                color: '#fff'
              }}
            />
            <button style={{ padding: '0.75rem 1rem', background: '#ef4444', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>
              Search
            </button>
          </div>
          <div style={{ color: '#64748b', fontSize: '0.875rem' }}>
            <Filter size={14} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
            Ready to receive backend connections...
          </div>
        </section>

        {/* Spiderweb Visualization Placeholder */}
        <section style={{ background: '#1e293b', padding: '1.5rem', borderRadius: '8px', minHeight: '300px', display: 'flex', flexDirection: 'column' }}>
          <h2 style={{ marginTop: 0, fontSize: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Network size={20} /> Spiderweb Knowledge Graph
          </h2>
          <div style={{ flex: 1, border: '2px dashed #334155', borderRadius: '6px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}>
            Graph visualization workspace ready
          </div>
        </section>
      </main>
    </div>
  );
}