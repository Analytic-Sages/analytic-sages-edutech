"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";
import type { ArticleBlock } from "@/lib/insights";
import { ArticleChart } from "@/components/insights/article-chart";
import { cn } from "@/lib/utils";

function HeadingTag({
  level,
  children,
}: {
  level: 1 | 2 | 3 | 4;
  children: string;
}) {
  const className = "font-heading font-bold text-foreground";
  if (level === 1) return <h2 className={cn(className, "mt-10 text-3xl")}>{children}</h2>;
  if (level === 2) return <h2 className={cn(className, "mt-10 text-2xl")}>{children}</h2>;
  if (level === 3) return <h3 className={cn(className, "mt-8 text-xl")}>{children}</h3>;
  return <h4 className={cn(className, "mt-6 text-lg")}>{children}</h4>;
}

function CodeBlock({ language, code }: { language: string; code: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="my-8 overflow-hidden rounded-xl border bg-brand-navy text-white">
      <div className="flex items-center justify-between border-b border-white/10 px-4 py-2 text-xs uppercase tracking-wide text-white/70">
        <span>{language}</span>
        <button type="button" onClick={() => void copy()} className="inline-flex items-center gap-1 hover:text-white">
          {copied ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre className="overflow-x-auto p-4 text-sm leading-relaxed">
        <code>{code}</code>
      </pre>
    </div>
  );
}

export function ArticleBody({ blocks }: { blocks: ArticleBlock[] }) {
  return (
    <div className="max-w-none space-y-6">
      {blocks.map((block, index) => {
        const key = `${block.type}-${index}`;
        if (block.type === "paragraph") {
          return (
            <p key={key} className="text-lg leading-relaxed text-muted-foreground">
              {block.text}
            </p>
          );
        }
        if (block.type === "heading") {
          return <HeadingTag key={key} level={block.level}>{block.text}</HeadingTag>;
        }
        if (block.type === "list") {
          const ListTag = block.ordered ? "ol" : "ul";
          return (
            <ListTag
              key={key}
              className={cn(
                "space-y-2 pl-6 text-lg text-muted-foreground",
                block.ordered ? "list-decimal" : "list-disc"
              )}
            >
              {block.items.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ListTag>
          );
        }
        if (block.type === "quote") {
          return (
            <blockquote key={key} className="border-l-4 border-brand-orange pl-4 text-lg italic text-foreground">
              {block.text}
            </blockquote>
          );
        }
        if (block.type === "divider") {
          return <hr key={key} className="border-border" />;
        }
        if (block.type === "code") {
          return <CodeBlock key={key} language={block.language} code={block.code} />;
        }
        if (block.type === "image") {
          return (
            <figure key={key} className="my-10">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={block.src}
                alt={block.alt}
                className="mx-auto h-auto max-w-full"
                loading="lazy"
              />
              {block.caption || block.credit ? (
                <figcaption className="mt-3 text-center text-sm text-muted-foreground">
                  {block.caption}
                  {block.caption && block.credit ? " · " : null}
                  {block.credit}
                </figcaption>
              ) : null}
            </figure>
          );
        }
        if (block.type === "youtube") {
          return (
            <div key={key} className="my-10 aspect-video overflow-hidden rounded-xl bg-black">
              <iframe
                title="YouTube video"
                src={`https://www.youtube-nocookie.com/embed/${block.videoId}`}
                className="h-full w-full"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
                referrerPolicy="strict-origin-when-cross-origin"
              />
            </div>
          );
        }
        if (block.type === "table") {
          return (
            <div key={key} className="my-8 overflow-x-auto">
              <table className="min-w-full border-collapse text-sm">
                <thead>
                  <tr>
                    {block.headers.map((header) => (
                      <th key={header} className="border-b px-3 py-2 text-left font-semibold">
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {block.rows.map((row, rowIndex) => (
                    <tr key={rowIndex}>
                      {row.map((cell, cellIndex) => (
                        <td key={`${rowIndex}-${cellIndex}`} className="border-b px-3 py-2 text-muted-foreground">
                          {cell}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        }
        if (block.type === "chart") {
          return (
            <ArticleChart
              key={key}
              chartType={block.chartType}
              title={block.title}
              labels={block.labels}
              values={block.values}
              source={block.source}
              caption={block.caption}
            />
          );
        }
        return (
          <aside key={key} className="rounded-xl border bg-brand-surface p-6">
            <p className="text-xs font-semibold uppercase tracking-wide text-brand-orange">Key takeaways</p>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-foreground">
              {block.items.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </aside>
        );
      })}
    </div>
  );
}
