import { useEffect, useState } from 'react'

const demoOrganizations = [
  { id: 1, name: 'Tech Academy', email: 'tech@example.com', type: 'Education', status: 'Pending' },
  { id: 2, name: 'Future Company', email: 'future@example.com', type: 'Technology', status: 'Pending' }
]

const demoOpportunities = [
  {
    id: 1, title: 'AI Internship', organization: 'Tech Academy',
    category: 'Internship', description: 'Artificial intelligence training.',
    deadline: '2026-12-20', status: 'Pending'
  }
]

const demoUsers = [
  { id: 1, name: 'Sara Ahmed', email: 'sara@example.com', role: 'Student', status: 'Active' },
  { id: 2, name: 'Tech Academy', email: 'tech@example.com', role: 'Organization', status: 'Active' }
]

const demoApplications = [
  { id: 1, student: 'Sara Ahmed', opportunity: 'AI Internship', status: 'Pending' }
]

function load(key, fallback) {
  try {
    const saved = localStorage.getItem(key)
    return saved ? JSON.parse(saved) : fallback
  } catch {
    return fallback
  }
}

function App() {
  const [role, setRole] = useState('Admin')
  const [page, setPage] = useState('Dashboard')
  const [organizations, setOrganizations] = useState(() => load('bloom_orgs', demoOrganizations))
  const [opportunities, setOpportunities] = useState(() => load('bloom_opps', demoOpportunities))
  const [users, setUsers] = useState(() => load('bloom_users', demoUsers))
  const [applications, setApplications] = useState(() => load('bloom_apps', demoApplications))
  const [selected, setSelected] = useState(null)
  const [editing, setEditing] = useState(null)
  const [message, setMessage] = useState('')

  const [form, setForm] = useState({
    title: '', category: 'Internship',
    description: '', deadline: ''
  })

  const organizationName = 'Tech Academy'

  useEffect(() => {
    localStorage.setItem('bloom_orgs', JSON.stringify(organizations))
    localStorage.setItem('bloom_opps', JSON.stringify(opportunities))
    localStorage.setItem('bloom_users', JSON.stringify(users))
    localStorage.setItem('bloom_apps', JSON.stringify(applications))
  }, [organizations, opportunities, users, applications])

  const adminPages = ['Dashboard', 'Organizations', 'Opportunities', 'Users']
  const orgPages = ['Dashboard', 'Add Opportunity', 'My Opportunities', 'Applications']

  const pendingOrgs = organizations.filter(x => x.status === 'Pending')
  const pendingOpps = opportunities.filter(x => x.status === 'Pending')
  const myOpps = opportunities.filter(x => x.organization === organizationName)

  const button = 'rounded-lg px-4 py-2 text-sm font-medium text-white'
  const pink = button + ' bg-pink-600 hover:bg-pink-700'
  const green = button + ' bg-green-600 hover:bg-green-700'
  const red = button + ' bg-red-600 hover:bg-red-700'

  function navigate(next) {
    setPage(next)
    setSelected(null)
    setMessage('')
  }

  function changeRole(next) {
    setRole(next)
    navigate('Dashboard')
  }

  function updateOrg(id, status) {
    setOrganizations(items => items.map(x => x.id === id ? { ...x, status } : x))
    setSelected(null)
    setMessage('Organization status updated successfully.')
  }

  function updateOpp(id, status) {
    setOpportunities(items => items.map(x => x.id === id ? { ...x, status } : x))
    setSelected(null)
    setMessage('Opportunity status updated successfully.')
  }

  function saveOpportunity(e) {
    e.preventDefault()

    if (!form.title.trim() || !form.description.trim() || !form.deadline) {
      setMessage('Please complete all fields.')
      return
    }

    if (editing !== null) {
      setOpportunities(items => items.map(x =>
        x.id === editing
          ? { ...x, ...form, status: 'Pending' }
          : x
      ))
      setMessage('Opportunity updated and sent for admin review.')
    } else {
      const newOpportunity = {
        id: Date.now(),
        ...form,
        organization: organizationName,
        status: 'Pending'
      }
      setOpportunities(items => [...items, newOpportunity])
      setMessage('Opportunity submitted for admin review.')
    }

    setEditing(null)
    setForm({ title: '', category: 'Internship', description: '', deadline: '' })
    setPage('My Opportunities')
  }

  function startEdit(item) {
    setEditing(item.id)
    setForm({
      title: item.title,
      category: item.category,
      description: item.description,
      deadline: item.deadline
    })
    navigate('Add Opportunity')
  }

  function deleteOpportunity(id) {
    if (!window.confirm('Delete this opportunity?')) return
    setOpportunities(items => items.filter(x => x.id !== id))
    setMessage('Opportunity deleted.')
  }

  function updateUser(id, status) {
    setUsers(items => items.map(x => x.id === id ? { ...x, status } : x))
    setMessage('User account updated.')
  }

  function updateApplication(id, status) {
    setApplications(items => items.map(x => x.id === id ? { ...x, status } : x))
    setMessage('Application status updated.')
  }

  function Table({ headers, children }) {
    return (
      <div className="mt-5 overflow-x-auto rounded-xl bg-white shadow-sm">
        <table className="w-full min-w-[650px] text-left text-sm">
          <thead className="bg-pink-50">
            <tr>
              {headers.map(h => <th key={h} className="p-4">{h}</th>)}
            </tr>
          </thead>
          <tbody>{children}</tbody>
        </table>
      </div>
    )
  }

  function Status({ value }) {
    const colors = {
      Pending: 'bg-yellow-100 text-yellow-700',
      Approved: 'bg-green-100 text-green-700',
      Rejected: 'bg-red-100 text-red-700',
      Active: 'bg-green-100 text-green-700',
      Suspended: 'bg-red-100 text-red-700',
      Accepted: 'bg-green-100 text-green-700'
    }

    return (
      <span className={`rounded-full px-3 py-1 text-xs ${colors[value] || 'bg-gray-100'}`}>
        {value}
      </span>
    )
  }

  function Stat({ label, value }) {
    return (
      <div className="rounded-xl bg-white p-6 shadow-sm">
        <p className="text-sm text-gray-500">{label}</p>
        <p className="mt-3 text-3xl font-bold text-pink-700">{value}</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 md:flex">
      <aside className="bg-white p-6 shadow-sm md:min-h-screen md:w-64">
        <h1 className="text-3xl font-bold text-pink-700">Bloom</h1>
        <p className="mt-1 text-sm text-gray-500">Student Opportunities Platform</p>

        <label className="mt-8 block text-sm font-medium text-gray-700">
          Demo View
        </label>
        <select
          value={role}
          onChange={e => changeRole(e.target.value)}
          className="mt-2 w-full rounded-lg border border-gray-200 p-3"
        >
          <option value="Admin">Admin</option>
          <option value="Organization">Organization</option>
        </select>

        <p className="mb-3 mt-8 text-xs font-semibold uppercase text-gray-400">
          {role} Panel
        </p>

        {(role === 'Admin' ? adminPages : orgPages).map(item => (
          <button
            key={item}
            onClick={() => navigate(item)}
            className={`mb-2 block w-full rounded-lg p-3 text-left text-sm ${
              page === item
                ? 'bg-pink-100 font-semibold text-pink-700'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            {item}
          </button>
        ))}
      </aside>

      <main className="min-w-0 flex-1 p-5 md:p-10">
        <div className="mb-7">
          <h1 className="text-3xl font-bold text-gray-800">{page}</h1>
          <p className="mt-2 text-gray-500">
            {role === 'Admin'
              ? 'Bloom Administrator Dashboard'
              : 'Bloom Organization Dashboard'}
          </p>
        </div>

        {message && (
          <div className="mb-5 rounded-lg bg-pink-50 p-4 text-sm text-pink-800">
            {message}
          </div>
        )}

        {role === 'Admin' && page === 'Dashboard' && (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            <Stat label="Pending Organizations" value={pendingOrgs.length} />
            <Stat label="Pending Opportunities" value={pendingOpps.length} />
            <Stat label="Total Users" value={users.length} />
          </div>
        )}

        {role === 'Admin' && page === 'Organizations' && (
          <>
            <Stat label="Pending Registrations" value={pendingOrgs.length} />

            <Table headers={['Organization', 'Type', 'Status', 'Action']}>
              {pendingOrgs.map(org => (
                <tr key={org.id} className="border-t border-gray-100">
                  <td className="p-4">{org.name}</td>
                  <td className="p-4">{org.type}</td>
                  <td className="p-4"><Status value={org.status} /></td>
                  <td className="p-4">
                    <button className={pink} onClick={() => setSelected(org)}>
                      Review
                    </button>
                  </td>
                </tr>
              ))}
            </Table>

            {pendingOrgs.length === 0 && <p className="mt-4 text-gray-500">No pending registrations.</p>}

            {selected && (
              <div className="mt-6 rounded-xl bg-white p-6 shadow-sm">
                <h2 className="text-xl font-bold">Organization Details</h2>
                <p className="mt-4">Name: {selected.name}</p>
                <p className="mt-2">Email: {selected.email}</p>
                <p className="mt-2">Type: {selected.type}</p>
                <div className="mt-5 flex flex-wrap gap-3">
                  <button className={green} onClick={() => updateOrg(selected.id, 'Approved')}>Approve</button>
                  <button className={red} onClick={() => updateOrg(selected.id, 'Rejected')}>Reject</button>
                  <button className="rounded-lg bg-gray-200 px-4 py-2" onClick={() => setSelected(null)}>Cancel</button>
                </div>
              </div>
            )}
          </>
        )}

        {role === 'Admin' && page === 'Opportunities' && (
          <>
            <Stat label="Pending Opportunities" value={pendingOpps.length} />

            <Table headers={['Opportunity', 'Organization', 'Status', 'Action']}>
              {pendingOpps.map(opp => (
                <tr key={opp.id} className="border-t border-gray-100">
                  <td className="p-4">{opp.title}</td>
                  <td className="p-4">{opp.organization}</td>
                  <td className="p-4"><Status value={opp.status} /></td>
                  <td className="p-4">
                    <button className={pink} onClick={() => setSelected(opp)}>Review</button>
                  </td>
                </tr>
              ))}
            </Table>

            {pendingOpps.length === 0 && <p className="mt-4 text-gray-500">No pending opportunities.</p>}

            {selected && (
              <div className="mt-6 rounded-xl bg-white p-6 shadow-sm">
                <h2 className="text-xl font-bold">Opportunity Details</h2>
                <p className="mt-4">Title: {selected.title}</p>
                <p className="mt-2">Organization: {selected.organization}</p>
                <p className="mt-2">Category: {selected.category}</p>
                <p className="mt-2">Description: {selected.description}</p>
                <p className="mt-2">Deadline: {selected.deadline}</p>
                <div className="mt-5 flex flex-wrap gap-3">
                  <button className={green} onClick={() => updateOpp(selected.id, 'Approved')}>Approve</button>
                  <button className={red} onClick={() => updateOpp(selected.id, 'Rejected')}>Reject</button>
                  <button className="rounded-lg bg-gray-200 px-4 py-2" onClick={() => setSelected(null)}>Cancel</button>
                </div>
              </div>
            )}
          </>
        )}

        {role === 'Admin' && page === 'Users' && (
          <Table headers={['Name', 'Email', 'Role', 'Status', 'Action']}>
            {users.map(user => (
              <tr key={user.id} className="border-t border-gray-100">
                <td className="p-4">{user.name}</td>
                <td className="p-4">{user.email}</td>
                <td className="p-4">{user.role}</td>
                <td className="p-4"><Status value={user.status} /></td>
                <td className="p-4">
                  <button
                    className={user.status === 'Active' ? red : green}
                    onClick={() => updateUser(user.id, user.status === 'Active' ? 'Suspended' : 'Active')}
                  >
                    {user.status === 'Active' ? 'Suspend' : 'Activate'}
                  </button>
                </td>
              </tr>
            ))}
          </Table>
        )}

        {role === 'Organization' && page === 'Dashboard' && (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            <Stat label="My Opportunities" value={myOpps.length} />
            <Stat label="Approved Opportunities" value={myOpps.filter(x => x.status === 'Approved').length} />
            <Stat label="Applications" value={applications.filter(a => myOpps.some(o => o.title === a.opportunity)).length} />
          </div>
        )}

        {role === 'Organization' && page === 'Add Opportunity' && (
          <form onSubmit={saveOpportunity} className="max-w-2xl rounded-xl bg-white p-6 shadow-sm">
            <h2 className="mb-6 text-xl font-bold">
              {editing !== null ? 'Edit Opportunity' : 'Create New Opportunity'}
            </h2>

            <label className="mb-2 block font-medium">Opportunity Title</label>
            <input
              value={form.title}
              onChange={e => setForm({ ...form, title: e.target.value })}
              className="mb-5 w-full rounded-lg border border-gray-200 p-3"
              placeholder="Enter opportunity title"
              required
            />

            <label className="mb-2 block font-medium">Category</label>
            <select
              value={form.category}
              onChange={e => setForm({ ...form, category: e.target.value })}
              className="mb-5 w-full rounded-lg border border-gray-200 p-3"
            >
              <option>Internship</option>
              <option>Workshop</option>
              <option>Training</option>
              <option>Competition</option>
              <option>Volunteering</option>
            </select>

            <label className="mb-2 block font-medium">Description</label>
            <textarea
              value={form.description}
              onChange={e => setForm({ ...form, description: e.target.value })}
              className="mb-5 w-full rounded-lg border border-gray-200 p-3"
              rows="4"
              placeholder="Describe the opportunity"
              required
            />

            <label className="mb-2 block font-medium">Application Deadline</label>
            <input
              type="date"
              value={form.deadline}
              onChange={e => setForm({ ...form, deadline: e.target.value })}
              className="mb-6 w-full rounded-lg border border-gray-200 p-3"
              required
            />

            <button type="submit" className={pink}>
              {editing !== null ? 'Save Changes' : 'Submit Opportunity'}
            </button>
          </form>
        )}

        {role === 'Organization' && page === 'My Opportunities' && (
          <>
            <button
              className={pink}
              onClick={() => {
                setEditing(null)
                setForm({ title: '', category: 'Internship', description: '', deadline: '' })
                navigate('Add Opportunity')
              }}
            >
              + Add Opportunity
            </button>

            <Table headers={['Title', 'Category', 'Deadline', 'Status', 'Actions']}>
              {myOpps.map(opp => (
                <tr key={opp.id} className="border-t border-gray-100">
                  <td className="p-4">{opp.title}</td>
                  <td className="p-4">{opp.category}</td>
                  <td className="p-4">{opp.deadline}</td>
                  <td className="p-4"><Status value={opp.status} /></td>
                  <td className="p-4">
                    <div className="flex gap-2">
                      <button className={pink} onClick={() => startEdit(opp)}>Edit</button>
                      <button className={red} onClick={() => deleteOpportunity(opp.id)}>Delete</button>
                    </div>
                  </td>
                </tr>
              ))}
            </Table>

            {myOpps.length === 0 && <p className="mt-4 text-gray-500">No opportunities yet.</p>}
          </>
        )}

        {role === 'Organization' && page === 'Applications' && (
          <>
            <Table headers={['Student', 'Opportunity', 'Status', 'Action']}>
              {applications
                .filter(a => myOpps.some(o => o.title === a.opportunity))
                .map(app => (
                  <tr key={app.id} className="border-t border-gray-100">
                    <td className="p-4">{app.student}</td>
                    <td className="p-4">{app.opportunity}</td>
                    <td className="p-4"><Status value={app.status} /></td>
                    <td className="p-4">
                      {app.status === 'Pending' ? (
                        <div className="flex gap-2">
                          <button className={green} onClick={() => updateApplication(app.id, 'Accepted')}>Accept</button>
                          <button className={red} onClick={() => updateApplication(app.id, 'Rejected')}>Reject</button>
                        </div>
                      ) : 'Reviewed'}
                    </td>
                  </tr>
                ))}
            </Table>
          </>
        )}

        <p className="mt-8 text-xs text-gray-400">
          Demo mode — data is stored in this browser only.
        </p>
      </main>
    </div>
  )
}

export default App