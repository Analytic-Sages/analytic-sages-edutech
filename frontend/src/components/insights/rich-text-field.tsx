"use client";

import { useRef } from "react";
import { Bold, Italic } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

/** Wraps the current selection with a markdown marker, or inserts an empty pair at the caret. */
function applyMarker(el: HTMLTextAreaElement | HTMLInputElement, value: string, marker: string) {
  const start = el.selectionStart ?? value.length;
  const end = el.selectionEnd ?? value.length;
  const selected = value.slice(start, end);
  const next = `${value.slice(0, start)}${marker}${selected}${marker}${value.slice(end)}`;
  const cursorStart = start + marker.length;
  const cursorEnd = cursorStart + selected.length;
  return { next, cursorStart, cursorEnd };
}

function useFormatting(value: string, onChange: (next: string) => void) {
  const ref = useRef<HTMLTextAreaElement & HTMLInputElement>(null);

  function format(marker: string) {
    const el = ref.current;
    if (!el) return;
    const { next, cursorStart, cursorEnd } = applyMarker(el, value, marker);
    onChange(next);
    requestAnimationFrame(() => {
      el.focus();
      el.setSelectionRange(cursorStart, cursorEnd);
    });
  }

  function onKeyDown(event: React.KeyboardEvent) {
    const meta = event.metaKey || event.ctrlKey;
    if (!meta) return;
    if (event.key.toLowerCase() === "b") {
      event.preventDefault();
      format("**");
    } else if (event.key.toLowerCase() === "i") {
      event.preventDefault();
      format("*");
    }
  }

  return { ref, format, onKeyDown };
}

function Toolbar({ onBold, onItalic }: { onBold: () => void; onItalic: () => void }) {
  return (
    <div className="mb-1.5 flex gap-1">
      <Button type="button" size="sm" variant="ghost" className="h-7 px-2" onClick={onBold} title="Bold (Ctrl/Cmd+B)">
        <Bold className="size-3.5" />
      </Button>
      <Button
        type="button"
        size="sm"
        variant="ghost"
        className="h-7 px-2"
        onClick={onItalic}
        title="Italic (Ctrl/Cmd+I)"
      >
        <Italic className="size-3.5" />
      </Button>
    </div>
  );
}

type FieldProps = {
  value: string;
  onChange: (value: string) => void;
  rows?: number;
  className?: string;
  placeholder?: string;
  onPaste?: (event: React.ClipboardEvent<HTMLTextAreaElement>) => void;
};

export function RichTextField({ value, onChange, rows = 4, className, placeholder, onPaste }: FieldProps) {
  const { ref, format, onKeyDown } = useFormatting(value, onChange);
  return (
    <div>
      <Toolbar onBold={() => format("**")} onItalic={() => format("*")} />
      <Textarea
        ref={ref}
        value={value}
        rows={rows}
        placeholder={placeholder}
        className={cn(className)}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={onKeyDown}
        onPaste={onPaste}
      />
    </div>
  );
}

type InputFieldProps = {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
};

export function RichTextInput({ value, onChange, placeholder, className }: InputFieldProps) {
  const { ref, format, onKeyDown } = useFormatting(value, onChange);
  return (
    <div>
      <Toolbar onBold={() => format("**")} onItalic={() => format("*")} />
      <Input
        ref={ref}
        value={value}
        placeholder={placeholder}
        className={cn(className)}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={onKeyDown}
      />
    </div>
  );
}
