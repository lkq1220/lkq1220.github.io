export default function AcademicHomepageTemplate() {
  const navItems = ["Home", "Publications", "Experience", "Honors & Awards"];
  const tags = [
    "Research Area 1",
    "Research Area 2",
    "Research Area 3",
    "Research Area 4",
    "Research Area 5",
    "Research Area 6",
    "Research Area 7",
  ];

  const newsPrimary = [
    {
      date: "Apr. 2026",
      text: "Write your latest news here. Keep each entry concise and achievement-oriented.",
    },
    {
      date: "Mar. 2026",
      text: "Add a paper acceptance, release, invited talk, award, or other update here.",
    },
    {
      date: "Aug. 2025",
      text: "Add another highlight here.",
    },
    {
      date: "Aug. 2024",
      text: "Add another highlight here.",
    },
  ];

  const newsEarlier = [
    {
      date: "Mar. 2024",
      text: "Add an invited talk, workshop, webinar, or professional activity here.",
      links: ["website", "video", "slides"],
    },
    {
      date: "Sep. 2023",
      text: "Add a position change, appointment, or milestone here.",
    },
    {
      date: "Jul. 2023",
      text: "Add a degree completion or dissertation milestone here.",
    },
    {
      date: "Jul. 2022",
      text: "Add an earlier update here.",
    },
  ];

  const repos = [
    {
      title: "Repository Title 1",
      desc: "Short one-line description of the code repository or project.",
      stars: 106,
    },
    {
      title: "Repository Title 2",
      desc: "Short one-line description of the code repository or project.",
      stars: 47,
    },
    {
      title: "Repository Title 3",
      desc: "Short one-line description of the code repository or project.",
      stars: 27,
    },
    {
      title: "Repository Title 4",
      desc: "Short one-line description of the code repository or project.",
      stars: 24,
    },
    {
      title: "Repository Title 5",
      desc: "Short one-line description of the code repository or project.",
      stars: 11,
    },
    {
      title: "Repository Title 6",
      desc: "Short one-line description of the code repository or project.",
      stars: 9,
    },
  ];

  const sidebarLinks = [
    "Email",
    "ResearchGate",
    "Google Scholar",
  ];

  return (
    <div className="min-h-screen bg-[#f7f7f8] text-[#3e4650]">
      <header className="sticky top-0 z-20 border-b border-[#e5e7eb] bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center gap-4 px-6 py-4 lg:px-10">
          <div className="flex gap-3 text-[15px] font-medium text-[#4b5563]">
            {navItems.map((item, idx) => (
              <button
                key={item}
                className={`rounded-md px-4 py-2 transition ${
                  idx === 0
                    ? "border border-[#f0b35f] bg-[#fffaf2] text-[#334155]"
                    : "hover:bg-[#f3f4f6]"
                }`}
              >
                {item}
              </button>
            ))}
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl grid-cols-1 gap-10 px-6 py-10 lg:grid-cols-[290px_minmax(0,1fr)] lg:px-10">
        <aside className="lg:sticky lg:top-24 lg:self-start">
          <div className="flex flex-col items-start">
            <div className="h-44 w-44 overflow-hidden rounded-full border border-[#d9dee6] bg-gradient-to-b from-[#cdd5df] to-[#b7c2cf] shadow-sm">
              <div className="flex h-full items-center justify-center text-sm text-white/90">
                Profile Photo
              </div>
            </div>

            <h1 className="mt-6 text-[22px] font-semibold tracking-tight text-[#2f3742]">
              Your Name
            </h1>

            <div className="mt-3 space-y-2 text-[15px] leading-7 text-[#58616e]">
              <p>Institute / Department Name</p>
              <p>University / Organization</p>
              <p>Current Position Title</p>
            </div>

            <div className="mt-5 space-y-3 text-[15px] text-[#4b5563]">
              <div className="flex items-start gap-3">
                <span>📍</span>
                <span>City, Country</span>
              </div>
              <div className="flex items-start gap-3">
                <span>🏛️</span>
                <span>Affiliation</span>
              </div>
              {sidebarLinks.map((item) => (
                <div key={item} className="flex items-start gap-3">
                  <span>✉️</span>
                  <a href="#" className="hover:text-[#2563eb] hover:underline">
                    {item}
                  </a>
                </div>
              ))}
            </div>
          </div>
        </aside>

        <section className="min-w-0">
          <section>
            <h2 className="text-[20px] font-semibold text-[#374151]">About Me</h2>
            <div className="mt-5 space-y-4 text-[17px] leading-9 text-[#4b5563]">
              <p>
                Write your academic biography here. This section can include your degree history,
                advisors, previous appointments, current position, and broad research focus. Keep
                the paragraph professional and easy to scan.
              </p>
              <p>
                You can later replace this placeholder with a longer biography, a shorter summary,
                or multiple paragraphs depending on the style you want for the homepage.
              </p>
            </div>

            <div className="mt-6 flex flex-wrap gap-3">
              {tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full bg-[#eaf1ff] px-4 py-2 text-[14px] font-medium text-[#2563eb]"
                >
                  {tag}
                </span>
              ))}
            </div>
          </section>

          <section className="mt-12">
            <div className="flex items-center gap-3">
              <span className="text-[26px]">🔥</span>
              <h2 className="text-[20px] font-semibold text-[#374151]">News</h2>
            </div>

            <Timeline items={newsPrimary} />

            <button className="mt-4 rounded-md border border-[#d1d5db] bg-white px-5 py-2.5 text-[15px] text-[#4b5563] shadow-sm hover:bg-[#f9fafb]">
              View Earlier News
            </button>

            <Timeline items={newsEarlier} className="mt-5" />
          </section>

          <section className="mt-14">
            <h2 className="text-[20px] font-semibold text-[#374151]">Selected Code Repositories</h2>
            <div className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-2">
              {repos.map((repo) => (
                <div
                  key={repo.title}
                  className="rounded-2xl border border-[#e5e7eb] bg-white p-4 shadow-sm"
                >
                  <div className="flex items-start justify-between gap-4">
                    <a href="#" className="text-[15px] font-semibold text-[#2563eb] hover:underline">
                      {repo.title}
                    </a>
                    <div className="shrink-0 rounded-md border border-[#d1d5db] px-2 py-1 text-[12px] text-[#4b5563]">
                      ★ {repo.stars}
                    </div>
                  </div>
                  <p className="mt-2 text-[15px] leading-7 text-[#6b7280]">{repo.desc}</p>
                </div>
              ))}
            </div>
          </section>
        </section>
      </main>
    </div>
  );
}

function Timeline({ items, className = "mt-7" }) {
  return (
    <div className={className}>
      <div className="relative pl-8">
        <div className="absolute left-[10px] top-1 bottom-1 w-[3px] rounded-full bg-[#2563eb]" />
        <div className="space-y-8">
          {items.map((item, idx) => (
            <div key={idx} className="relative">
              <div className="absolute left-[-22px] top-[10px] h-3.5 w-3.5 rounded-full border-2 border-white bg-[#2563eb] shadow-sm" />
              <div className="text-[17px] leading-8 text-[#4b5563]">
                <span className="mr-4 inline-block min-w-[95px] font-semibold text-[#4b5563]">
                  {item.date}
                </span>
                <span>{item.text}</span>
                {item.links?.length ? (
                  <span className="ml-2 inline-flex flex-wrap gap-2">
                    {item.links.map((link) => (
                      <a key={link} href="#" className="text-[#2563eb] underline underline-offset-2">
                        [{link}]
                      </a>
                    ))}
                  </span>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
