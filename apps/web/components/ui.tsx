import type { ButtonHTMLAttributes, HTMLAttributes, ReactNode } from "react";
import Link from "next/link";
import { ArrowRight, CircleDot, Sparkles } from "lucide-react";

import { cx } from "@/lib/utils";

type ButtonVariant = "primary" | "secondary";

function buttonClassName(variant: ButtonVariant): string {
  return cx(
    "focus-pop inline-flex min-h-12 items-center justify-center gap-3 rounded-full border-2 border-[var(--border)] px-5 py-3 text-sm font-bold tracking-[0.01em] transition-all duration-300 ease-[cubic-bezier(0.34,1.56,0.64,1)] disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-x-0 disabled:hover:translate-y-0",
    variant === "primary"
      ? "bg-[var(--accent)] text-[var(--accent-foreground)] shadow-[var(--shadow-hard)] hover:-translate-x-0.5 hover:-translate-y-0.5 hover:shadow-[var(--shadow-hard-hover)] active:translate-x-0.5 active:translate-y-0.5 active:shadow-[var(--shadow-hard-active)]"
      : "bg-white text-[var(--foreground)] hover:bg-[var(--tertiary)]",
  );
}

export function AppWordmark() {
  return (
    <Link href="/" className="inline-flex items-center gap-3 font-[family-name:var(--font-outfit)] text-lg font-extrabold tracking-tight">
      <span className="inline-flex h-11 w-11 items-center justify-center rounded-[24px_24px_24px_0] border-2 border-[var(--border)] bg-[var(--secondary)] shadow-[var(--shadow-hard)]">
        <Sparkles className="h-5 w-5" strokeWidth={2.5} />
      </span>
      <span>Skylattice App</span>
    </Link>
  );
}

export function ButtonLink({
  href,
  children,
  variant = "primary",
  className,
}: {
  href: string;
  children: ReactNode;
  variant?: ButtonVariant;
  className?: string;
}) {
  return (
    <Link href={href} className={cx(buttonClassName(variant), className)}>
      <span>{children}</span>
      <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-white text-[var(--foreground)]">
        <ArrowRight className="h-4 w-4" strokeWidth={2.5} />
      </span>
    </Link>
  );
}

export function CandyButton({
  className,
  variant = "primary",
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant }) {
  return (
    <button {...props} className={cx(buttonClassName(variant), className)}>
      {children}
    </button>
  );
}

export function StickerCard({
  className,
  children,
  tone = "white",
  icon,
}: HTMLAttributes<HTMLDivElement> & {
  tone?: "white" | "accent" | "secondary" | "tertiary" | "quaternary";
  icon?: ReactNode;
}) {
  const backgrounds = {
    white: "bg-white",
    accent: "bg-[color:rgba(139,92,246,0.14)]",
    secondary: "bg-[color:rgba(244,114,182,0.14)]",
    tertiary: "bg-[color:rgba(251,191,36,0.18)]",
    quaternary: "bg-[color:rgba(52,211,153,0.18)]",
  };
  return (
    <div
      className={cx(
        "confetti wiggle-on-hover relative rounded-[24px] border-2 border-[var(--border)] p-6 shadow-[var(--shadow-soft)]",
        backgrounds[tone],
        className,
      )}
    >
      {icon ? (
        <div className="absolute -top-5 left-5 inline-flex h-12 w-12 items-center justify-center rounded-full border-2 border-[var(--border)] bg-white shadow-[var(--shadow-hard)]">
          {icon}
        </div>
      ) : null}
      {children}
    </div>
  );
}

export function StatusChip({
  children,
  tone = "muted",
}: {
  children: ReactNode;
  tone?: "muted" | "accent" | "secondary" | "tertiary" | "quaternary";
}) {
  const tones = {
    muted: "bg-[var(--muted)] text-[var(--foreground)]",
    accent: "bg-[var(--accent)] text-white",
    secondary: "bg-[var(--secondary)] text-white",
    tertiary: "bg-[var(--tertiary)] text-[var(--foreground)]",
    quaternary: "bg-[var(--quaternary)] text-[var(--foreground)]",
  };
  return (
    <span className={cx("inline-flex items-center gap-2 rounded-full border-2 border-[var(--border)] px-3 py-1 text-xs font-bold uppercase tracking-[0.14em]", tones[tone])}>
      <CircleDot className="h-3.5 w-3.5" strokeWidth={2.5} />
      {children}
    </span>
  );
}

export function SectionHeading({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div className="max-w-2xl space-y-3">
        <p className="text-xs font-extrabold uppercase tracking-[0.24em] text-[var(--muted-foreground)]">{eyebrow}</p>
        <h2 className="font-[family-name:var(--font-outfit)] text-3xl font-extrabold tracking-tight md:text-5xl">{title}</h2>
        <p className="max-w-xl text-base leading-7 text-[var(--muted-foreground)]">{description}</p>
      </div>
      {action}
    </div>
  );
}

export function PageFrame({ children }: { children: ReactNode }) {
  return <div className="mx-auto w-full max-w-6xl px-4 py-10 md:px-6 md:py-16">{children}</div>;
}

export function WorkspaceHero({
  title,
  description,
  chips,
}: {
  title: string;
  description: string;
  chips: ReactNode;
}) {
  return (
    <section className="dot-grid relative overflow-hidden rounded-[32px] border-2 border-[var(--border)] bg-white/80 px-6 py-10 shadow-[var(--shadow-soft)] backdrop-blur-sm md:px-10">
      <div className="absolute -left-10 top-6 h-40 w-40 rounded-full border-2 border-[var(--border)] bg-[color:rgba(251,191,36,0.35)]" />
      <div className="absolute right-6 top-6 h-24 w-24 rounded-[28px_28px_28px_0] border-2 border-[var(--border)] bg-[color:rgba(244,114,182,0.25)]" />
      <div className="relative space-y-4">
        <h1 className="max-w-3xl font-[family-name:var(--font-outfit)] text-4xl font-extrabold tracking-tight md:text-6xl">{title}</h1>
        <p className="max-w-2xl text-base leading-8 text-[var(--muted-foreground)] md:text-lg">{description}</p>
        <div className="flex flex-wrap gap-3">{chips}</div>
      </div>
    </section>
  );
}

export function PreviewNotice({
  title = "Read-only preview data",
  description = "This surface is showing representative command, device, and approval records so you can inspect the product shape before GitHub sign-in, pairing, or a live local runtime are configured.",
  action,
}: {
  title?: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <StickerCard tone="tertiary" className="px-6 py-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div className="space-y-3">
          <p className="text-xs font-extrabold uppercase tracking-[0.22em] text-[var(--muted-foreground)]">Preview mode</p>
          <h2 className="font-[family-name:var(--font-outfit)] text-2xl font-extrabold tracking-tight md:text-3xl">{title}</h2>
          <p className="max-w-3xl text-sm leading-7 text-[var(--foreground)]">{description}</p>
        </div>
        {action}
      </div>
    </StickerCard>
  );
}

export function HostedAlphaNotice({
  title = "Hosted Alpha configuration required",
  description,
  blockers,
  action,
}: {
  title?: string;
  description: string;
  blockers: string[];
  action?: ReactNode;
}) {
  return (
    <StickerCard tone="secondary" className="px-6 py-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div className="space-y-3">
          <p className="text-xs font-extrabold uppercase tracking-[0.22em] text-white/80">Hosted alpha</p>
          <h2 className="font-[family-name:var(--font-outfit)] text-2xl font-extrabold tracking-tight text-white md:text-3xl">{title}</h2>
          <p className="max-w-3xl text-sm leading-7 text-white">{description}</p>
          {blockers.length ? (
            <ul className="space-y-2 text-sm leading-7 text-white">
              {blockers.map((blocker) => (
                <li key={blocker}>- {blocker}</li>
              ))}
            </ul>
          ) : null}
        </div>
        {action}
      </div>
    </StickerCard>
  );
}

export function AppStatusBanner({
  mode,
  title,
  description,
  blockers = [],
  chips,
  action,
}: {
  mode: "preview" | "blocked" | "live" | "development";
  title: string;
  description: string;
  blockers?: string[];
  chips?: ReactNode;
  action?: ReactNode;
}) {
  const tone = mode === "blocked"
    ? "secondary"
    : mode === "preview"
      ? "tertiary"
      : mode === "development"
        ? "white"
        : "quaternary";
  const eyebrow = mode === "blocked"
    ? "Hosted Alpha blocked"
    : mode === "preview"
      ? "Preview mode"
      : mode === "development"
        ? "Local development"
        : "Local-first control";
  const textClass = mode === "blocked" ? "text-white" : "text-[var(--foreground)]";
  const subtleTextClass = mode === "blocked" ? "text-white/80" : "text-[var(--muted-foreground)]";

  return (
    <StickerCard tone={tone} className="mb-8 px-6 py-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-3">
          <p className={`text-xs font-extrabold uppercase tracking-[0.22em] ${subtleTextClass}`}>{eyebrow}</p>
          <h2 className={`font-[family-name:var(--font-outfit)] text-2xl font-extrabold tracking-tight md:text-3xl ${textClass}`}>{title}</h2>
          <p className={`max-w-3xl text-sm leading-7 ${textClass}`}>{description}</p>
          {chips ? <div className="flex flex-wrap gap-3">{chips}</div> : null}
          {blockers.length ? (
            <ul className={`space-y-2 text-sm leading-7 ${textClass}`}>
              {blockers.map((blocker) => (
                <li key={blocker}>- {blocker}</li>
              ))}
            </ul>
          ) : null}
        </div>
        {action}
      </div>
    </StickerCard>
  );
}
