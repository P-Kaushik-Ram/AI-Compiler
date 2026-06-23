import { Cpu } from "lucide-react";
import { NavLink } from "react-router-dom";
import { Badge } from "../common/Badge";
import { StatusPill } from "../common/StatusPill";
import { BRAND_NAME, NAV_ITEMS, TEST_STATUS_LABEL, VERSION_LABEL } from "../../lib/constants";

export function TopNav() {
  return (
    <header
      style={{
        height: "var(--topnav-height)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 var(--space-5)",
        borderBottom: "1px solid var(--color-border)",
        background: "var(--color-surface-1)",
        flexShrink: 0,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-5)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
          <Cpu size={18} color="var(--color-brand)" />
          <span style={{ fontWeight: 600, fontSize: 14 }}>{BRAND_NAME}</span>
          <Badge variant="brand">{VERSION_LABEL}</Badge>
        </div>

        <nav style={{ display: "flex", gap: "var(--space-2)" }}>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              style={({ isActive }) => ({
                padding: "6px 12px",
                borderRadius: "var(--radius-sm)",
                fontSize: 13,
                fontWeight: 500,
                textDecoration: "none",
                color: isActive ? "var(--color-text-primary)" : "var(--color-text-secondary)",
                background: isActive ? "var(--color-surface-2)" : "transparent",
              })}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>

      <StatusPill label={TEST_STATUS_LABEL} status="success" />
    </header>
  );
}
