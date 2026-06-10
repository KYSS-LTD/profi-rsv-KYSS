import {
  CalendarDays,
  Check,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock,
  FileText,
  ListChecks,
  Loader2,
  MoreVertical,
  Pencil,
  Sparkles,
  SpellCheck,
  TrendingUp,
  Users,
  X,
} from 'lucide-react';
import { ReactNode, useMemo, useState } from 'react';
import { createPortal } from 'react-dom';
import { Badge } from '../../shared/ui/Badge';
import { Button } from '../../shared/ui/Button';
import { Card } from '../../shared/ui/Card';
import { cn } from '../../shared/lib/cn';
import { Call, CallTask, calls } from './mockCalls';

const WEEKDAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
const SPEAKER_TONES = [
  'bg-sky-100 text-sky-700',
  'bg-emerald-100 text-emerald-700',
  'bg-amber-100 text-amber-700',
  'bg-violet-100 text-violet-700',
  'bg-rose-100 text-rose-700',
];

const pad = (n: number) => String(n).padStart(2, '0');
const dateKey = (year: number, month: number, day: number) => `${year}-${pad(month + 1)}-${pad(day)}`;

function monthMatrix(year: number, month: number): Array<number | null> {
  const startWeekday = (new Date(year, month, 1).getDay() + 6) % 7; // Пн = 0
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const cells: Array<number | null> = Array.from({ length: startWeekday }, () => null);
  for (let d = 1; d <= daysInMonth; d += 1) cells.push(d);
  while (cells.length % 7 !== 0) cells.push(null);
  return cells;
}

function formatLongDate(iso: string) {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' });
}

const DEFAULT_DAY = calls[0].date; // 2026-04-13 — самая насыщенная встреча

type ModalTab = 'transcript' | 'tasks' | 'edit';

export function CallsView() {
  const initial = DEFAULT_DAY.split('-').map(Number);
  const [year, setYear] = useState(initial[0]);
  const [month, setMonth] = useState(initial[1] - 1); // 0-based
  const [selectedDay, setSelectedDay] = useState(DEFAULT_DAY);
  const [openMenu, setOpenMenu] = useState<string | null>(null);
  const [modal, setModal] = useState<{ call: Call; tab: ModalTab } | null>(null);
  const [edits, setEdits] = useState<Record<string, string>>({});

  const callsByDate = useMemo(() => {
    const map = new Map<string, Call[]>();
    for (const call of calls) {
      const list = map.get(call.date) ?? [];
      list.push(call);
      map.set(call.date, list);
    }
    return map;
  }, []);

  const cells = useMemo(() => monthMatrix(year, month), [year, month]);
  const dayCalls = callsByDate.get(selectedDay) ?? [];
  const monthTitle = new Date(year, month, 1).toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' });

  const headline = calls.find((c) => c.id === 'm1') ?? calls[0];
  const tasksTotal = calls.reduce((sum, c) => sum + c.tasks.length, 0);

  const shiftMonth = (delta: number) => {
    const next = new Date(year, month + delta, 1);
    setYear(next.getFullYear());
    setMonth(next.getMonth());
  };

  return (
    <div className="space-y-6">
      {/* Метрики качества транскрипции (оценка AI) */}
      <section className="grid gap-4 md:grid-cols-3">
        <MetricTile
          icon={<Sparkles className="h-5 w-5" />}
          label="Точность транскрипции"
          value={`${headline.accuracy}%`}
          note="Точность в этот раз. Модель стала точнее после дообучения."
          trend={`+${headline.accuracyDelta} п.п. после дообучения`}
        />
        <MetricTile
          icon={<SpellCheck className="h-5 w-5" />}
          label="Орфография"
          value={`${headline.spelling}%`}
          note="Корректность написания терминов, имён и аббревиатур."
        />
        <MetricTile
          icon={<ListChecks className="h-5 w-5" />}
          label="Задач выделено AI"
          value={String(tasksTotal)}
          note={`Из ${calls.filter((c) => c.status === 'processed').length} обработанных созвонов.`}
        />
      </section>

      <div className="grid gap-6 lg:grid-cols-[340px_minmax(0,1fr)]">
        {/* Календарь */}
        <Card className="h-fit p-4">
          <div className="mb-4 flex items-center justify-between">
            <button
              type="button"
              onClick={() => shiftMonth(-1)}
              className="focus-ring rounded-lg p-1.5 text-stone-500 transition hover:bg-stone-100 hover:text-stone-900"
              aria-label="Предыдущий месяц"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <p className="text-sm font-semibold capitalize text-stone-900">{monthTitle}</p>
            <button
              type="button"
              onClick={() => shiftMonth(1)}
              className="focus-ring rounded-lg p-1.5 text-stone-500 transition hover:bg-stone-100 hover:text-stone-900"
              aria-label="Следующий месяц"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>

          <div className="mb-2 grid grid-cols-7 gap-1 text-center text-xs font-medium text-stone-400">
            {WEEKDAYS.map((w) => (
              <div key={w} className="py-1">{w}</div>
            ))}
          </div>

          <div className="grid grid-cols-7 gap-1">
            {cells.map((day, index) => {
              if (day === null) return <div key={`empty-${index}`} />;
              const key = dateKey(year, month, day);
              const count = (callsByDate.get(key) ?? []).length;
              const isSelected = key === selectedDay;
              const hasCalls = count > 0;
              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => setSelectedDay(key)}
                  className={cn(
                    'focus-ring relative flex aspect-square flex-col items-center justify-center rounded-xl text-sm transition',
                    isSelected
                      ? 'bg-stone-900 font-semibold text-white'
                      : hasCalls
                        ? 'bg-stone-50 font-medium text-stone-900 hover:bg-stone-100'
                        : 'text-stone-400 hover:bg-stone-50',
                  )}
                >
                  {day}
                  {hasCalls && (
                    <span
                      className={cn(
                        'absolute bottom-1.5 h-1.5 w-1.5 rounded-full',
                        isSelected ? 'bg-white' : 'bg-emerald-500',
                      )}
                    />
                  )}
                </button>
              );
            })}
          </div>

          <div className="mt-4 flex items-center gap-2 border-t border-stone-100 pt-3 text-xs text-stone-500">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            Дни с созвонами
          </div>
        </Card>

        {/* Список созвонов выбранного дня */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm text-stone-500">
            <CalendarDays className="h-4 w-4" />
            <span className="capitalize">{formatLongDate(selectedDay)}</span>
            <Badge tone="neutral">{dayCalls.length}</Badge>
          </div>

          {dayCalls.length === 0 ? (
            <Card className="text-center">
              <p className="font-semibold text-stone-900">В этот день созвонов нет</p>
              <p className="mt-2 text-sm text-stone-500">Выберите день, отмеченный зелёной точкой.</p>
            </Card>
          ) : (
            dayCalls.map((call) => (
              <CallCard
                key={call.id}
                call={call}
                menuOpen={openMenu === call.id}
                onToggleMenu={() => setOpenMenu((prev) => (prev === call.id ? null : call.id))}
                onCloseMenu={() => setOpenMenu(null)}
                onOpen={(tab) => {
                  setOpenMenu(null);
                  setModal({ call, tab });
                }}
              />
            ))
          )}
        </div>
      </div>

      {modal && (
        <CallModal
          call={modal.call}
          tab={modal.tab}
          onTab={(tab) => setModal({ call: modal.call, tab })}
          onClose={() => setModal(null)}
          editedValue={edits[modal.call.id]}
          onSaveEdit={(value) => setEdits((prev) => ({ ...prev, [modal.call.id]: value }))}
        />
      )}
    </div>
  );
}

function MetricTile({
  icon,
  label,
  value,
  note,
  trend,
}: {
  icon: ReactNode;
  label: string;
  value: string;
  note: string;
  trend?: string;
}) {
  return (
    <Card>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm text-stone-500">{label}</p>
          <p className="mt-2 text-4xl font-semibold tracking-tight text-stone-950">{value}</p>
        </div>
        <div className="shrink-0 rounded-xl bg-stone-100 p-3 text-stone-700">{icon}</div>
      </div>
      {trend && (
        <p className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
          <TrendingUp className="h-3.5 w-3.5" />
          {trend}
        </p>
      )}
      <p className="mt-3 text-sm leading-6 text-stone-500">{note}</p>
    </Card>
  );
}

function CallCard({
  call,
  menuOpen,
  onToggleMenu,
  onCloseMenu,
  onOpen,
}: {
  call: Call;
  menuOpen: boolean;
  onToggleMenu: () => void;
  onCloseMenu: () => void;
  onOpen: (tab: ModalTab) => void;
}) {
  const processing = call.status === 'processing';
  return (
    <Card className="relative">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2 text-sm text-stone-500">
            <span className="inline-flex items-center gap-1.5 font-medium text-stone-700">
              <Clock className="h-3.5 w-3.5" />
              {call.time}
            </span>
            <span className="text-stone-300">·</span>
            <span>{call.durationMin} мин</span>
            {processing ? (
              <Badge tone="amber" className="gap-1.5">
                <Loader2 className="h-3 w-3 animate-spin" />
                AI распознаёт
              </Badge>
            ) : (
              <>
                <Badge tone="green" className="gap-1.5">
                  <Sparkles className="h-3 w-3" />
                  Точность {call.accuracy}%
                </Badge>
                <Badge tone="blue">Орфография {call.spelling}%</Badge>
              </>
            )}
          </div>
          <h3 className="mt-2 text-lg font-semibold text-stone-950">{call.title}</h3>
          <p className="mt-2 flex items-center gap-1.5 text-sm text-stone-500">
            <Users className="h-3.5 w-3.5 shrink-0" />
            <span className="truncate">{call.participants.join(', ')}</span>
          </p>
        </div>

        {!processing && (
          <div className="relative shrink-0">
            <button
              type="button"
              onClick={onToggleMenu}
              className="focus-ring rounded-lg p-2 text-stone-500 transition hover:bg-stone-100 hover:text-stone-900"
              aria-label="Действия по созвону"
            >
              <MoreVertical className="h-5 w-5" />
            </button>
            {menuOpen && (
              <>
                <div className="fixed inset-0 z-20" onClick={onCloseMenu} />
                <div className="absolute right-0 z-30 mt-1 w-64 overflow-hidden rounded-2xl border border-stone-200 bg-white p-1.5 shadow-soft">
                  <MenuItem icon={<FileText className="h-4 w-4" />} onClick={() => onOpen('transcript')}>
                    Транскрипция встречи
                  </MenuItem>
                  <MenuItem icon={<ListChecks className="h-4 w-4" />} onClick={() => onOpen('tasks')}>
                    <span className="flex w-full items-center justify-between gap-2">
                      Выделенные задачи
                      <Badge tone="neutral">{call.tasks.length}</Badge>
                    </span>
                  </MenuItem>
                  <MenuItem icon={<Pencil className="h-4 w-4" />} onClick={() => onOpen('edit')}>
                    Отредактировать транскрипцию
                  </MenuItem>
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {processing ? (
        <p className="mt-4 rounded-2xl bg-amber-50 px-4 py-3 text-sm text-amber-700">
          Идёт распознавание речи и выделение задач. Транскрипция появится здесь автоматически.
        </p>
      ) : (
        <div className="mt-4 flex flex-wrap gap-2">
          <Button variant="secondary" onClick={() => onOpen('transcript')}>
            <FileText className="h-4 w-4" />
            Транскрипция
          </Button>
          <Button variant="secondary" onClick={() => onOpen('tasks')}>
            <ListChecks className="h-4 w-4" />
            Задачи
            <Badge tone="neutral">{call.tasks.length}</Badge>
          </Button>
          <Button variant="ghost" onClick={() => onOpen('edit')}>
            <Pencil className="h-4 w-4" />
            Редактировать
          </Button>
        </div>
      )}
    </Card>
  );
}

function MenuItem({ icon, children, onClick }: { icon: ReactNode; children: ReactNode; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="focus-ring flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm text-stone-700 transition hover:bg-stone-50"
    >
      <span className="text-stone-400">{icon}</span>
      <span className="flex-1">{children}</span>
    </button>
  );
}

const TABS: Array<{ key: ModalTab; label: string; icon: ReactNode }> = [
  { key: 'transcript', label: 'Транскрипция', icon: <FileText className="h-4 w-4" /> },
  { key: 'tasks', label: 'Задачи', icon: <ListChecks className="h-4 w-4" /> },
  { key: 'edit', label: 'Редактировать', icon: <Pencil className="h-4 w-4" /> },
];

function CallModal({
  call,
  tab,
  onTab,
  onClose,
  editedValue,
  onSaveEdit,
}: {
  call: Call;
  tab: ModalTab;
  onTab: (tab: ModalTab) => void;
  onClose: () => void;
  editedValue?: string;
  onSaveEdit: (value: string) => void;
}) {
  const originalText = useMemo(
    () => call.transcript.map((line) => `${line.speaker}: ${line.text}`).join('\n'),
    [call],
  );
  const [draft, setDraft] = useState(editedValue ?? originalText);
  const [saved, setSaved] = useState(false);
  const speakers = useMemo(() => Array.from(new Set(call.transcript.map((l) => l.speaker))), [call]);
  const speakerTone = (speaker: string) => SPEAKER_TONES[speakers.indexOf(speaker) % SPEAKER_TONES.length];

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-stone-950/40 p-0 sm:items-center sm:p-6" onClick={onClose}>
      <div
        className="flex max-h-[92vh] w-full max-w-3xl flex-col overflow-hidden rounded-t-3xl bg-white shadow-2xl sm:rounded-3xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Шапка */}
        <div className="flex items-start justify-between gap-4 border-b border-stone-100 p-5">
          <div className="min-w-0">
            <p className="text-xs uppercase tracking-[0.16em] text-stone-400">{formatLongDate(call.date)} · {call.time}</p>
            <h2 className="mt-1 text-xl font-semibold text-stone-950">{call.title}</h2>
            <div className="mt-2 flex flex-wrap gap-2">
              <Badge tone="green" className="gap-1.5"><Sparkles className="h-3 w-3" />Точность {call.accuracy}%</Badge>
              <Badge tone="blue">Орфография {call.spelling}%</Badge>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="focus-ring shrink-0 rounded-lg p-2 text-stone-400 transition hover:bg-stone-100 hover:text-stone-900"
            aria-label="Закрыть"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Вкладки */}
        <div className="flex gap-1 border-b border-stone-100 px-3">
          {TABS.map((t) => (
            <button
              key={t.key}
              type="button"
              onClick={() => onTab(t.key)}
              className={cn(
                'focus-ring -mb-px flex items-center gap-2 border-b-2 px-3 py-3 text-sm font-medium transition',
                tab === t.key
                  ? 'border-stone-900 text-stone-950'
                  : 'border-transparent text-stone-400 hover:text-stone-700',
              )}
            >
              {t.icon}
              {t.label}
              {t.key === 'tasks' && <Badge tone="neutral">{call.tasks.length}</Badge>}
            </button>
          ))}
        </div>

        {/* Контент */}
        <div className="flex-1 overflow-y-auto p-5">
          {tab === 'transcript' && (
            <div className="space-y-3">
              {call.transcript.map((line, index) => (
                <div key={index} className="flex gap-3">
                  <span className={cn('mt-0.5 h-fit shrink-0 rounded-full px-2.5 py-1 text-xs font-medium', speakerTone(line.speaker))}>
                    {line.speaker}
                  </span>
                  <p className="text-sm leading-6 text-stone-800">{line.text}</p>
                </div>
              ))}
            </div>
          )}

          {tab === 'tasks' && <TasksTab tasks={call.tasks} />}

          {tab === 'edit' && (
            <div className="space-y-3">
              <p className="rounded-2xl bg-stone-50 px-4 py-3 text-sm text-stone-500">
                Ручная правка транскрипции. Формат строки — <span className="font-medium text-stone-700">Спикер: текст</span>.
                После сохранения AED заново выделит задачи (демо-режим — изменения хранятся локально).
              </p>
              <textarea
                value={draft}
                onChange={(e) => {
                  setDraft(e.target.value);
                  setSaved(false);
                }}
                rows={16}
                className="w-full rounded-2xl border border-stone-300 bg-white p-4 font-mono text-sm leading-6 text-stone-900 outline-none focus:border-stone-900"
              />
              <div className="flex items-center gap-3">
                <Button
                  onClick={() => {
                    onSaveEdit(draft);
                    setSaved(true);
                  }}
                >
                  <Check className="h-4 w-4" />
                  Сохранить транскрипцию
                </Button>
                <Button variant="ghost" onClick={() => { setDraft(editedValue ?? originalText); setSaved(false); }}>
                  Сбросить
                </Button>
                {saved && (
                  <span className="inline-flex items-center gap-1.5 text-sm font-medium text-emerald-600">
                    <CheckCircle2 className="h-4 w-4" />
                    Сохранено
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>,
    document.body,
  );
}

function TasksTab({ tasks }: { tasks: CallTask[] }) {
  if (tasks.length === 0) {
    return <p className="text-sm text-stone-500">Задачи ещё не выделены.</p>;
  }
  return (
    <div className="space-y-3">
      {tasks.map((task, index) => (
        <div key={index} className="rounded-2xl border border-stone-200 p-4">
          <div className="flex items-start justify-between gap-3">
            <h4 className="font-medium text-stone-950">{task.title}</h4>
            <Badge tone={task.status === 'done' ? 'green' : 'amber'} className="shrink-0">
              {task.status === 'done' ? 'Выполнена' : 'Новая'}
            </Badge>
          </div>
          <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm text-stone-500">
            <span className="inline-flex items-center gap-1.5"><Users className="h-3.5 w-3.5" />{task.assignee}</span>
            <span className="inline-flex items-center gap-1.5"><Clock className="h-3.5 w-3.5" />Срок: {task.due}</span>
          </div>
          <p className="mt-3 border-l-2 border-stone-200 pl-3 text-sm italic leading-6 text-stone-500">
            «{task.quote}»
          </p>
        </div>
      ))}
    </div>
  );
}
