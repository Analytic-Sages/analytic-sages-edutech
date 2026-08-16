"use client";

import { Flame, Trophy, Zap } from "lucide-react";

type DayActivity = {
  date: string;
  count: number;
};

// Generate 30 days of sample activity data
const generate30DayActivity = (): DayActivity[] => {
  const days: DayActivity[] = [];
  const today = new Date();

  for (let i = 29; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    const isRecent = i < 7;
    const count = isRecent ? (i % 2 === 0 ? 3 : 2) : i % 5 === 0 ? 1 : 0;
    days.push({
      date: d.toISOString().split("T")[0],
      count,
    });
  }
  return days;
};

export function LearningHeatmap() {
  const activity = generate30DayActivity();
  const streak = 7; // Current active streak
  const totalXp = 1450;
  const level = 3;

  const getColorClass = (count: number) => {
    if (count === 0) return "bg-muted/50 border-border/40";
    if (count === 1) return "bg-brand-orange/30 border-brand-orange/40";
    if (count === 2) return "bg-brand-orange/60 border-brand-orange/70";
    return "bg-brand-orange text-white border-brand-orange shadow-sm";
  };

  return (
    <div className="rounded-2xl border bg-card p-5 shadow-card">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-heading text-base font-bold">Learning Momentum</h3>
            <span className="inline-flex items-center gap-1 rounded-full bg-brand-orange/10 px-2.5 py-0.5 text-xs font-bold text-brand-orange border border-brand-orange/20">
              <Flame className="size-3.5 fill-current animate-pulse" /> {streak} Day Streak!
            </span>
          </div>
          <p className="mt-0.5 text-xs text-muted-foreground">
            30-day activity history • Keep your daily learning streak alive
          </p>
        </div>

        <div className="flex items-center gap-3 text-xs">
          <div className="flex items-center gap-1.5 rounded-lg border bg-brand-navy/5 px-2.5 py-1.5 font-medium">
            <Zap className="size-3.5 text-brand-orange" />
            <span>{totalXp} XP</span>
          </div>
          <div className="flex items-center gap-1.5 rounded-lg border bg-emerald-500/10 px-2.5 py-1.5 font-medium text-emerald-600 dark:text-emerald-400">
            <Trophy className="size-3.5" />
            <span>Level {level} Scholar</span>
          </div>
        </div>
      </div>

      {/* Grid of 30 Days */}
      <div className="mt-5">
        <div className="grid grid-cols-10 gap-1.5 sm:grid-cols-15 sm:gap-2">
          {activity.map((day) => (
            <div
              key={day.date}
              title={`${day.date}: ${day.count} lessons completed`}
              className={`group relative flex aspect-square items-center justify-center rounded-lg border text-[0.65rem] font-mono transition-all hover:scale-110 ${getColorClass(
                day.count
              )}`}
            >
              {day.count > 0 && <span className="font-bold">{day.count}</span>}
            </div>
          ))}
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between text-[0.75rem] text-muted-foreground">
        <span>30 Days Ago</span>
        <div className="flex items-center gap-1.5">
          <span>Less</span>
          <span className="size-2.5 rounded-xs bg-muted/50 border" />
          <span className="size-2.5 rounded-xs bg-brand-orange/30 border" />
          <span className="size-2.5 rounded-xs bg-brand-orange/60 border" />
          <span className="size-2.5 rounded-xs bg-brand-orange border" />
          <span>More</span>
        </div>
        <span>Today</span>
      </div>
    </div>
  );
}
