import { parseOpportunityMarkdown, renderInline } from "@/lib/opportunity-prose";
import { cn } from "@/lib/utils";

export function OpportunityDescription({ text }: { text: string }) {
  const blocks = parseOpportunityMarkdown(text);
  if (!blocks.length) return null;
  return (
    <div className="max-w-3xl text-[15px] leading-[1.75] text-muted-foreground sm:text-base">
      {blocks.map((block, index) => {
        const key = `${block.type}-${index}`;
        if (block.type === "heading") {
          const Tag = block.level === 2 ? "h3" : "h4";
          return (
            <Tag
              key={key}
              className={cn(
                "font-heading font-semibold text-brand-navy dark:text-foreground",
                block.level === 2 ? "mt-10 mb-3 text-lg" : "mt-8 mb-3 text-base",
                index === 0 && "mt-0",
              )}
            >
              {block.text}
            </Tag>
          );
        }
        if (block.type === "list") {
          const ListTag = block.ordered ? "ol" : "ul";
          return (
            <ListTag
              key={key}
              className={cn(
                "my-4 space-y-2.5 pl-5",
                block.ordered ? "list-decimal" : "list-disc",
              )}
            >
              {block.items.map((item, itemIndex) => (
                <li key={`${itemIndex}-${item.slice(0, 48)}`} className="pl-1">
                  <Inline text={item} />
                </li>
              ))}
            </ListTag>
          );
        }
        return (
          <p key={key} className="mb-4 last:mb-0">
            <Inline text={block.text} />
          </p>
        );
      })}
    </div>
  );
}

function Inline({ text }: { text: string }) {
  return (
    <>
      {renderInline(text).map((part, index) => (
        <span key={`${part.text}-${index}`}>{part.text}</span>
      ))}
    </>
  );
}
