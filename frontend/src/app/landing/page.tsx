import Link from 'next/link';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Hero */}
      <div className="max-w-6xl mx-auto px-6 py-20">
        <nav className="flex items-center justify-between mb-20">
          <h1 className="text-2xl font-bold text-gray-900">🚀 AI Outreach</h1>
          <div className="flex gap-4">
            <Link href="/auth/login" className="text-gray-600 hover:text-gray-900 font-medium">Login</Link>
            <Link href="/auth/register" className="bg-primary-600 text-white px-5 py-2.5 rounded-lg hover:bg-primary-700 font-medium">Get Started Free</Link>
          </div>
        </nav>

        <div className="text-center max-w-4xl mx-auto">
          <div className="inline-block bg-primary-100 text-primary-700 px-4 py-1.5 rounded-full text-sm font-medium mb-6">
            AI-Powered Email Outreach
          </div>
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6 leading-tight">
            Find Leads. Personalize with AI. <span className="text-primary-600">Send at Scale.</span>
          </h1>
          <p className="text-xl text-gray-600 mb-10 max-w-2xl mx-auto">
            The all-in-one platform for cold email outreach. Find verified business leads, generate personalized intros with AI, and send bulk campaigns with high deliverability.
          </p>
          <div className="flex gap-4 justify-center">
            <Link href="/auth/register" className="bg-primary-600 text-white px-8 py-4 rounded-xl hover:bg-primary-700 font-semibold text-lg shadow-lg shadow-primary-500/30">
              Start Free — 100 Credits
            </Link>
            <Link href="#features" className="bg-white text-gray-700 px-8 py-4 rounded-xl hover:bg-gray-50 font-semibold text-lg border border-gray-200">
              See Features
            </Link>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-8 max-w-2xl mx-auto mt-20">
          {[
            { value: '10x', label: 'Faster Lead Gen' },
            { value: '45%', label: 'Avg Open Rate' },
            { value: '$0.003', label: 'Per Email' },
          ].map((stat) => (
            <div key={stat.label} className="text-center">
              <p className="text-3xl font-bold text-primary-600">{stat.value}</p>
              <p className="text-sm text-gray-500 mt-1">{stat.label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Features */}
      <div id="features" className="max-w-6xl mx-auto px-6 py-20">
        <h2 className="text-3xl font-bold text-center mb-16">Everything You Need for Cold Email</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {[
            { icon: '🔍', title: 'Lead Discovery', desc: 'Search by industry, location, job title. Apollo.io & Hunter.io integration. CSV upload.' },
            { icon: '🤖', title: 'AI Personalization', desc: 'AI writes unique intro per lead. References company news, role, industry. 3 tones.' },
            { icon: '📧', title: 'Bulk Email Sending', desc: 'SendGrid, SES, Mailgun, Resend support. Rate limiting. Send windows.' },
            { icon: '📊', title: 'Real-time Tracking', desc: 'Open, click, reply tracking. Campaign analytics. Export to CSV.' },
            { icon: '🔥', title: 'Email Warm-up', desc: '14-day automatic warm-up. Builds sender reputation. Avoids spam folders.' },
            { icon: '🧪', title: 'A/B Testing', desc: 'Test subject lines. Auto-select winner. Data-driven optimization.' },
          ].map((f) => (
            <div key={f.title} className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
              <div className="text-4xl mb-4">{f.icon}</div>
              <h3 className="text-xl font-semibold mb-2">{f.title}</h3>
              <p className="text-gray-600">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Pricing */}
      <div className="max-w-6xl mx-auto px-6 py-20">
        <h2 className="text-3xl font-bold text-center mb-4">Simple, Transparent Pricing</h2>
        <p className="text-center text-gray-500 mb-16">Start free. Scale as you grow.</p>
        <div className="grid md:grid-cols-4 gap-6">
          {[
            { name: 'Free', price: '$0', credits: '100', features: ['Basic search', 'CSV upload', 'SMTP sending'] },
            { name: 'Starter', price: '$49', credits: '2,000', features: ['Apollo + Hunter', 'AI personalization', 'SendGrid/SES', 'Analytics'], popular: true },
            { name: 'Pro', price: '$149', credits: '10,000', features: ['Everything in Starter', 'A/B testing', 'Follow-ups', 'API access'] },
            { name: 'Enterprise', price: '$499', credits: '50,000', features: ['Everything in Pro', 'Dedicated IP', 'Custom integrations', 'Account manager'] },
          ].map((plan) => (
            <div key={plan.name} className={`bg-white rounded-2xl p-8 border ${plan.popular ? 'border-primary-500 ring-2 ring-primary-500 shadow-lg' : 'border-gray-200'} relative`}>
              {plan.popular && <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary-600 text-white text-xs px-3 py-1 rounded-full">Most Popular</div>}
              <h3 className="text-lg font-semibold">{plan.name}</h3>
              <p className="text-4xl font-bold mt-2">{plan.price}<span className="text-sm text-gray-400">/mo</span></p>
              <p className="text-primary-600 font-medium mt-1">{plan.credits} credits</p>
              <ul className="mt-6 space-y-2">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-center gap-2 text-sm text-gray-600">
                    <span className="text-green-500">✓</span> {f}
                  </li>
                ))}
              </ul>
              <Link href="/auth/register" className={`block mt-8 text-center py-3 rounded-lg font-medium ${plan.popular ? 'bg-primary-600 text-white hover:bg-primary-700' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}>
                Get Started
              </Link>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <footer className="max-w-6xl mx-auto px-6 py-12 border-t border-gray-200">
        <div className="flex items-center justify-between">
          <p className="text-gray-500">© 2026 AI Outreach. All rights reserved.</p>
          <div className="flex gap-6">
            <Link href="/privacy" className="text-gray-500 hover:text-gray-700">Privacy</Link>
            <Link href="/terms" className="text-gray-500 hover:text-gray-700">Terms</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
