# Иван — checklist соответствия документу

| Пункт документа | Где реализовано |
|---|---|
| Создать frontend project | `package.json`, `vite.config.ts`, `src/main.tsx` |
| Vite / React | `package.json`, `src/app/*` |
| Tailwind | `tailwind.config.js`, `src/index.css` |
| Layout | `src/widgets/Layout/*` |
| Navigation | `src/widgets/Layout/navigation.ts`, `Sidebar.tsx` |
| Demo-friendly UI | все страницы + mock mode |
| Tasks page | `src/pages/TasksPage.tsx` |
| AI Suggestions page | `src/pages/SuggestionsPage.tsx` |
| Meetings page | `src/pages/MeetingsPage.tsx` |
| Analytics page | `src/pages/AnalyticsPage.tsx` |
| Profile page | `src/pages/ProfilePage.tsx` |
| Mini-kanban | `src/widgets/Kanban/*` |
| Task fields | `TaskCard.tsx` |
| Task status change | `shared/api/tasks.ts` |
| Task reschedule | `shared/api/tasks.ts` |
| Pending TaskCandidates | `SuggestionsPage.tsx`, `SuggestionsList.tsx` |
| Confirm / reject | `shared/api/candidates.ts`, `SuggestionCard.tsx` |
| Edit locally | `SuggestionCard.tsx` |
| Open source message | `SuggestionCard.tsx` |
| Meeting short summary | `MeetingSummary.tsx` |
| Decisions | `MeetingSummary.tsx` |
| Action items | `MeetingSummary.tsx` |
| Risks | `MeetingSummary.tsx` |
| Open questions | `MeetingSummary.tsx` |
| Created tasks | `MeetingSummary.tsx` |
| MVP analytics | `AnalyticsGrid.tsx` |
| Empty states | `EmptyState.tsx` + pages |
| Loading skeletons/loaders | `Loader.tsx` + pages |
| Readable cards | `Card.tsx` + widgets |
| Source badges | `Badge.tsx`, `TaskCard.tsx`, `SuggestionCard.tsx` |
| Confidence badge | `TaskCard.tsx`, `SuggestionCard.tsx`, `MeetingSummary.tsx` |
| Quick access pages | sidebar navigation |
| Backup mock data | `shared/api/mock.ts`, `VITE_USE_MOCKS` |
| Team Analytics | `AnalyticsPage.tsx` |
| My Profile | `ProfilePage.tsx` |
| Achievements | `Achievements.tsx`, leaderboard |
| Knowledge Base preview | `KnowledgePreview.tsx` |
| Roadmap cards | `RoadmapCards.tsx` |
