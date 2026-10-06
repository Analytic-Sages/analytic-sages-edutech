"use client";

import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import PhoneInput, {
  getCountries,
  getCountryCallingCode,
  type Country,
  type Value,
} from "react-phone-number-input";
import en from "react-phone-number-input/locale/en";
import "react-phone-number-input/style.css";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

type PhoneFieldProps = {
  id?: string;
  label?: string;
  hint?: string;
  value: string;
  country: Country | undefined;
  onChange: (phone: string, country: Country | undefined) => void;
  error?: string;
  className?: string;
};

export function PhoneField({
  id = "phone",
  label = "Phone / WhatsApp number",
  hint,
  value,
  country,
  onChange,
  error,
  className,
}: PhoneFieldProps) {
  return (
    <div className={cn("space-y-2", className)}>
      <Label htmlFor={id}>{label}</Label>
      {hint ? <p className="text-xs text-muted-foreground">{hint}</p> : null}
      <PhoneInput
        id={id}
        international
        defaultCountry={country || "NG"}
        country={country}
        value={(value || undefined) as Value | undefined}
        onChange={(next) => onChange(next || "", country)}
        onCountryChange={(next) => onChange(value, next)}
        labels={en}
        className={cn(
          "PhoneInput flex h-10 w-full items-stretch overflow-hidden rounded-lg border border-input bg-transparent text-sm",
          "focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/50",
          error && "border-destructive"
        )}
        numberInputProps={{
          className:
            "PhoneInputInput h-full min-w-0 flex-1 border-0 bg-transparent px-3 outline-none",
          placeholder: "801 234 5678",
        }}
      />
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
    </div>
  );
}

type CountrySelectFieldProps = {
  id?: string;
  label?: string;
  hint?: string;
  value: string;
  onChange: (iso2: string) => void;
  error?: string;
  className?: string;
};

export function CountrySelectField({
  id = "country_of_residence",
  label = "Country of residence",
  hint,
  value,
  onChange,
  error,
  className,
}: CountrySelectFieldProps) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [rect, setRect] = useState<DOMRect | null>(null);
  const triggerRef = useRef<HTMLButtonElement | null>(null);

  const options = useMemo(() => {
    return getCountries()
      .map((code) => ({
        code,
        name: en[code] || code,
        dial: `+${getCountryCallingCode(code)}`,
      }))
      .sort((a, b) => a.name.localeCompare(b.name));
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return options;
    return options.filter(
      (opt) =>
        opt.name.toLowerCase().includes(q) ||
        opt.code.toLowerCase().includes(q) ||
        opt.dial.includes(q)
    );
  }, [options, query]);

  const selected = options.find((opt) => opt.code === value);

  // Keep the popover anchored to the trigger as it moves (scroll/resize).
  useLayoutEffect(() => {
    if (!open || !triggerRef.current) return;
    const update = () => {
      if (triggerRef.current) setRect(triggerRef.current.getBoundingClientRect());
    };
    update();
    window.addEventListener("scroll", update, true);
    window.addEventListener("resize", update);
    return () => {
      window.removeEventListener("scroll", update, true);
      window.removeEventListener("resize", update);
    };
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <div className={cn("space-y-2", className)}>
      <Label htmlFor={id}>{label}</Label>
      {hint ? <p className="text-xs text-muted-foreground">{hint}</p> : null}
      <button
        ref={triggerRef}
        id={id}
        type="button"
        className={cn(
          "flex h-10 w-full items-center justify-between rounded-lg border border-input bg-transparent px-3 text-left text-sm",
          "hover:bg-muted/40 focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50",
          error && "border-destructive"
        )}
        onClick={() => setOpen((prev) => !prev)}
        aria-expanded={open}
        aria-haspopup="listbox"
      >
        <span className={selected ? "text-foreground" : "text-muted-foreground"}>
          {selected ? selected.name : "Select your country"}
        </span>
        <span className="text-muted-foreground">{open ? "▴" : "▾"}</span>
      </button>
      {error ? <p className="text-xs text-destructive">{error}</p> : null}

      {open && typeof document !== "undefined" && rect
        ? createPortal(
            <>
              <div
                className="fixed inset-0 z-[59]"
                onClick={() => setOpen(false)}
                aria-hidden
              />
              <div
                className="fixed z-[60] rounded-lg border bg-popover p-2 shadow-lg"
                style={{ top: rect.bottom + 4, left: rect.left, width: rect.width }}
                role="listbox"
              >
                <Input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search countries"
                  className="mb-2 h-9"
                  autoFocus
                />
                <ul className="max-h-48 overflow-y-auto">
                  {filtered.map((opt) => (
                    <li key={opt.code}>
                      <button
                        type="button"
                        role="option"
                        aria-selected={opt.code === value}
                        className={cn(
                          "w-full rounded-md px-2 py-2 text-left text-sm hover:bg-muted",
                          opt.code === value && "bg-muted font-medium"
                        )}
                        onClick={() => {
                          onChange(opt.code);
                          setQuery("");
                          setOpen(false);
                        }}
                      >
                        {opt.name}{" "}
                        <span className="text-muted-foreground">({opt.code})</span>
                      </button>
                    </li>
                  ))}
                  {filtered.length === 0 ? (
                    <li className="px-2 py-3 text-sm text-muted-foreground">No countries found</li>
                  ) : null}
                </ul>
              </div>
            </>,
            document.body
          )
        : null}
    </div>
  );
}
