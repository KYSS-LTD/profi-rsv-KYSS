import { TeamAnalytics } from '../../entities/analytics/types';
import { TaskCandidate } from '../../entities/candidate/types';
import { MeetingSummary } from '../../entities/meeting/types';
import { Task } from '../../entities/task/types';
import { Achievement, Note, Recommendation, UserDigest, UserProfile } from '../../entities/user/types';

export const mockTasks: Task[] = [
  {
    id: 'task_1',
    title: 'Подключить Telegram webhook',
    description: 'Принять update, сохранить message и отправить job в очередь.',
    assignee: 'Даниил',
    deadline: '2026-06-03T18:00:00+03:00',
    status: 'in_progress',
    priority: 'high',
    source: 'telegram_text',
    confidence: 0.93,
    created_by_ai: true,
    kanban_provider: 'external',
    external_kanban_url: 'https://kanban.example/card/task_1',
    source_message_excerpt: 'Даниил, подключи webhook сегодня к вечеру.',
    status_changed_count: 2,
  },
  {
    id: 'task_2',
    title: 'Собрать макет панели',
    description: 'Навигация, страницы и интерфейс, удобный для демо.',
    assignee: 'Иван',
    deadline: '2026-06-03T20:00:00+03:00',
    status: 'review',
    priority: 'high',
    source: 'telegram_text',
    confidence: 0.89,
    created_by_ai: true,
    kanban_provider: 'internal',
    source_message_excerpt: 'Иван, подготовь UI доски сегодня вечером.',
    status_changed_count: 4,
  },
  {
    id: 'task_3',
    title: 'Проверить ASR для голосовых',
    description: 'Прогнать тестовую голосовую фразу и сохранить качество транскрипта.',
    assignee: 'Алексей',
    deadline: '2026-06-04T12:00:00+03:00',
    status: 'todo',
    priority: 'medium',
    source: 'telegram_voice',
    confidence: 0.78,
    created_by_ai: true,
    kanban_provider: 'internal',
    source_message_excerpt: 'Голосовое: надо проверить распознавание голосовых.',
    status_changed_count: 1,
  },
  {
    id: 'task_4',
    title: 'Собрать prompt для summary встречи',
    description: 'Вернуть краткое summary, решения, действия после встречи, риски и открытые вопросы.',
    assignee: 'Павел',
    deadline: '2026-06-04T18:00:00+03:00',
    status: 'backlog',
    priority: 'medium',
    source: 'meeting_audio',
    confidence: 0.84,
    created_by_ai: true,
    kanban_provider: 'external',
    external_kanban_url: 'https://kanban.example/card/task_4',
    source_message_excerpt: 'На встрече договорились подготовить prompt для summary.',
    status_changed_count: 0,
  },
  {
    id: 'task_5',
    title: 'Закрыть полировку демо',
    description: 'Проверить загрузку, пустые состояния, ссылки и финальный сценарий.',
    assignee: 'Иван',
    deadline: '2026-06-04T21:00:00+03:00',
    status: 'done',
    priority: 'critical',
    source: 'telegram_text',
    confidence: 0.96,
    created_by_ai: true,
    kanban_provider: 'internal',
    source_message_excerpt: 'К вечеру надо собрать демо.',
    status_changed_count: 5,
  },
];

export const mockCandidates: TaskCandidate[] = [
  {
    id: 'candidate_1',
    title: 'Сделать кнопку переноса дедлайна',
    description: 'Добавить действие в карточке задачи и отправлять POST /tasks/{id}/reschedule.',
    assignee_raw: 'Иван',
    deadline_raw: 'сегодня вечером',
    deadline: '2026-06-03T20:00:00+03:00',
    priority: 'medium',
    confidence: 0.73,
    status: 'pending',
    source: 'telegram_text',
    missing_fields: [],
    source_excerpt: 'Иван, еще сделай перенос дедлайна через dashboard.',
    source_message_url: 'https://t.me/c/123456/1001',
  },
  {
    id: 'candidate_2',
    title: 'Проверить качество распознавания встречи',
    description: 'Нужно качество транскрипта и пример очистки текста до/после.',
    assignee_raw: 'Алексей',
    deadline_raw: 'завтра',
    priority: 'high',
    confidence: 0.68,
    status: 'pending',
    source: 'meeting_audio',
    missing_fields: ['deadline'],
    source_excerpt: 'На созвоне решили проверить качество ASR для meeting audio.',
    source_message_url: 'https://t.me/c/123456/1002',
  },
];

export const mockMeeting: MeetingSummary = {
  id: 'meeting_1',
  title: 'Ежедневная встреча: MVP Командус',
  summary: 'Команда согласовала основной сценарий: сообщение в Telegram → извлечение задачи AI → кандидат задачи → подтверждение → карточка в канбане → напоминание → dashboard.',
  decisions: [
    'Для фронтенда используем React + Vite + Tailwind.',
    'Панель остается удобной для демо и не превращается в сложный таск-трекер.',
    'Backend отдает задачи, кандидатов, аналитику, профиль и summary встреч через REST API.',
  ],
  action_items: [
    { title: 'Закрыть мини-канбан', assignee: 'Иван', deadline: 'сегодня' },
    { title: 'Подготовить pipeline извлечения задач', assignee: 'Павел', deadline: 'завтра' },
    { title: 'Поднять endpoint /analytics/team', assignee: 'Даниил', deadline: 'завтра' },
  ],
  risks: ['Backend API может быть не готов к дню демо.', 'API внешней канбан-доски может упасть.'],
  open_questions: ['Какую внешнюю канбан-доску выбираем для P0?', 'Нужен ли live listener для Телемоста или хватит загрузки аудио?'],
  created_task_candidates: mockCandidates,
  created_tasks: [
    { id: 'task_2', title: 'Собрать макет панели', assignee: 'Иван', deadline: 'сегодня', status: 'review' },
    { id: 'task_4', title: 'Собрать prompt для summary встречи', assignee: 'Павел', deadline: 'завтра', status: 'backlog' },
  ],
  transcript_quality: 0.91,
};

export const mockAnalytics: TeamAnalytics = {
  ai_created_tasks: 12,
  auto_confirmed: 8,
  waiting_confirmation: 3,
  rejected_suggestions: 1,
  voice_messages_processed: 4,
  meetings_summarized: 1,
  average_confidence: 0.87,
  overdue_tasks: 2,
  done_tasks: 5,
  team_velocity: {
    done_this_week: 18,
    avg_lead_time_hours: 14.5,
    overdue_percent: 12,
  },
  ai_quality: {
    average_confidence: 0.87,
    auto_created: 8,
    rejected_suggestions: 1,
  },
};

export const mockProfile: UserProfile = {
  id: 'user_ivan',
  name: 'Иван',
  telegram_username: '@ivan_frontend',
  role: 'JavaScript / панель / UI',
  team: 'Командус',
  timezone: 'Europe/Moscow',
  xp: 420,
  level: 'Драйвер команды',
  skills: ['React', 'Vite', 'Tailwind', 'UX панели', 'API Integration'],
};

export const mockDigest: UserDigest = {
  user_id: 'user_ivan',
  date: '2026-06-03',
  tasks_today: mockTasks.filter((task) => task.assignee === 'Иван'),
  overdue_tasks: [],
  upcoming_deadlines: mockTasks.filter((task) => task.status !== 'done').slice(0, 3),
};

export const mockNotes: Note[] = [
  {
    id: 'note_1',
    title: 'Фокус frontend',
    content: 'Не делать backend-логику во фронте. Только UI, API-запросы и демо-состояния.',
    source: 'manual',
  },
  {
    id: 'note_2',
    title: 'Решение со встречи',
    content: 'Итоги встречи показывают решения, действия после встречи, риски и открытые вопросы.',
    source: 'meeting',
  },
];

export const mockAchievements: Achievement[] = [
  {
    id: 'ach_1',
    code: 'kanban_cleaner',
    title: 'Чистый канбан',
    description: 'Закрыл все задачи demo-polish перед защитой.',
    icon: 'sparkles',
    unlocked_at: '2026-06-03T19:30:00+03:00',
  },
  {
    id: 'ach_2',
    code: 'ai_buddy',
    title: 'AI-помощник',
    description: 'Подтвердил 10 корректных AI-предложений.',
    icon: 'bot',
  },
];

export const mockRecommendations: Recommendation[] = [
  {
    id: 'rec_1',
    title: 'UX панели patterns',
    description: 'Усилить навыки по построению операционных dashboard и пустых состояний.',
    recommendation_type: 'skill',
    source: 'история задач',
  },
  {
    id: 'rec_2',
    title: 'Продвинутый React Query',
    description: 'Повторить инвалидацию, оптимистичные обновления и состояния ошибок для API-интеграций.',
    recommendation_type: 'practice',
    source: 'анализ профиля',
  },
];
