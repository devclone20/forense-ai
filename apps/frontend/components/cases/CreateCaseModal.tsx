"use client";

import { Button } from "@/components/ui/button";
import { Dialog, DialogPanel, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import type { CaseCreate, ConfidentialityLevel, ForensicDomain } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useState } from "react";

interface CreateCaseModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: CaseCreate) => Promise<void>;
}

interface FormErrors {
  title?: string;
  forensic_domain?: string;
}

const initialState: CaseCreate = {
  title: "",
  description: "",
  forensic_domain: "digital",
  confidentiality: "normal",
  tags: [],
  domain_metadata: {},
};

export function CreateCaseModal({ open, onClose, onSubmit }: CreateCaseModalProps) {
  const [form, setForm] = useState<CaseCreate>(initialState);
  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);

  function validate(): boolean {
    const next: FormErrors = {};
    if (!form.title.trim()) next.title = "O título é obrigatório.";
    if (!form.forensic_domain) next.forensic_domain = "Selecione um domínio.";
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    try {
      await onSubmit(form);
      setForm(initialState);
      setErrors({});
      onClose();
    } finally {
      setLoading(false);
    }
  }

  function handleClose() {
    if (loading) return;
    setForm(initialState);
    setErrors({});
    onClose();
  }

  return (
    <Dialog open={open} onClose={handleClose}>
      <DialogPanel>
        <form onSubmit={handleSubmit} noValidate>
          <div className="px-6 pt-6 pb-2">
            <DialogTitle>Novo Caso</DialogTitle>
            <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1">
              Preencha os dados essenciais. Pode editar os detalhes depois.
            </p>
          </div>

          <div className="px-6 py-4 space-y-4">
            {/* Title */}
            <div>
              <label className="block text-xs font-medium text-[hsl(var(--muted))] mb-1.5">
                Título <span className="text-destructive">*</span>
              </label>
              <Input
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                placeholder="ex: Análise de dispositivo móvel — suspeito X"
                className={cn(errors.title && "border-destructive")}
                autoFocus
              />
              {errors.title && (
                <p className="text-xs text-destructive mt-1">{errors.title}</p>
              )}
            </div>

            {/* Domain */}
            <div>
              <label className="block text-xs font-medium text-[hsl(var(--muted))] mb-1.5">
                Domínio forense <span className="text-destructive">*</span>
              </label>
              <Select
                value={form.forensic_domain}
                onChange={(e) =>
                  setForm({ ...form, forensic_domain: e.target.value as ForensicDomain })
                }
                className={cn(errors.forensic_domain && "border-destructive")}
              >
                <option value="digital">Digital</option>
                <option value="medico_legal">Médico-Legal</option>
                <option value="financeiro">Financeiro</option>
              </Select>
              {errors.forensic_domain && (
                <p className="text-xs text-destructive mt-1">{errors.forensic_domain}</p>
              )}
            </div>

            {/* Description */}
            <div>
              <label className="block text-xs font-medium text-[hsl(var(--muted))] mb-1.5">
                Descrição
              </label>
              <textarea
                value={form.description ?? ""}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                placeholder="Contexto, objectivo da investigação, notas iniciais..."
                rows={4}
                className={cn(
                  "w-full rounded border border-[hsl(var(--border))] bg-[hsl(var(--surface))]",
                  "px-3 py-2 text-sm text-foreground placeholder:text-[hsl(var(--muted-foreground))]",
                  "transition-colors focus:border-accent focus:outline-none resize-none",
                )}
              />
            </div>

            {/* Confidentiality */}
            <div>
              <label className="block text-xs font-medium text-[hsl(var(--muted))] mb-1.5">
                Confidencialidade
              </label>
              <Select
                value={form.confidentiality}
                onChange={(e) =>
                  setForm({
                    ...form,
                    confidentiality: e.target.value as ConfidentialityLevel,
                  })
                }
              >
                <option value="normal">Normal</option>
                <option value="reservado">Reservado</option>
                <option value="confidencial">Confidencial</option>
                <option value="secreto">Secreto</option>
              </Select>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-2 px-6 py-4 border-t border-[hsl(var(--border))]">
            <Button
              type="button"
              variant="ghost"
              onClick={handleClose}
              disabled={loading}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "A criar..." : "Criar caso"}
            </Button>
          </div>
        </form>
      </DialogPanel>
    </Dialog>
  );
}
