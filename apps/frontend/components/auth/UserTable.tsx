"use client";

interface User {
  id: string;
  email: string;
  display_name: string;
  global_role: string;
  is_active: boolean;
  mfa_enabled: boolean;
  last_login_at: string | null;
}

interface UserTableProps {
  users: User[];
  onChangeRole: (userId: string) => void;
  onSuspend: (userId: string) => void;
}

const ROLE_COLOURS: Record<string, string> = {
  admin: "bg-violet-500/15 text-violet-300 border-violet-500/30",
  perito: "bg-blue-500/15 text-blue-300 border-blue-500/30",
  supervisor: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  investigador: "bg-cyan-500/15 text-cyan-300 border-cyan-500/30",
  advogado: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  consultor: "bg-orange-500/15 text-orange-300 border-orange-500/30",
  viewer: "bg-[#1f1f1f] text-[#888] border-[#2a2a2a]",
};

export function UserTable({ users, onChangeRole, onSuspend }: UserTableProps) {
  return (
    <div className="rounded-xl border border-[#1f1f1f] overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[#1f1f1f]">
            {["Member", "Role", "MFA", "Status", "Last login", ""].map((h) => (
              <th
                key={h}
                className="px-4 py-3 text-left text-xs font-medium text-[#555] uppercase tracking-wider first:pl-5 last:pr-5"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {users.map((user) => {
            const roleColour = ROLE_COLOURS[user.global_role] ?? ROLE_COLOURS["viewer"];
            return (
              <tr
                key={user.id}
                className="border-b border-[#111] last:border-0 hover:bg-[#111] transition-colors"
              >
                <td className="px-5 py-3.5">
                  <div className="flex flex-col gap-0.5">
                    <span className="text-white font-medium">{user.display_name}</span>
                    <span className="text-[#555] text-xs">{user.email}</span>
                  </div>
                </td>
                <td className="px-4 py-3.5">
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${roleColour}`}
                  >
                    {user.global_role}
                  </span>
                </td>
                <td className="px-4 py-3.5">
                  <span
                    className={`text-xs ${user.mfa_enabled ? "text-emerald-400" : "text-[#444]"}`}
                  >
                    {user.mfa_enabled ? "Active" : "Off"}
                  </span>
                </td>
                <td className="px-4 py-3.5">
                  <span
                    className={`text-xs ${user.is_active ? "text-[#888]" : "text-red-400"}`}
                  >
                    {user.is_active ? "Active" : "Suspended"}
                  </span>
                </td>
                <td className="px-4 py-3.5 text-xs text-[#555]">
                  {user.last_login_at
                    ? new Date(user.last_login_at).toLocaleDateString()
                    : "Never"}
                </td>
                <td className="pr-5 py-3.5">
                  <div className="flex gap-2 justify-end">
                    <button
                      type="button"
                      onClick={() => onChangeRole(user.id)}
                      className="text-xs text-[#555] hover:text-white transition-colors px-2 py-1 rounded border border-transparent hover:border-[#1f1f1f]"
                    >
                      Change role
                    </button>
                    {user.is_active && (
                      <button
                        type="button"
                        onClick={() => onSuspend(user.id)}
                        className="text-xs text-red-500/70 hover:text-red-400 transition-colors px-2 py-1 rounded border border-transparent hover:border-red-500/20"
                      >
                        Suspend
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
