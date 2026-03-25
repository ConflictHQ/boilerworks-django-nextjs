"use client";

import { useCallback, useMemo, useState } from "react";
import {
  ReactFlow,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  MiniMap,
  type Connection,
  type Edge,
  type Node,
  type NodeTypes,
  MarkerType,
  Handle,
  Position,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { PlusIcon, SaveIcon, TrashIcon, XIcon } from "lucide-react";
import { TagInput } from "@/components/ui/tag-input";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type Condition = {
  type: string;
  role?: string;
  field?: string;
  value?: unknown;
  values?: unknown[];
};

type Action = {
  type: string;
  user?: string;
  to?: string;
  subject?: string;
  message?: string;
  url?: string;
  field?: string;
  value?: unknown;
};

type WorkflowState = {
  name: string;
  label: string;
  is_initial: boolean;
  is_final: boolean;
  color: string;
  form_slug?: string;
  assigned_role?: string;
};

type WorkflowTransition = {
  from_state: string;
  to_state: string;
  label: string;
  conditions: Condition[];
  actions: Action[];
};

type FormOption = { slug: string; name: string };

type WorkflowBuilderProps = {
  states: WorkflowState[];
  transitions: WorkflowTransition[];
  onSave: (states: WorkflowState[], transitions: WorkflowTransition[]) => void;
  availableForms?: FormOption[];
};

// ---------------------------------------------------------------------------
// Condition / Action definitions
// ---------------------------------------------------------------------------

const CONDITION_TYPES = [
  { value: "user_has_role", label: "User has role" },
  { value: "field_equals", label: "Field equals value" },
  { value: "field_in", label: "Field in list" },
  { value: "is_authenticated", label: "User is authenticated" },
  { value: "is_superuser", label: "User is superuser" },
];

const ACTION_TYPES = [
  { value: "notify_user", label: "Notify user" },
  { value: "send_email", label: "Send email" },
  { value: "call_webhook", label: "Call webhook" },
  { value: "update_field", label: "Update field" },
];

const USER_REFS = [
  { value: "current_user", label: "Current user (who transitioned)" },
  { value: "form_owner", label: "Form owner (created_by)" },
  { value: "submitter", label: "Submitter (submitted_by)" },
];

// ---------------------------------------------------------------------------
// StateNode component
// ---------------------------------------------------------------------------

function StateNode({
  data,
  selected,
}: {
  data: WorkflowState & { onSelect: () => void; onDelete: () => void };
  selected?: boolean;
}) {
  return (
    <div
      className="cursor-pointer rounded-lg border-2 px-4 py-3 shadow-md transition-shadow hover:shadow-lg"
      style={{
        borderColor: selected ? "#3b82f6" : data.color,
        backgroundColor: `${data.color}15`,
        minWidth: 150,
        boxShadow: selected ? "0 0 0 2px rgba(59,130,246,0.3)" : undefined,
      }}
      onClick={(e) => {
        e.stopPropagation();
        data.onSelect();
      }}
    >
      <Handle type="target" position={Position.Top} className="!bg-gray-400" />
      <div className="flex items-center justify-between gap-2">
        <div>
          <div className="font-medium">{data.label}</div>
          <div className="text-xs text-gray-500">{data.name}</div>
          {data.form_slug && (
            <div className="mt-1 text-[10px] text-blue-500">Form: {data.form_slug}</div>
          )}
          {data.assigned_role && (
            <div className="text-[10px] text-purple-500">Role: {data.assigned_role}</div>
          )}
        </div>
        <div className="flex flex-col gap-1">
          {data.is_initial && (
            <Badge variant="outline" className="text-[10px]">
              Start
            </Badge>
          )}
          {data.is_final && (
            <Badge variant="outline" className="text-[10px]">
              End
            </Badge>
          )}
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-gray-400" />
    </div>
  );
}

const nodeTypes: NodeTypes = {
  stateNode: StateNode as unknown as NodeTypes[string],
};

const STATE_COLORS = [
  "#3b82f6",
  "#22c55e",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#ec4899",
  "#06b6d4",
  "#6b7280",
];

// ---------------------------------------------------------------------------
// Condition editor
// ---------------------------------------------------------------------------

function ConditionEditor({
  conditions,
  onChange,
}: {
  conditions: Condition[];
  onChange: (c: Condition[]) => void;
}) {
  const addCondition = () => onChange([...conditions, { type: "user_has_role", role: "" }]);
  const removeCondition = (i: number) => onChange(conditions.filter((_, idx) => idx !== i));
  const updateCondition = (i: number, updates: Partial<Condition>) =>
    onChange(conditions.map((c, idx) => (idx === i ? { ...c, ...updates } : c)));

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <Label className="text-xs">Conditions</Label>
        <Button variant="ghost" size="sm" className="h-6 px-2 text-xs" onClick={addCondition}>
          <PlusIcon className="mr-1 h-3 w-3" /> Add
        </Button>
      </div>
      {conditions.length === 0 && (
        <p className="text-muted-foreground text-[11px]">
          No conditions — transition is always available
        </p>
      )}
      {conditions.map((cond, i) => (
        <div
          key={i}
          className="flex flex-col gap-1.5 rounded border bg-gray-50 p-2 dark:bg-gray-900"
        >
          <div className="flex items-center gap-1">
            <Select
              value={cond.type}
              onValueChange={(v) => updateCondition(i, { type: v })}
            >
              <SelectTrigger className="h-7 flex-1 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CONDITION_TYPES.map((ct) => (
                  <SelectItem key={ct.value} value={ct.value}>
                    {ct.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <button
              type="button"
              className="rounded p-0.5 text-red-400 hover:text-red-600"
              onClick={() => removeCondition(i)}
            >
              <XIcon className="h-3 w-3" />
            </button>
          </div>
          {cond.type === "user_has_role" && (
            <TagInput
              value={cond.role ? [cond.role] : []}
              onChange={(tags) => updateCondition(i, { role: tags[tags.length - 1] || "" })}
              placeholder="Type role name and press Enter"
            />
          )}
          {cond.type === "field_equals" && (
            <div className="flex gap-1">
              <Input
                className="h-7 flex-1 text-xs"
                placeholder="Field name"
                value={cond.field || ""}
                onChange={(e) => updateCondition(i, { field: e.target.value })}
              />
              <Input
                className="h-7 flex-1 text-xs"
                placeholder="Value"
                value={String(cond.value ?? "")}
                onChange={(e) => updateCondition(i, { value: e.target.value })}
              />
            </div>
          )}
          {cond.type === "field_in" && (
            <div className="flex flex-col gap-1">
              <Input
                className="h-7 text-xs"
                placeholder="Field name"
                value={cond.field || ""}
                onChange={(e) => updateCondition(i, { field: e.target.value })}
              />
              <TagInput
                value={Array.isArray(cond.values) ? cond.values.map(String) : []}
                onChange={(tags) => updateCondition(i, { values: tags })}
                placeholder="Type value and press Enter"
              />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Action editor
// ---------------------------------------------------------------------------

function ActionEditor({
  actions,
  onChange,
}: {
  actions: Action[];
  onChange: (a: Action[]) => void;
}) {
  const addAction = () =>
    onChange([
      ...actions,
      { type: "notify_user", user: "current_user", subject: "", message: "" },
    ]);
  const removeAction = (i: number) => onChange(actions.filter((_, idx) => idx !== i));
  const updateAction = (i: number, updates: Partial<Action>) =>
    onChange(actions.map((a, idx) => (idx === i ? { ...a, ...updates } : a)));

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <Label className="text-xs">Actions</Label>
        <Button variant="ghost" size="sm" className="h-6 px-2 text-xs" onClick={addAction}>
          <PlusIcon className="mr-1 h-3 w-3" /> Add
        </Button>
      </div>
      {actions.length === 0 && (
        <p className="text-muted-foreground text-[11px]">
          No actions — nothing happens on transition
        </p>
      )}
      {actions.map((action, i) => (
        <div
          key={i}
          className="flex flex-col gap-1.5 rounded border bg-gray-50 p-2 dark:bg-gray-900"
        >
          <div className="flex items-center gap-1">
            <Select
              value={action.type}
              onValueChange={(v) => updateAction(i, { type: v })}
            >
              <SelectTrigger className="h-7 flex-1 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ACTION_TYPES.map((at) => (
                  <SelectItem key={at.value} value={at.value}>
                    {at.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <button
              type="button"
              className="rounded p-0.5 text-red-400 hover:text-red-600"
              onClick={() => removeAction(i)}
            >
              <XIcon className="h-3 w-3" />
            </button>
          </div>

          {(action.type === "notify_user" || action.type === "send_email") && (
            <>
              <Select
                value={action.user || action.to || "current_user"}
                onValueChange={(v) => updateAction(i, { user: v, to: v })}
              >
                <SelectTrigger className="h-7 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {USER_REFS.map((ur) => (
                    <SelectItem key={ur.value} value={ur.value}>
                      {ur.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Input
                className="h-7 text-xs"
                placeholder="Subject"
                value={action.subject || ""}
                onChange={(e) => updateAction(i, { subject: e.target.value })}
              />
              <Input
                className="h-7 text-xs"
                placeholder="Message"
                value={action.message || ""}
                onChange={(e) => updateAction(i, { message: e.target.value })}
              />
            </>
          )}

          {action.type === "call_webhook" && (
            <Input
              className="h-7 text-xs"
              placeholder="https://example.com/webhook"
              value={action.url || ""}
              onChange={(e) => updateAction(i, { url: e.target.value })}
            />
          )}

          {action.type === "update_field" && (
            <div className="flex gap-1">
              <Input
                className="h-7 flex-1 text-xs"
                placeholder="Field name"
                value={action.field || ""}
                onChange={(e) => updateAction(i, { field: e.target.value })}
              />
              <Input
                className="h-7 flex-1 text-xs"
                placeholder="Value"
                value={String(action.value ?? "")}
                onChange={(e) => updateAction(i, { value: e.target.value })}
              />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main builder
// ---------------------------------------------------------------------------

export function WorkflowBuilder({
  states: initialStates,
  transitions: initialTransitions,
  onSave,
  availableForms = [],
}: WorkflowBuilderProps) {
  const [workflowStates, setWorkflowStates] = useState<WorkflowState[]>(initialStates);
  const [workflowTransitions, setWorkflowTransitions] =
    useState<WorkflowTransition[]>(initialTransitions);
  const [selectedStateName, setSelectedStateName] = useState<string | null>(null);
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);

  const buildNodes = useCallback(
    (states: WorkflowState[], existingNodes: Node[]): Node[] => {
      return states.map((state, i) => {
        const existing = existingNodes.find((n) => n.id === state.name);
        return {
          id: state.name,
          type: "stateNode",
          position: existing?.position ?? { x: 250, y: i * 150 },
          selected: state.name === selectedStateName,
          data: {
            ...state,
            onSelect: () => setSelectedStateName(state.name),
            onDelete: () => removeState(state.name),
          },
        };
      });
    },
    [selectedStateName],
  );

  const initialNodes: Node[] = useMemo(
    () => buildNodes(initialStates, []),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  const initialEdges: Edge[] = useMemo(
    () =>
      initialTransitions.map((t) => ({
        id: `${t.from_state}-${t.to_state}`,
        source: t.from_state,
        target: t.to_state,
        label: t.label,
        animated: true,
        markerEnd: { type: MarkerType.ArrowClosed },
        style: { strokeWidth: 2 },
      })),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const refreshNodes = useCallback(
    (states: WorkflowState[]) => {
      setNodes((currentNodes) => buildNodes(states, currentNodes));
    },
    [buildNodes, setNodes],
  );

  const onConnect = useCallback(
    (connection: Connection) => {
      const label = `${connection.source} → ${connection.target}`;
      const newEdge = {
        ...connection,
        id: `${connection.source}-${connection.target}`,
        label,
        animated: true,
        markerEnd: { type: MarkerType.ArrowClosed },
        style: { strokeWidth: 2 },
      };
      setEdges((eds) => addEdge(newEdge, eds) as typeof eds);
      setWorkflowTransitions((prev) => [
        ...prev,
        {
          from_state: connection.source!,
          to_state: connection.target!,
          label,
          conditions: [],
          actions: [],
        },
      ]);
    },
    [setEdges],
  );

  const addState = () => {
    const index = workflowStates.length;
    const name = `state_${index + 1}`;
    const newState: WorkflowState = {
      name,
      label: `State ${index + 1}`,
      is_initial: index === 0,
      is_final: false,
      color: STATE_COLORS[index % STATE_COLORS.length],
    };
    const updated = [...workflowStates, newState];
    setWorkflowStates(updated);
    setSelectedStateName(name);
    refreshNodes(updated);
  };

  const removeState = (name: string) => {
    const updated = workflowStates.filter((s) => s.name !== name);
    setWorkflowStates(updated);
    setEdges((eds) => eds.filter((e) => e.source !== name && e.target !== name));
    setWorkflowTransitions((prev) =>
      prev.filter((t) => t.from_state !== name && t.to_state !== name),
    );
    if (selectedStateName === name) setSelectedStateName(null);
    refreshNodes(updated);
  };

  const updateState = (name: string, updates: Partial<WorkflowState>) => {
    const updated = workflowStates.map((s) => {
      if (s.name !== name) {
        if (updates.is_initial) return { ...s, is_initial: false };
        return s;
      }
      return { ...s, ...updates };
    });
    setWorkflowStates(updated);
    refreshNodes(updated);
  };

  const removeEdge = (edgeId: string) => {
    const edge = edges.find((e) => e.id === edgeId);
    if (!edge) return;
    setEdges((eds) => eds.filter((e) => e.id !== edgeId));
    setWorkflowTransitions((prev) =>
      prev.filter((t) => !(t.from_state === edge.source && t.to_state === edge.target)),
    );
    setSelectedEdgeId(null);
  };

  const updateTransitionLabel = (edgeId: string, label: string) => {
    setEdges((eds) => eds.map((e) => (e.id === edgeId ? { ...e, label } : e)));
    const edge = edges.find((e) => e.id === edgeId);
    if (edge) {
      setWorkflowTransitions((prev) =>
        prev.map((t) =>
          t.from_state === edge.source && t.to_state === edge.target ? { ...t, label } : t,
        ),
      );
    }
  };

  const updateTransitionConditions = (edgeId: string, conditions: Condition[]) => {
    const edge = edges.find((e) => e.id === edgeId);
    if (edge) {
      setWorkflowTransitions((prev) =>
        prev.map((t) =>
          t.from_state === edge.source && t.to_state === edge.target ? { ...t, conditions } : t,
        ),
      );
    }
  };

  const updateTransitionActions = (edgeId: string, actions: Action[]) => {
    const edge = edges.find((e) => e.id === edgeId);
    if (edge) {
      setWorkflowTransitions((prev) =>
        prev.map((t) =>
          t.from_state === edge.source && t.to_state === edge.target ? { ...t, actions } : t,
        ),
      );
    }
  };

  const handleSave = () => {
    const currentTransitions = edges.map((e) => {
      const wt = workflowTransitions.find(
        (t) => t.from_state === e.source && t.to_state === e.target,
      );
      return {
        from_state: e.source,
        to_state: e.target,
        label: (e.label as string) || `${e.source} → ${e.target}`,
        conditions: wt?.conditions ?? [],
        actions: wt?.actions ?? [],
      };
    });
    onSave(workflowStates, currentTransitions);
  };

  const selectedState = workflowStates.find((s) => s.name === selectedStateName);
  const selectedEdge = edges.find((e) => e.id === selectedEdgeId);
  const selectedTransition = selectedEdge
    ? workflowTransitions.find(
        (t) => t.from_state === selectedEdge.source && t.to_state === selectedEdge.target,
      )
    : null;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={addState}>
            <PlusIcon className="mr-1 h-3 w-3" /> Add State
          </Button>
        </div>
        <Button size="sm" onClick={handleSave}>
          <SaveIcon className="mr-1 h-3 w-3" /> Save Workflow
        </Button>
      </div>

      <div className="flex gap-4">
        {/* Canvas */}
        <div className="h-[500px] flex-1 rounded-lg border bg-white dark:bg-gray-950">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onEdgeClick={(_, edge) => {
              setSelectedEdgeId(edge.id);
              setSelectedStateName(null);
            }}
            onPaneClick={() => {
              setSelectedStateName(null);
              setSelectedEdgeId(null);
            }}
            nodeTypes={nodeTypes}
            fitView
            className="bg-dots-pattern"
          >
            <Controls />
            <Background />
            <MiniMap />
          </ReactFlow>
        </div>

        {/* Properties panel */}
        {(selectedState || selectedEdge) && (
          <div className="w-80 shrink-0 overflow-y-auto rounded-lg border bg-white p-4 dark:bg-gray-950"
               style={{ maxHeight: 500 }}>
            {/* ---- STATE PANEL ---- */}
            {selectedState && (
              <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold">Edit State</h3>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0"
                    onClick={() => setSelectedStateName(null)}
                  >
                    <XIcon className="h-3 w-3" />
                  </Button>
                </div>
                <Separator />

                <div className="flex flex-col gap-1.5">
                  <Label className="text-xs">Label</Label>
                  <Input
                    value={selectedState.label}
                    onChange={(e) => updateState(selectedState.name, { label: e.target.value })}
                    placeholder="Display name"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <Label className="text-xs">Name (slug)</Label>
                  <Input
                    value={selectedState.name}
                    disabled
                    className="bg-muted text-muted-foreground text-xs"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <Label className="text-xs">Color</Label>
                  <div className="flex gap-2">
                    {STATE_COLORS.map((c) => (
                      <button
                        key={c}
                        type="button"
                        className="h-6 w-6 rounded-full border-2 transition-transform hover:scale-110"
                        style={{
                          backgroundColor: c,
                          borderColor: selectedState.color === c ? "#000" : "transparent",
                        }}
                        onClick={() => updateState(selectedState.name, { color: c })}
                      />
                    ))}
                  </div>
                </div>

                <Separator />

                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={selectedState.is_initial}
                    onChange={(e) =>
                      updateState(selectedState.name, { is_initial: e.target.checked })
                    }
                    className="h-4 w-4 rounded"
                  />
                  <span className="text-sm">Initial state (start)</span>
                </label>

                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={selectedState.is_final}
                    onChange={(e) =>
                      updateState(selectedState.name, { is_final: e.target.checked })
                    }
                    className="h-4 w-4 rounded"
                  />
                  <span className="text-sm">Final state (end)</span>
                </label>

                <Separator />

                {/* Form picker */}
                <div className="flex flex-col gap-1.5">
                  <Label className="text-xs">Attached Form</Label>
                  <Select
                    value={selectedState.form_slug || "__none__"}
                    onValueChange={(v) =>
                      updateState(selectedState.name, {
                        form_slug: v === "__none__" ? undefined : v,
                      })
                    }
                  >
                    <SelectTrigger className="h-8 text-xs">
                      <SelectValue placeholder="No form" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__none__">No form</SelectItem>
                      {availableForms.map((f) => (
                        <SelectItem key={f.slug} value={f.slug}>
                          {f.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-muted-foreground text-[10px]">
                    Form required at this step before transitioning
                  </p>
                </div>

                {/* Assigned role */}
                <div className="flex flex-col gap-1.5">
                  <Label className="text-xs">Assigned Role</Label>
                  <TagInput
                    value={selectedState.assigned_role ? [selectedState.assigned_role] : []}
                    onChange={(tags) =>
                      updateState(selectedState.name, {
                        assigned_role: tags[tags.length - 1] || undefined,
                      })
                    }
                    placeholder="Type role and press Enter"
                  />
                  <p className="text-muted-foreground text-[10px]">
                    Users with this role are responsible for this step
                  </p>
                </div>

                <Separator />

                <Button
                  variant="outline"
                  size="sm"
                  className="text-red-600 hover:bg-red-50 hover:text-red-700"
                  onClick={() => removeState(selectedState.name)}
                >
                  <TrashIcon className="mr-1 h-3 w-3" /> Delete State
                </Button>
              </div>
            )}

            {/* ---- TRANSITION PANEL ---- */}
            {selectedEdge && (
              <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold">Edit Transition</h3>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0"
                    onClick={() => setSelectedEdgeId(null)}
                  >
                    <XIcon className="h-3 w-3" />
                  </Button>
                </div>
                <Separator />

                <div className="flex flex-col gap-1.5">
                  <Label className="text-xs">Label</Label>
                  <Input
                    value={(selectedEdge.label as string) || ""}
                    onChange={(e) => updateTransitionLabel(selectedEdge.id, e.target.value)}
                    placeholder="Transition label"
                  />
                </div>

                <div className="text-muted-foreground text-xs">
                  <span className="font-medium">{selectedEdge.source}</span>
                  {" → "}
                  <span className="font-medium">{selectedEdge.target}</span>
                </div>

                <Separator />

                {/* Conditions */}
                <ConditionEditor
                  conditions={selectedTransition?.conditions ?? []}
                  onChange={(c) => updateTransitionConditions(selectedEdge.id, c)}
                />

                <Separator />

                {/* Actions */}
                <ActionEditor
                  actions={selectedTransition?.actions ?? []}
                  onChange={(a) => updateTransitionActions(selectedEdge.id, a)}
                />

                <Separator />

                <Button
                  variant="outline"
                  size="sm"
                  className="text-red-600 hover:bg-red-50 hover:text-red-700"
                  onClick={() => removeEdge(selectedEdge.id)}
                >
                  <TrashIcon className="mr-1 h-3 w-3" /> Delete Transition
                </Button>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="text-muted-foreground text-xs">
        Click a state or transition to edit. Draw connections by dragging from a state&apos;s bottom
        handle to another&apos;s top handle.
        {workflowStates.length > 0 && (
          <span>
            {" "}
            {workflowStates.length} states, {edges.length} transitions.
          </span>
        )}
      </div>
    </div>
  );
}
