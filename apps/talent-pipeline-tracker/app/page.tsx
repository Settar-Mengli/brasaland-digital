import { STATUS_LABELS, STAGE_LABELS } from '@/lib/api';

export default function HomePage() {
  return (
    <main className="min-h-screen px-6 py-10 md:px-10">
      <div className="mx-auto max-w-6xl">
        {/* Page header */}
        <header className="mb-8">
          <h1 className="font-display text-4xl font-bold text-brasaland-charcoal">Candidates</h1>
          <p className="mt-2 text-brasaland-charcoal/70">Brasaland talent pipeline overview.</p>
        </header>

        {/* Filter bar — disabled, static */}
        <section
          aria-labelledby="filters-heading"
          className="rounded-lg border border-brasaland-charcoal/10 bg-brasaland-cream/40 p-4 mb-6"
        >
          <h2 id="filters-heading" className="sr-only">
            Filter candidates
          </h2>
          <div className="flex flex-col gap-3 md:flex-row md:items-end">
            <label className="flex flex-col gap-1 text-sm font-medium text-brasaland-charcoal">
              Status
              <select
                disabled
                className="border border-brasaland-charcoal/20 bg-brasaland-ivory px-3 py-2 rounded-md disabled:opacity-60"
              >
                <option value="">All statuses</option>
                {Object.entries(STATUS_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-1 text-sm font-medium text-brasaland-charcoal">
              Stage
              <select
                disabled
                className="border border-brasaland-charcoal/20 bg-brasaland-ivory px-3 py-2 rounded-md disabled:opacity-60"
              >
                <option value="">All stages</option>
                {Object.entries(STAGE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-1 text-sm font-medium text-brasaland-charcoal md:flex-1">
              Search
              <input
                type="search"
                disabled
                placeholder="Name, email, or position"
                className="border border-brasaland-charcoal/20 bg-brasaland-ivory px-3 py-2 rounded-md disabled:opacity-60"
              />
            </label>
          </div>
          <p className="mt-3 text-xs text-brasaland-charcoal/60">
            Filters become interactive in a later commit.
          </p>
        </section>

        {/* Candidate table */}
        <section
          aria-labelledby="candidates-heading"
          className="overflow-x-auto rounded-lg border border-brasaland-charcoal/10 bg-brasaland-ivory"
        >
          <h2 id="candidates-heading" className="sr-only">
            Candidate list
          </h2>
          <table className="w-full text-left text-sm">
            <thead className="bg-brasaland-cream/50 text-brasaland-charcoal">
              <tr>
                <th scope="col" className="px-4 py-3 font-semibold">
                  Name
                </th>
                <th scope="col" className="px-4 py-3 font-semibold">
                  Position
                </th>
                <th scope="col" className="px-4 py-3 font-semibold">
                  Experience
                </th>
                <th scope="col" className="px-4 py-3 font-semibold">
                  Status
                </th>
                <th scope="col" className="px-4 py-3 font-semibold">
                  Stage
                </th>
                <th scope="col" className="px-4 py-3 font-semibold">
                  Notes
                </th>
                <th scope="col" className="px-4 py-3 font-semibold">
                  Applied
                </th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td colSpan={7} className="px-4 py-10 text-center text-brasaland-charcoal/60">
                  Candidate rows will appear here once the data wiring lands.
                </td>
              </tr>
            </tbody>
          </table>
        </section>
      </div>
    </main>
  );
}
