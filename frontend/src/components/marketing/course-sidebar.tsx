"use client";

import Image from "next/image";
import Link from "next/link";
import { ArrowUpRight, BookOpen, Clock3 } from "lucide-react";

const courses = [
  {
    title: "SQL & Excel for Blockchain Data Analytics",
    description: "Six weeks of SQL, Excel, APIs and AI-assisted onchain research.",
    duration: "6 weeks",
    price: "$50",
    href: "/programs/cohort-9-sql-blockchain-data-analytics",
    image: "/SQL and Excel for Blockchain Analytics.png",
    label: "Registration open",
  },
  {
    title: "Blockchain Data Engineering",
    description: "Build production-minded blockchain data pipelines and infrastructure.",
    duration: "10 weeks",
    price: "$200",
    href: "/programs/blockchain-data-engineering",
    image: "/blockchain-data-engineering.png",
    label: "Join the waitlist",
  },
];

export function CourseSidebar() {
  return (
    <aside aria-label="Live Analytic Sages courses" className="space-y-4">
      <div className="flex items-center gap-2">
        <BookOpen className="size-4 text-brand-orange" />
        <h2 className="font-heading text-sm font-bold uppercase tracking-[0.14em]">Learn with us</h2>
      </div>
      {courses.map((course) => (
        <article key={course.href} className="overflow-hidden rounded-xl border border-border/70 bg-card shadow-sm">
          <Link href={course.href} className="group block">
            <div className="relative aspect-[16/9] overflow-hidden bg-brand-navy">
              <Image src={course.image} alt={course.title} fill sizes="(min-width: 1024px) 300px, 100vw" className="object-cover transition-transform duration-300 group-hover:scale-[1.03]" />
            </div>
            <div className="space-y-3 p-4">
              <span className="inline-flex rounded-full bg-brand-orange/10 px-2.5 py-1 text-[11px] font-semibold text-brand-orange">{course.label}</span>
              <h3 className="font-heading text-base font-bold leading-snug group-hover:text-brand-orange">{course.title}</h3>
              <p className="text-sm leading-5 text-muted-foreground">{course.description}</p>
              <div className="flex items-center justify-between gap-3 border-t pt-3 text-sm">
                <span className="inline-flex items-center gap-1.5 text-muted-foreground"><Clock3 className="size-3.5" />{course.duration}</span>
                <span className="font-semibold">{course.price}</span>
              </div>
              <span className="inline-flex items-center gap-1 text-sm font-semibold text-brand-orange">Explore programme <ArrowUpRight className="size-4" /></span>
            </div>
          </Link>
        </article>
      ))}
      <p className="text-xs leading-5 text-muted-foreground">Project-based learning for blockchain data, analytics and Web3 engineering.</p>
    </aside>
  );
}
