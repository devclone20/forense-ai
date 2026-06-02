"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { UserTable } from "@/components/auth/UserTable";
import { InviteModal } from "@/components/auth/InviteModal";

interface User {
  id: string;
  email: string;
  display_name: string;
  global_role: string;
  is_active: boolean;
  mfa_enabled: boolean;
  last_login_at: string | null;
}

interface PendingInvite {
  id: string;
  email: string;
  role: string;
  expires_at: string;
}

const ROLES = ["admin", "perito", "investigador", "supervisor", "advogado", "consultor", "viewer"];

export default function AdminUsersPage() {
  const [tab, setTab] = useState<"members" | "invites">("members");
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [showInvite, setShowInvite] = useState(false);
  const [inviteLink, setInviteLink] = useState<string | null>(null);
  const [changeRoleUserId, setChangeRoleUserId] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<User[]>("/api/v1/admin/users")
      .then(setUsers)
      .finally(() => setLoading(false));
  }, []);

  async function handleSuspend(userId: string) {
    if (!confirm("Suspend this user? Their sessions will be revoked immediately.")) return;
    try {
      await api.post(`/api/v1/admin/users/${userId}/suspend`, {});
      setUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, is_active: false } : u)),
      );
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to suspend user");
    }
  }

  async function handleChangeRole(userId: string, newRole: string) {
    try {
      await api.patch(`/api/v1/admin/users/${userId}/role`, { role: newRole });
      setUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, global_role: newRole } : u)),
      );
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to change role");
    }
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-white text-2xl font-semibold tracking-tight">Team</h1>
          <p className="text-[#666] text-sm mt-1">
            {users.length} member{users.length !== 1 ? "s" : ""}
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowInvite(true)}
          className="px-4 py-2 rounded-lg text-sm font-medium bg-white text-black hover:bg-[#f0f0f0] active:scale-[0.98] transition-all"
        >
          Invite member
        </button>
      </div>

      {/* Invite link banner */}
      {inviteLink && (
        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl px-4 py-3 flex items-center justify-between gap-4">
          <div>
            <p className="text-xs font-medium text-emerald-400">Invitation created</p>
            <p className="text-xs text-[#888] mt-0.5 font-mono break-all">{inviteLink}</p>
          </div>
          <button
            type="button"
            onClick={() => setInviteLink(null)}
            className="text-[#555] hover:text-white text-xs shrink-0"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 border-b border-[#1f1f1f]">
        {(["members", "invites"] as const).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={[
              "px-4 py-2 text-sm font-medium capitalize transition-colors border-b-2 -mb-px",
              tab === t
                ? "border-white text-white"
                : "border-transparent text-[#555] hover:text-[#888]",
            ].join(" ")}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === "members" && (
        <>
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="w-5 h-5 border-2 border-[#333] border-t-white rounded-full animate-spin" />
            </div>
          ) : (
            <UserTable
              users={users}
              onSuspend={handleSuspend}
              onChangeRole={(uid) => setChangeRoleUserId(uid)}
            />
          )}
        </>
      )}

      {tab === "invites" && (
        <div className="text-sm text-[#555] py-8 text-center">
          Pending invitations will appear here.
          <br />
          <span className="text-xs">(Full invite listing requires a dedicated endpoint — coming in next iteration)</span>
        </div>
      )}

      {/* Invite modal */}
      {showInvite && (
        <InviteModal
          onClose={() => setShowInvite(false)}
          onSuccess={(link) => {
            setShowInvite(false);
            setInviteLink(link);
          }}
        />
      )}

      {/* Change role modal (inline) */}
      {changeRoleUserId && (
        <ChangeRoleModal
          userId={changeRoleUserId}
          currentRole={users.find((u) => u.id === changeRoleUserId)?.global_role ?? "viewer"}
          onClose={() => setChangeRoleUserId(null)}
          onSave={(role) => {
            handleChangeRole(changeRoleUserId, role);
            setChangeRoleUserId(null);
          }}
        />
      )}
    </div>
  );
}

function ChangeRoleModal({
  currentRole,
  onClose,
  onSave,
}: {
  userId: string;
  currentRole: string;
  onClose: () => void;
  onSave: (role: string) => void;
}) {
  const [role, setRole] = useState(currentRole);
  const ROLES = ["admin", "perito", "investigador", "supervisor", "advogado", "consultor", "viewer"];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div
        className="absolute inset-0"
        onClick={onClose}
        role="button"
        aria-label="Close"
        tabIndex={-1}
        onKeyDown={(e) => e.key === "Escape" && onClose()}
      />
      <div className="relative bg-[#111] border border-[#1f1f1f] rounded-2xl px-8 py-7 w-full max-w-sm flex flex-col gap-5">
        <h2 className="text-white text-lg font-semibold">Change role</h2>
        <select
          value={role}
          onChange={(e) => setRole(e.target.value)}
          className="w-full rounded-lg bg-[#0a0a0a] border border-[#1f1f1f] px-3.5 py-2.5 text-white text-sm focus:outline-none focus:ring-1 focus:ring-[#333]"
        >
          {ROLES.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => onSave(role)}
            className="flex-1 py-2.5 rounded-lg text-sm font-medium bg-white text-black hover:bg-[#f0f0f0] transition-all"
          >
            Save
          </button>
          <button
            type="button"
            onClick={onClose}
            className="py-2.5 px-4 rounded-lg text-sm font-medium border border-[#1f1f1f] text-[#888] hover:text-white hover:border-[#333] transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
