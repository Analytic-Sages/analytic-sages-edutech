export type OpportunityProseBlock =
  | { type: "heading"; level: 2 | 3 | 4; text: string }
  | { type: "paragraph"; text: string }
  | { type: "list"; ordered: boolean; items: string[] };

const HEADING_RE = /^(#{1,4})\s+(.+)$/;
const UL_RE = /^[-*•–]\s+(.+)$/;
const OL_RE = /^(\d+)[.)]\s+(.+)$/;

/** Strip markdown emphasis and fancy dashes so opportunity copy reads clean. */
export function sanitizeOpportunityProse(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, "$1")
    .replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, "$1")
    .replace(/\*\*/g, "")
    .replace(/__/g, "")
    .replace(/\s*[\u2014\u2013]\s*/g, " - ")
    .replace(/[ \t]+/g, " ");
}

export function parseOpportunityMarkdown(source: string): OpportunityProseBlock[] {
  const lines = sanitizeOpportunityProse(source.replace(/\r\n/g, "\n")).split("\n");
  const blocks: OpportunityProseBlock[] = [];
  let paragraph: string[] = [];
  let list: { ordered: boolean; items: string[] } | null = null;

  function flushParagraph() {
    const text = paragraph.join(" ").trim();
    paragraph = [];
    if (text) blocks.push({ type: "paragraph", text: sanitizeOpportunityProse(text).trim() });
  }

  function flushList() {
    if (list?.items.length) blocks.push({ type: "list", ordered: list.ordered, items: list.items });
    list = null;
  }

  for (const raw of lines) {
    const line = raw.trim();
    if (!line) {
      flushParagraph();
      flushList();
      continue;
    }
    const heading = line.match(HEADING_RE);
    if (heading) {
      flushParagraph();
      flushList();
      const hashes = heading[1].length;
      const level = hashes <= 2 ? 2 : hashes === 3 ? 3 : 4;
      blocks.push({
        type: "heading",
        level,
        text: sanitizeOpportunityProse(heading[2]).trim(),
      });
      continue;
    }
    const ul = line.match(UL_RE);
    if (ul) {
      flushParagraph();
      if (!list || list.ordered) {
        flushList();
        list = { ordered: false, items: [] };
      }
      list.items.push(sanitizeOpportunityProse(ul[1]).trim());
      continue;
    }
    const ol = line.match(OL_RE);
    if (ol) {
      flushParagraph();
      if (!list || !list.ordered) {
        flushList();
        list = { ordered: true, items: [] };
      }
      list.items.push(sanitizeOpportunityProse(ol[2]).trim());
      continue;
    }
    flushList();
    paragraph.push(line);
  }
  flushParagraph();
  flushList();
  return blocks;
}

export function renderInline(text: string): { text: string }[] {
  const cleaned = sanitizeOpportunityProse(text).trim();
  return cleaned ? [{ text: cleaned }] : [];
}
