"use client";

import { useMemo } from "react";
import { Combobox } from "@base-ui/react/combobox";
import { Check, ChevronDown } from "lucide-react";
import PhoneInput, {
  getCountries,
  getCountryCallingCode,
  type Country,
  type Value,
} from "react-phone-number-input";
import en from "react-phone-number-input/locale/en";
import "react-phone-number-input/style.css";
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

type CountryOption = { code: Country; name: string; dial: string };

type CountrySelectFieldProps = {
  id?: string;
  label?: string;
  hint?: string;
  value: string;
  onChange: (iso2: string) => void;
  error?: string;
  className?: string;
};

/**
 * Searchable country picker built on Base UI's Combobox: its Portal + Positioner
 * handle collision/flipping and scroll for us, so the option list can never be
 * clipped by a parent card (`overflow-hidden`) or run off-screen.
 */
export function CountrySelectField({
  id = "country_of_residence",
  label = "Country of residence",
  hint,
  value,
  onChange,
  error,
  className,
}: CountrySelectFieldProps) {
  const options = useMemo<CountryOption[]>(
    () =>
      getCountries()
        .map((code) => ({
          code,
          name: en[code] || code,
          dial: `+${getCountryCallingCode(code)}`,
        }))
        .sort((a, b) => a.name.localeCompare(b.name)),
    []
  );

  const selected = useMemo(
    () => options.find((opt) => opt.code === value) ?? null,
    [options, value]
  );

  return (
    <div className={cn("space-y-2", className)}>
      <Label htmlFor={id}>{label}</Label>
      {hint ? <p className="text-xs text-muted-foreground">{hint}</p> : null}
      <Combobox.Root
        items={options}
        value={selected}
        onValueChange={(next) => onChange(next ? next.code : "")}
        itemToStringLabel={(option) => option.name}
        itemToStringValue={(option) => option.code}
        isItemEqualToValue={(item, currentItem) => item.code === currentItem.code}
      >
        <div className="relative">
          <Combobox.Input
            id={id}
            placeholder="Search countries"
            aria-invalid={error ? true : undefined}
            className={cn(
              "flex h-10 w-full rounded-lg border border-input bg-transparent px-3 pr-9 text-sm outline-none",
              "focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50",
              "placeholder:text-muted-foreground dark:bg-input/30",
              error && "border-destructive"
            )}
          />
          <Combobox.Trigger className="absolute top-0 right-0 flex h-10 w-9 items-center justify-center text-muted-foreground">
            <Combobox.Icon>
              <ChevronDown className="size-4" />
            </Combobox.Icon>
          </Combobox.Trigger>
        </div>
        <Combobox.Portal>
          <Combobox.Positioner sideOffset={4} className="isolate z-[60]">
            <Combobox.Popup className="max-h-72 w-(--anchor-width) min-w-48 overflow-y-auto rounded-lg border bg-popover p-1 text-popover-foreground shadow-lg outline-none">
              <Combobox.Empty className="px-2 py-3 text-sm text-muted-foreground">
                No countries found
              </Combobox.Empty>
              <Combobox.List>
                {(option: CountryOption) => (
                  <Combobox.Item
                    key={option.code}
                    value={option}
                    className="flex cursor-default items-center gap-2 rounded-md px-2 py-2 text-sm outline-none data-[highlighted]:bg-accent data-[highlighted]:text-accent-foreground"
                  >
                    <span className="min-w-0 flex-1 truncate">{option.name}</span>
                    <span className="text-xs text-muted-foreground">{option.code}</span>
                    <Combobox.ItemIndicator>
                      <Check className="size-4" />
                    </Combobox.ItemIndicator>
                  </Combobox.Item>
                )}
              </Combobox.List>
            </Combobox.Popup>
          </Combobox.Positioner>
        </Combobox.Portal>
      </Combobox.Root>
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
    </div>
  );
}

