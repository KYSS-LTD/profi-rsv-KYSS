import { apiClient } from './client';

export type WorkloadSummary = {
  active_tasks: number;
  overdue_tasks: number;
  blocked_tasks: number;
  completed_tasks: number;
  workload_score: number;
};

export type OrgMapNode = {
  id: string;
  user_id?: string | null;
  full_name: string;
  position?: string | null;
  role: string;
  manager_id?: string | null;
  direct_reports: number;
  indirect_reports: number;
  responsibilities: string[];
  active_delegations: number;
  workload: WorkloadSummary;
  requires_attention: boolean;
  children: OrgMapNode[];
};

export type AttentionItem = {
  type: string;
  title: string;
  count: number;
  severity: 'critical' | 'warning' | 'info' | string;
  explanation: string;
};

export type OrgMapResponse = {
  nodes: OrgMapNode[];
  attention: AttentionItem[];
  health: { score: number; causes: string[] };
  role_model: string[];
  permission_scopes: string[];
};

export function getOrganizationMap() {
  return apiClient<OrgMapResponse>('/v2/org-os/map');
}
