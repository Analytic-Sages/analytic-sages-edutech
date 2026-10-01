"use client";

import { useState } from "react";
import { Plus, Trash2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { ArticleBlock } from "@/lib/insights";
import { uploadInsightImage } from "@/lib/insights";
import { RichTextField, RichTextInput } from "@/components/insights/rich-text-field";

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
  { label: "Image", block: { type: "image", src: "", alt: "", caption: "", credit: "", width: "full" } },
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

function removeAt<T>(list: T[], index: number) {
  return list.filter((_, i) => i !== index);
}

/** Splits pasted text on blank lines so large research drafts don't land in a single paragraph block. */
function splitIntoParagraphs(text: string): string[] {
  return text
    .split(/\n\s*\n+/)
    .map((chunk) => chunk.trim())
    .filter(Boolean);
}

export function ArticleEditor({ blocks, onChange }: Props) {
  const [uploadError, setUploadError] = useState<string | null>(null);

  function insert(index: number, block: ArticleBlock) {
    const next = [...blocks];
    next.splice(index, 0, block);
    // Keep the writer able to keep typing right after a non-text block (e.g. an image).
    const followUp = next[index + 1];
    if (block.type !== "paragraph" && (!followUp || followUp.type !== "paragraph")) {
      next.splice(index + 1, 0, { type: "paragraph", text: "" });
    }
    onChange(next);
  }

  function remove(index: number) {
    if (blocks.length === 1) {
      onChange([{ type: "paragraph", text: "" }]);
      return;
    }
    onChange(blocks.filter((_, i) => i !== index));
  }

  function onParagraphPaste(
    event: React.ClipboardEvent<HTMLTextAreaElement>,
    index: number,
    block: Extract<ArticleBlock, { type: "paragraph" }>
  ) {
    const pasted = event.clipboardData.getData("text");
    const parts = splitIntoParagraphs(pasted);
    if (parts.length <= 1) return;
    event.preventDefault();
    const textarea = event.currentTarget;
    const before = block.text.slice(0, textarea.selectionStart);
    const after = block.text.slice(textarea.selectionEnd);
    const trailing: ArticleBlock[] = parts.slice(1).map((text) => ({ type: "paragraph", text }));
    const last = trailing[trailing.length - 1] as Extract<ArticleBlock, { type: "paragraph" }> | undefined;
    if (last) last.text = `${last.text}${after}`;
    const next = [...blocks];
    next[index] = { ...block, text: `${before}${parts[0]}${trailing.length ? "" : after}` };
    next.splice(index + 1, 0, ...trailing);
    onChange(next);
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
            <RichTextField
              value={block.text}
              onChange={(text) => onChange(replaceAt(blocks, index, { ...block, text }))}
              rows={4}
              onPaste={
                block.type === "paragraph"
                  ? (event) => onParagraphPaste(event, index, block)
                  : undefined
              }
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
                <div key={itemIndex} className="flex items-start gap-2">
                  <div className="flex-1">
                    <RichTextInput
                      value={item}
                      onChange={(value) => {
                        const items = replaceAt(block.items, itemIndex, value);
                        onChange(replaceAt(blocks, index, { ...block, items }));
                      }}
                    />
                  </div>
                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    className="mt-7"
                    disabled={block.items.length === 1}
                    onClick={() =>
                      onChange(replaceAt(blocks, index, { ...block, items: removeAt(block.items, itemIndex) }))
                    }
                  >
                    <X className="size-4" />
                  </Button>
                </div>
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
              <div className="space-y-1">
                <Label>Size</Label>
                <select
                  className="h-10 w-full rounded-lg border bg-background px-3 text-sm"
                  value={block.width || "full"}
                  onChange={(event) =>
                    onChange(
                      replaceAt(blocks, index, {
                        ...block,
                        width: event.target.value as "small" | "medium" | "large" | "full",
                      })
                    )
                  }
                >
                  <option value="small">Small (25%)</option>
                  <option value="medium">Medium (50%)</option>
                  <option value="large">Large (75%)</option>
                  <option value="full">Full width</option>
                </select>
              </div>
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
                <div key={itemIndex} className="flex items-start gap-2">
                  <div className="flex-1">
                    <RichTextInput
                      value={item}
                      onChange={(value) => {
                        const items = replaceAt(block.items, itemIndex, value);
                        onChange(replaceAt(blocks, index, { ...block, items }));
                      }}
                    />
                  </div>
                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    className="mt-7"
                    disabled={block.items.length === 1}
                    onClick={() =>
                      onChange(replaceAt(blocks, index, { ...block, items: removeAt(block.items, itemIndex) }))
                    }
                  >
                    <X className="size-4" />
                  </Button>
                </div>
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
