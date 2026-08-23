"use client";
import { PageHeader } from "@/components/PageHeader";
import { IconCheck } from "@/components/icons";

function Kbd({ children }: { children: React.ReactNode }) {
  return (
    <kbd className="inline-block rounded-md border border-line border-b-2 bg-black/40 px-1.5 py-0.5 text-[11px] font-mono font-medium text-slate-200 whitespace-nowrap">
      {children}
    </kbd>
  );
}

function Ui({ children }: { children: React.ReactNode }) {
  return <span className="rounded-md bg-brand-500/15 px-1.5 py-0.5 text-[12px] font-medium text-brand-200 whitespace-nowrap">{children}</span>;
}

function Steps({ items }: { items: React.ReactNode[] }) {
  return (
    <ol className="space-y-3">
      {items.map((it, i) => (
        <li key={i} className="flex gap-3">
          <span className="mt-0.5 grid h-5 w-5 flex-none place-items-center rounded-md bg-brand-500/20 font-mono text-[11px] font-semibold text-brand-200">{i + 1}</span>
          <div className="text-sm text-slate-300 leading-snug">{it}</div>
        </li>
      ))}
    </ol>
  );
}

function BrowserCard({ name, sub, accent, children }: { name: string; sub: string; accent: string; children: React.ReactNode }) {
  return (
    <div className="card flex flex-col">
      <div className="mb-4 flex items-center gap-3 border-b border-line pb-3">
        <span className="grid h-8 w-8 flex-none place-items-center rounded-lg text-sm font-bold" style={{ background: `${accent}22`, color: accent }}>
          {name[0]}
        </span>
        <div className="leading-tight">
          <div className="font-semibold">{name}</div>
          <div className="font-mono text-[11px] text-slate-500">{sub}</div>
        </div>
      </div>
      {children}
    </div>
  );
}

export default function HarGuidePage() {
  return (
    <>
      <PageHeader title="Как снять HAR-файл" showRefresh={false} />

      <p className="mb-6 max-w-2xl text-sm text-slate-400">
        HAR — запись всех сетевых запросов страницы. Снимается один раз во время реального вывода
        средств через lib.iwlive.club, потом загружается в CRM в форме агентства. Ниже — по шагам для
        трёх браузеров.
      </p>

      {/* общее правило */}
      <div className="card mb-6">
        <div className="mb-4 flex items-center gap-2">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-rose-500" />
          <h2 className="font-semibold">Сначала — общее для всех браузеров</h2>
        </div>
        <div className="grid gap-4 sm:grid-cols-3">
          {[
            ["Открой панель разработчика до начала вывода", "Держи её открытой всё время — запись должна идти, пока делаешь вывод."],
            ["Включи «сохранять журнал»", "Preserve log / Persist logs — чтобы записи не стёрлись при переходах."],
            ["Сделай вывод целиком, потом экспортируй HAR", "Внутри будут запросы WithdrawByAgent и GetAgentWithdrawInfo — это и нужно."],
          ].map(([t, s], i) => (
            <div key={i} className="flex gap-3">
              <span className="grid h-6 w-6 flex-none place-items-center rounded-full bg-brand-500/20 font-mono text-xs font-semibold text-brand-200">{i + 1}</span>
              <div>
                <div className="text-sm font-medium text-slate-200">{t}</div>
                <div className="mt-0.5 text-xs text-slate-500">{s}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* три браузера */}
      <div className="grid gap-5 lg:grid-cols-3">
        <BrowserCard name="Chrome" sub="Edge · Brave — так же" accent="#4d90f0">
          <Steps items={[
            <>Открой DevTools: <Kbd>F12</Kbd> <span className="text-slate-500">(или <Kbd>Ctrl+Shift+I</Kbd> · Mac <Kbd>⌘+⌥+I</Kbd>)</span></>,
            <>Вкладка <Ui>Network</Ui> (Сеть)</>,
            <>Поставь галочку <Ui>Preserve log</Ui> (Сохранять журнал)</>,
            <>Слева вверху горит красный <span className="text-rose-400 font-medium">● кружок</span> — идёт запись</>,
            <>Сделай вывод полностью</>,
            <>Жми стрелку <Ui>⭳ Export HAR</Ui> вверху справа → сохрани файл</>,
          ]} />
        </BrowserCard>

        <BrowserCard name="Firefox" sub="Windows · Mac" accent="#ff9640">
          <Steps items={[
            <>Открой инструменты: <Kbd>F12</Kbd> <span className="text-slate-500">(или <Kbd>Ctrl+Shift+I</Kbd> · Mac <Kbd>⌘+⌥+I</Kbd>)</span></>,
            <>Вкладка <Ui>Сеть</Ui> (Network)</>,
            <>Включи <Ui>Сохранять журналы</Ui> (Persist Logs) — в шестерёнке ⚙</>,
            <>Сделай вывод полностью</>,
            <>Нажми шестерёнку <Ui>⚙</Ui> справа вверху панели «Сеть»</>,
            <>Выбери <Ui>Сохранить всё как HAR</Ui> (Save All As HAR)</>,
          ]} />
        </BrowserCard>

        <BrowserCard name="Safari" sub="только Mac" accent="#39c0f0">
          <Steps items={[
            <><b className="text-slate-200">Один раз</b> включи меню разработки: <Ui>Safari → Настройки → Дополнения</Ui> → «Показывать функции для веб-разработчиков»</>,
            <>Открой инспектор: <Kbd>⌘+⌥+I</Kbd></>,
            <>Вкладка <Ui>Сеть</Ui> (Network)</>,
            <>Включи <Ui>Preserve Log</Ui> — переключатель вверху панели</>,
            <>Сделай вывод полностью</>,
            <>Нажми <Ui>Экспорт</Ui> (Export) вверху справа → сохрани <span className="font-mono text-xs">.har</span></>,
          ]} />
        </BrowserCard>
      </div>

      {/* предупреждение */}
      <div className="mt-6 flex items-start gap-3 rounded-xl2 border border-danger/30 bg-danger/10 px-5 py-4">
        <svg viewBox="0 0 24 24" fill="none" className="mt-0.5 h-5 w-5 flex-none text-danger">
          <path d="M12 3 2.5 20h19L12 3Z" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" />
          <path d="M12 10v4.5M12 17.2v.1" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
        <p className="text-sm text-slate-300">
          <b className="text-danger">Файл содержит пароли и токены.</b> Отправляй HAR только в CRM или тому,
          кто настраивает вывод. Никуда не выкладывай и удали после загрузки.
        </p>
      </div>

      {/* куда грузить */}
      <div className="mt-4 flex items-start gap-3 rounded-xl2 border border-emerald-500/25 bg-emerald-500/10 px-5 py-4">
        <IconCheck className="mt-0.5 h-5 w-5 flex-none text-emerald-400" />
        <p className="text-sm text-slate-300">
          В CRM: <b className="text-emerald-300">Агентства → ✏️ → Вывод средств → «Загрузить HAR»</b>.
          Поля заполнятся сами, останется нажать «Сохранить».
        </p>
      </div>
    </>
  );
}
