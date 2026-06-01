import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { CaseStatus, ForensicDomain } from "./types";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function formatDate(iso: string): string {
  return new Intl.DateTimeFormat("pt-PT", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(iso));
}

export function formatDateTime(iso: string): string {
  return new Intl.DateTimeFormat("pt-PT", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));
}

export const STATUS_LABELS: Record<CaseStatus, string> = {
  aberto: "Aberto",
  em_investigacao: "Em Investigação",
  em_revisao: "Em Revisão",
  fechado: "Fechado",
  arquivado: "Arquivado",
};

export const STATUS_STYLES: Record<CaseStatus, string> = {
  aberto:
    "bg-blue-500/10 text-blue-400 border border-blue-500/20",
  em_investigacao:
    "bg-amber-500/10 text-amber-400 border border-amber-500/20",
  em_revisao:
    "bg-violet-500/10 text-violet-400 border border-violet-500/20",
  fechado:
    "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20",
  arquivado:
    "bg-neutral-500/10 text-neutral-400 border border-neutral-500/20",
};

export const DOMAIN_LABELS: Record<ForensicDomain, string> = {
  digital: "Digital",
  medico_legal: "Médico-Legal",
  financeiro: "Financeiro",
};

export const DOMAIN_STYLES: Record<ForensicDomain, string> = {
  digital: "bg-blue-500/10 text-blue-400 border border-blue-500/20",
  medico_legal: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20",
  financeiro: "bg-amber-500/10 text-amber-400 border border-amber-500/20",
};
