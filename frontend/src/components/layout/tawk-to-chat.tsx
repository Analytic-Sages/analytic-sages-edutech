"use client";

import { useEffect, useRef, useState } from "react";
import Script from "next/script";
import Link from "next/link";
import { MessageCircle, Send, X } from "lucide-react";
import { siteConfig } from "@/config/site";

const SUGGESTIONS = [
  "What courses and programs do you offer?",
  "Which program is right for me?",
  "I need help with my account.",
  "I have a question about a course.",
];

type ChatLink = { href: string; label: string };
type ChatMessage = {
  id: string;
  from: "user" | "agent";
  text: string;
  links?: ChatLink[];
};

type TawkApi = {
  hideWidget?: () => void;
  showWidget?: () => void;
  maximize?: () => void;
  setAttributes?: (attrs: Record<string, string>, cb?: (err?: unknown) => void) => void;
  addEvent?: (
    eventName: string,
    metadata?: Record<string, string> | ((error?: unknown) => void),
    callback?: (error?: unknown) => void
  ) => void;
  addTags?: (tags: string[], cb?: (err?: unknown) => void) => void;
  onLoad?: () => void;
  onChatMaximized?: () => void;
  onChatMinimized?: () => void;
  onChatHidden?: () => void;
};

declare global {
  interface Window {
    Tawk_API?: TawkApi;
    Tawk_LoadStart?: Date;
  }
}

function tawk(): TawkApi {
  window.Tawk_API = window.Tawk_API || {};
  return window.Tawk_API;
}

function setTawkVisible(visible: boolean) {
  document.body.classList.toggle("as-tawk-open", visible);
}

/** Tawk rewrites the tab to "1 new message" and blinks it. Keep the real page title. */
function isTawkTabAlert(title: string) {
  const value = title.trim();
  if (!value) return false;
  if (/^(?:\(?\d+\)?\s*)?new messages?$/i.test(value)) return true;
  if (/^\(\d+\)\s+/.test(value)) return true;
  return false;
}

function guardDocumentTitle() {
  const descriptor = Object.getOwnPropertyDescriptor(Document.prototype, "title");
  if (!descriptor?.get || !descriptor?.set) return () => undefined;

  const read = descriptor.get;
  const write = descriptor.set;
  let lastGood = read.call(document) as string;

  Object.defineProperty(document, "title", {
    configurable: true,
    enumerable: descriptor.enumerable ?? true,
    get() {
      return read.call(this);
    },
    set(value: string) {
      if (typeof value === "string" && isTawkTabAlert(value)) return;
      lastGood = value;
      write.call(this, value);
    },
  });

  const titleEl = document.querySelector("title");
  const observer = titleEl
    ? new MutationObserver(() => {
        const current = read.call(document) as string;
        if (isTawkTabAlert(current)) {
          write.call(document, lastGood);
          return;
        }
        lastGood = current;
      })
    : null;
  observer?.observe(titleEl, { childList: true, characterData: true, subtree: true });

  return () => {
    observer?.disconnect();
    delete (document as { title?: string }).title;
  };
}

function replyFor(question: string): Pick<ChatMessage, "text" | "links"> {
  if (question === SUGGESTIONS[0]) {
    return {
      text: "We run instructor-led live cohorts and a self-paced catalog. Cohort 9 (SQL Blockchain Data Analytics) is the live program. Self-paced courses are visible now and launch when the player is ready.",
      links: [
        { href: "/instructor-led", label: "Instructor-led programs" },
        { href: "/courses", label: "Self-paced catalog" },
      ],
    };
  }
  if (question === SUGGESTIONS[1]) {
    return {
      text: "If you want live classes, community, and a 4-week SQL + blockchain data path, start with Cohort 9. If you prefer to browse on your own, the self-paced catalog is the place to look.",
      links: [
        { href: "/instructor-led", label: "See Cohort 9" },
        { href: "/courses", label: "Browse self-paced" },
      ],
    };
  }
  if (question === SUGGESTIONS[2]) {
    return {
      text: "Sign in to reach your dashboard, enrollments, and classroom. If you just verified email, you should already be signed in. Need a person? Use Talk to the team, or email support.",
      links: [
        { href: "/login?next=/dashboard", label: "Sign in" },
        { href: "/dashboard", label: "Dashboard" },
      ],
    };
  }
  if (question === SUGGESTIONS[3]) {
    return {
      text: "Open the course or program page for schedule, syllabus, and enrollment. You can also tell us which course you mean and we’ll point you to the right page.",
      links: [
        { href: "/instructor-led", label: "Instructor-led" },
        { href: "/courses", label: "Courses" },
      ],
    };
  }
  return {
    text: `Thanks - we have that. Keep typing here, or tap Talk to the team for a live person. You can also email ${siteConfig.emails.support}.`,
  };
}

function newId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function TawkToChat() {
  const [panelOpen, setPanelOpen] = useState(false);
  const [tawkOpen, setTawkOpen] = useState(false);
  const [loadScript, setLoadScript] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const loaded = useRef(false);
  const wantLive = useRef(false);
  const threadRef = useRef<HTMLDivElement>(null);

  function concealTawk() {
    wantLive.current = false;
    tawk().hideWidget?.();
    setTawkVisible(false);
    setTawkOpen(false);
  }

  useEffect(() => guardDocumentTitle(), []);

  useEffect(() => {
    const api = tawk();
    api.hideWidget?.();
    setTawkVisible(false);
    api.onLoad = () => {
      loaded.current = true;
      if (!wantLive.current) api.hideWidget?.();
    };
    api.onChatMaximized = () => {
      setTawkVisible(true);
      setTawkOpen(true);
      setPanelOpen(false);
    };
    api.onChatMinimized = concealTawk;
    api.onChatHidden = concealTawk;
    return () => setTawkVisible(false);
  }, []);

  useEffect(() => {
    threadRef.current?.scrollTo({ top: threadRef.current.scrollHeight });
  }, [messages, panelOpen]);

  function loadTawk() {
    if (loaded.current || loadScript) return;
    window.Tawk_LoadStart = new Date();
    tawk();
    setLoadScript(true);
  }

  function passContextToTawk() {
    const transcript = messages
      .map((m) => `${m.from === "user" ? "Visitor" : "Site"}: ${m.text}`)
      .join(" | ")
      .slice(0, 255);
    const lastUser = [...messages].reverse().find((m) => m.from === "user")?.text ?? "";
    const api = tawk();
    api.setAttributes?.(
      {
        requestedhelp: lastUser.slice(0, 255),
        transcript,
      },
      () => undefined
    );
    api.addEvent?.("suggested-question", { question: lastUser.slice(0, 255) }, () => undefined);
    api.addTags?.(["suggested-question"], () => undefined);
  }

  function revealTawk() {
    passContextToTawk();
    const api = tawk();
    setTawkVisible(true);
    api.showWidget?.();
    api.maximize?.();
    setTawkOpen(true);
    setPanelOpen(false);
  }

  function openLiveTawk() {
    wantLive.current = true;
    loadTawk();
    if (loaded.current) {
      revealTawk();
      return;
    }
    const wait = window.setInterval(() => {
      if (!loaded.current) return;
      window.clearInterval(wait);
      revealTawk();
    }, 200);
    window.setTimeout(() => window.clearInterval(wait), 15000);
  }

  function startThread(question: string) {
    const reply = replyFor(question);
    setMessages([
      { id: newId(), from: "user", text: question },
      { id: newId(), from: "agent", text: reply.text, links: reply.links },
    ]);
    setPanelOpen(true);
  }

  function startBlankThread() {
    setMessages([
      {
        id: newId(),
        from: "agent",
        text: "Tell us what you need. Pick a question above, type here, or talk to the team when you’re ready.",
      },
    ]);
    setPanelOpen(true);
    window.setTimeout(() => document.getElementById("as-chat-draft")?.focus(), 50);
  }

  function sendDraft() {
    const question = draft.trim();
    if (!question) return;
    setDraft("");
    const reply = replyFor(question);
    setMessages((prev) => [
      ...prev,
      { id: newId(), from: "user", text: question },
      { id: newId(), from: "agent", text: reply.text, links: reply.links },
    ]);
  }

  function openPanel() {
    setPanelOpen(true);
  }

  const inThread = messages.length > 0;
  const showLauncher = !tawkOpen;

  return (
    <>
      {loadScript ? (
        <Script
          id="tawk-to"
          src="https://embed.tawk.to/6a85ac466a5078344713e929/1k0d2htqh"
          strategy="afterInteractive"
          onLoad={() => {
            loaded.current = true;
            if (wantLive.current) {
              revealTawk();
              return;
            }
            tawk().hideWidget?.();
          }}
        />
      ) : null}

      {showLauncher && panelOpen ? (
        <div className="fixed right-4 bottom-20 z-50 flex h-[min(32rem,calc(100dvh-7rem))] w-[min(100%-2rem,22rem)] flex-col overflow-hidden rounded-2xl border bg-background shadow-elevated md:bottom-4">
          <div className="flex items-start justify-between gap-3 border-b px-4 py-3">
            <div>
              <p className="font-heading text-base font-semibold">Hi! How can we help?</p>
              <p className="text-xs text-muted-foreground">Analytic Sages</p>
            </div>
            <button
              type="button"
              onClick={() => setPanelOpen(false)}
              className="rounded-full p-1 text-muted-foreground hover:bg-muted"
              aria-label="Close chat"
            >
              <X className="size-4" />
            </button>
          </div>

          <div ref={threadRef} className="min-h-0 flex-1 space-y-3 overflow-y-auto px-4 py-3">
            {!inThread ? (
              <>
                <p className="text-sm text-muted-foreground">
                  Choose a question or type your own. Live chat with the team is one tap away.
                </p>
                <div className="flex flex-col gap-2">
                  {SUGGESTIONS.map((question) => (
                    <button
                      key={question}
                      type="button"
                      onClick={() => startThread(question)}
                      className="rounded-lg border px-3 py-2 text-left text-sm hover:border-brand-orange/50 hover:bg-muted/50"
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={message.from === "user" ? "flex justify-end" : "flex justify-start"}
                >
                  <div
                    className={
                      message.from === "user"
                        ? "max-w-[90%] rounded-2xl rounded-br-md bg-brand-navy px-3 py-2 text-sm text-white"
                        : "max-w-[90%] rounded-2xl rounded-bl-md bg-muted px-3 py-2 text-sm"
                    }
                  >
                    <p>{message.text}</p>
                    {message.links?.length ? (
                      <div className="mt-2 flex flex-col gap-1">
                        {message.links.map((link) => (
                          <Link
                            key={link.href}
                            href={link.href}
                            className="font-medium text-brand-orange underline-offset-2 hover:underline"
                            onClick={() => setPanelOpen(false)}
                          >
                            {link.label}
                          </Link>
                        ))}
                      </div>
                    ) : null}
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="border-t p-3">
            <form
              className="flex items-end gap-2"
              onSubmit={(event) => {
                event.preventDefault();
                if (!inThread && !draft.trim()) return;
                if (draft.trim()) sendDraft();
              }}
            >
              <label className="sr-only" htmlFor="as-chat-draft">
                Message
              </label>
              <textarea
                id="as-chat-draft"
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    sendDraft();
                  }
                }}
                rows={1}
                placeholder={inThread ? "Type a message…" : "Or type a question…"}
                className="max-h-24 min-h-10 flex-1 resize-none rounded-xl border bg-background px-3 py-2 text-sm outline-none focus:border-brand-orange"
              />
              <button
                type="submit"
                className="flex size-10 shrink-0 items-center justify-center rounded-full bg-brand-navy text-white hover:bg-brand-navy/90"
                aria-label="Send message"
              >
                <Send className="size-4" />
              </button>
            </form>
            <button
              type="button"
              onClick={inThread ? openLiveTawk : startBlankThread}
              className="mt-2 w-full rounded-full bg-brand-orange px-4 py-2 text-sm font-semibold text-white hover:bg-brand-orange/90"
            >
              {inThread ? "Talk to the team" : "Chat with us"}
            </button>
          </div>
        </div>
      ) : null}

      {showLauncher && !panelOpen ? (
        <button
          type="button"
          onClick={openPanel}
          className="fixed right-4 bottom-20 z-50 flex size-14 items-center justify-center rounded-full bg-brand-navy text-white shadow-elevated hover:bg-brand-navy/90 md:bottom-4"
          aria-label="Open chat"
        >
          <MessageCircle className="size-6" />
        </button>
      ) : null}
    </>
  );
}
