"use client";

import { useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { ArticleBlock } from "@/lib/insights";
import { uploadInsightImage } from "@/lib/insights";

type Props = {
  blocks: ArticleBlock[];
  onChange: (blocks: ArticleBlock[]) => void;
};

const INSERTS: { label: string; block: ArticleBlock }[] = [
  { label: "Paragraph", block: { type: "paragraph", text: "" } },
  { label: "Heading", block: { type: "heading", level: 2, text: "" } },
  { label: "List", block: { type: "list", ordered: false, items: [""] } },
  { label: "Quote", block: { type: "quote", text: "" } },
  { label: "Divider", block: { type: "divider" } },
  { label: "Code", block: { type: "code", language: "sql", code: "" } },
  { label: "Image", block: { type: "image", src: "", alt: "", caption: "", credit: "" } },
  { label: "YouTube", block: { type: "youtube", videoId: "" } },
  { label: "Table", block: { type: "table", headers: ["Metric", "Value"], rows: [["", ""]] } },
  {
    label: "Chart",
    block: {
      type: "chart",
      chartType: "bar",
      title: "",
      labels: ["Jan", "Feb"],
      values: [0, 0],
      source: "",
      caption: "",
    },
  },
  { label: "Takeaways", block: { type: "takeaways", items: [""] } },
];

function replaceAt<T>(list: T[], index: number, item: T) {
  return list.map((current, i) => (i === index ? item : current));
}

export function ArticleEditor({ blocks, onChange }: Props) {
  const [uploadError, setUploadError] = useState<string | null>(null);

  function insert(index: number, block: ArticleBlock) {
    const next = [...blocks];
    next.splice(index, 0, block);
    onChange(next);
  }

  function remove(index: number) {
    if (blocks.length === 1) {
      onChange([{ type: "paragraph", text: "" }]);
      return;
    }
    onChange(blocks.filter((_, i) => i !== index));
  }

  async function onImageFile(index: number, file: File | undefined, block: Extract<ArticleBlock, { type: "image" }>) {
    if (!file) return;
    setUploadError(null);
    try {
      const uploaded = await uploadInsightImage(file);
      onChange(replaceAt(blocks, index, { ...block, src: uploaded.url }));
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Upload failed");
    }
  }

  return (
    <div className="space-y-4">
      {uploadError ? <p className="text-sm text-destructive">{uploadError}</p> : null}
      <InsertBar onInsert={(block) => insert(0, block)} />
      {blocks.map((block, index) => (
        <div key={`${block.type}-${index}`} className="rounded-xl border p-4">
          <div className="mb-3 flex items-center justify-between gap-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{block.type}</p>
            <Button type="button" size="sm" variant="ghost" onClick={() => remove(index)}>
              <Trash2 className="size-4" />
              Remove
            </Button>
          </div>
          {block.type === "paragraph" || block.type === "quote" ? (
            <Textarea
              value={block.text}
              onChange={(event) => onChange(replaceAt(blocks, index, { ...block, text: event.target.value }))}
              rows={4}
            />
          ) : null}
          {block.type === "heading" ? (
            <div className="space-y-2">
              <select
                className="h-10 rounded-lg border bg-background px-3 text-sm"
                value={block.level}
                onChange={(event) =>
                  onChange(replaceAt(blocks, index, { ...block, level: Number(event.target.value) as 1 | 2 | 3 | 4 }))
                }
              >
                <option value={1}>Heading 1</option>
                <option value={2}>Heading 2</option>
                <option value={3}>Heading 3</option>
                <option value={4}>Heading 4</option>
              </select>
              <Input
                value={block.text}
                onChange={(event) => onChange(replaceAt(blocks, index, { ...block, text: event.target.value }))}
              />
            </div>
          ) : null}
          {block.type === "list" ? (
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={block.ordered}
                  onChange={(event) => onChange(replaceAt(blocks, index, { ...block, ordered: event.target.checked }))}
                />
                Numbered list
              </label>
              {block.items.map((item, itemIndex) => (
                <Input
                  key={itemIndex}
                  value={item}
                  onChange={(event) => {
                    const items = [...block.items];
                    items[itemIndex] = event.target.value;
                    onChange(replaceAt(blocks, index, { ...block, items }));
                  }}
                />
              ))}
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => onChange(replaceAt(blocks, index, { ...block, items: [...block.items, ""] }))}
              >
                Add item
              </Button>
            </div>
          ) : null}
          {block.type === "code" ? (
            <div className="space-y-2">
              <select
                className="h-10 rounded-lg border bg-background px-3 text-sm"
                value={block.language}
                onChange={(event) => onChange(replaceAt(blocks, index, { ...block, language: event.target.value }))}
              >
                {["sql", "python", "javascript", "typescript", "rust", "solidity", "bash", "json", "text"].map(
                  (language) => (
                    <option key={language} value={language}>
                      {language}
                    </option>
                  )
                )}
              </select>
              <Textarea
                className="font-mono"
                rows={8}
                value={block.code}
                onChange={(event) => onChange(replaceAt(blocks, index, { ...block, code: event.target.value }))}
              />
            </div>
          ) : null}
          {block.type === "image" ? (
            <div className="space-y-2">
              <Label>Upload</Label>
              <Input
                type="file"
                accept="image/jpeg,image/png,image/webp,image/gif"
                onChange={(event) => void onImageFile(index, event.target.files?.[0], block)}
              />
              <Input
                placeholder="Image URL"
                value={block.src}
                onChange={(event) => onChange(replaceAt(blocks, index, { ...block, src: event.target.value }))}
              />
              <Input
                placeholder="Alt text (required)"
                value={block.alt}
                onChange={(event) => onChange(replaceAt(blocks, index, { ...block, alt: event.target.value }))}
              />
              <Input
                placeholder="Caption"
                value={block.caption || ""}
                onChange={(event) => onChange(replaceAt(blocks, index, { ...block, caption: event.target.value }))}
              />
              <Input
                placeholder="Credit / source"
                value={block.credit || ""}
                onChange={(event) => onChange(replaceAt(blocks, index, { ...block, credit: event.target.value }))}
              />
            </div>
          ) : null}
          {block.type === "youtube" ? (
            <Input
              placeholder="YouTube URL or video ID"
              value={block.videoId}
              onChange={(event) => onChange(replaceAt(blocks, index, { ...block, videoId: event.target.value }))}
            />
          ) : null}
          {block.type === "table" ? (
            <div className="space-y-2 overflow-x-auto">
              <div className="flex gap-2">
                {block.headers.map((header, headerIndex) => (
                  <Input
                    key={headerIndex}
                    value={header}
                    onChange={(event) => {
                      const headers = [...block.headers];
                      headers[headerIndex] = event.target.value;
                      onChange(replaceAt(blocks, index, { ...block, headers }));
                    }}
                  />
                ))}
              </div>
              {block.rows.map((row, rowIndex) => (
                <div key={rowIndex} className="flex gap-2">
                  {row.map((cell, cellIndex) => (
                    <Input
                      key={cellIndex}
                      value={cell}
                      onChange={(event) => {
                        const rows = block.rows.map((current, i) =>
                          i === rowIndex
                            ? current.map((value, j) => (j === cellIndex ? event.target.value : value))
                            : current
                        );
                        onChange(replaceAt(blocks, index, { ...block, rows }));
                      }}
                    />
                  ))}
                </div>
              ))}
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() =>
                  onChange(
                    replaceAt(blocks, index, {
                      ...block,
                      rows: [...block.rows, block.headers.map(() => "")],
                    })
                  )
                }
              >
                Add row
              </Button>
            </div>
          ) : null}
          {block.type === "chart" ? (
            <div className="space-y-2">
              <select
                className="h-10 rounded-lg border bg-background px-3 text-sm"
                value={block.chartType}
                onChange={(event) =>
                  onChange(
                    replaceAt(blocks, index, {
                      ...block,
                      chartType: event.target.value as "line" | "bar" | "pie" | "scatter",
                    })
                  )
                }
              >
                <option value="bar">Bar</option>
                <option value="line">Line</option>
                <option value="pie">Pie</option>
                <option value="scatter">Scatter</option>
              </select>
              <Input
                placeholder="Title"
                value={block.title || ""}
                onChange={(event) => onChange(replaceAt(blocks, index, { ...block, title: event.target.value }))}
              />
              <Input
                placeholder="Labels, comma separated"
                value={block.labels.join(", ")}
                onChange={(event) =>
                  onChange(
                    replaceAt(blocks, index, {
                      ...block,
                      labels: event.target.value.split(",").map((item) => item.trim()).filter(Boolean),
                    })
                  )
                }
              />
              <Input
                placeholder="Values, comma separated"
                value={block.values.join(", ")}
                onChange={(event) =>
                  onChange(
                    replaceAt(blocks, index, {
                      ...block,
                      values: event.target.value
                        .split(",")
                        .map((item) => Number(item.trim()))
                        .filter((item) => !Number.isNaN(item)),
                    })
                  )
                }
              />
              <Input
                placeholder="Source"
                value={block.source || ""}
                onChange={(event) => onChange(replaceAt(blocks, index, { ...block, source: event.target.value }))}
              />
              <Input
                placeholder="Caption"
                value={block.caption || ""}
                onChange={(event) => onChange(replaceAt(blocks, index, { ...block, caption: event.target.value }))}
              />
            </div>
          ) : null}
          {block.type === "takeaways" ? (
            <div className="space-y-2">
              {block.items.map((item, itemIndex) => (
                <Input
                  key={itemIndex}
                  value={item}
                  onChange={(event) => {
                    const items = [...block.items];
                    items[itemIndex] = event.target.value;
                    onChange(replaceAt(blocks, index, { ...block, items }));
                  }}
                />
              ))}
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => onChange(replaceAt(blocks, index, { ...block, items: [...block.items, ""] }))}
              >
                Add takeaway
              </Button>
            </div>
          ) : null}
          <InsertBar onInsert={(next) => insert(index + 1, next)} />
        </div>
      ))}
    </div>
  );
}

function InsertBar({ onInsert }: { onInsert: (block: ArticleBlock) => void }) {
  return (
    <div className="flex flex-wrap gap-2 py-2">
      {INSERTS.map((item) => (
        <Button key={item.label} type="button" size="sm" variant="outline" onClick={() => onInsert(item.block)}>
          <Plus className="size-3.5" />
          {item.label}
        </Button>
      ))}
    </div>
  );
}
