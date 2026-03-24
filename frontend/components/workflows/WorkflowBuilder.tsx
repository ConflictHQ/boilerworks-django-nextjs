"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
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
import { PlusIcon, SaveIcon, TrashIcon } from "lucide-react";

type WorkflowState = {
  name: string;
  label: string;
  is_initial: boolean;
  is_final: boolean;
  color: string;
};

type WorkflowTransition = {
  from_state: string;
  to_state: string;
  label: string;
  conditions: unknown[];
  actions: unknown[];
};

type WorkflowBuilderProps = {
  states: WorkflowState[];
  transitions: WorkflowTransition[];
  onSave: (states: WorkflowState[], transitions: WorkflowTransition[]) => void;
};

// Custom node component for workflow states
function StateNode({ data }: { data: WorkflowState & { onDelete: () => void } }) {
  return (
    <div
      className="rounded-lg border-2 px-4 py-3 shadow-md"
      style={{ borderColor: data.color, backgroundColor: `${data.color}15`, minWidth: 150 }}
    >
      <Handle type="target" position={Position.Top} className="!bg-gray-400" />
      <div className="flex items-center justify-between gap-2">
        <div>
          <div className="font-medium">{data.label}</div>
          <div className="text-xs text-gray-500">{data.name}</div>
        </div>
        <div className="flex flex-col gap-1">
          {data.is_initial && <Badge variant="outline" className="text-[10px]">Start</Badge>}
          {data.is_final && <Badge variant="outline" className="text-[10px]">End</Badge>}
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-gray-400" />
    </div>
  );
}

const nodeTypes: NodeTypes = {
  stateNode: StateNode as unknown as NodeTypes[string],
};

const STATE_COLORS = ["#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#06b6d4", "#6b7280"];

export function WorkflowBuilder({ states: initialStates, transitions: initialTransitions, onSave }: WorkflowBuilderProps) {
  const [workflowStates, setWorkflowStates] = useState<WorkflowState[]>(initialStates);
  const [workflowTransitions, setWorkflowTransitions] = useState<WorkflowTransition[]>(initialTransitions);
  const [selectedEdge, setSelectedEdge] = useState<string | null>(null);

  // Convert states to react-flow nodes
  const initialNodes: Node[] = useMemo(
    () =>
      workflowStates.map((state, i) => ({
        id: state.name,
        type: "stateNode",
        position: { x: 250, y: i * 150 },
        data: { ...state, onDelete: () => removeState(state.name) },
      })),
    [],
  );

  // Convert transitions to react-flow edges
  const initialEdges: Edge[] = useMemo(
    () =>
      workflowTransitions.map((t, i) => ({
        id: `${t.from_state}-${t.to_state}`,
        source: t.from_state,
        target: t.to_state,
        label: t.label,
        animated: true,
        markerEnd: { type: MarkerType.ArrowClosed },
        style: { strokeWidth: 2 },
      })),
    [],
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (connection: Connection) => {
      const newEdge = {
        ...connection,
        id: `${connection.source}-${connection.target}`,
        label: `${connection.source} → ${connection.target}`,
        animated: true,
        markerEnd: { type: MarkerType.ArrowClosed },
        style: { strokeWidth: 2 },
      };
      setEdges((eds) => addEdge(newEdge, eds));

      // Add to transitions
      setWorkflowTransitions((prev) => [
        ...prev,
        {
          from_state: connection.source!,
          to_state: connection.target!,
          label: `${connection.source} → ${connection.target}`,
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
      is_initial: index === 0 && workflowStates.length === 0,
      is_final: false,
      color: STATE_COLORS[index % STATE_COLORS.length],
    };
    setWorkflowStates((prev) => [...prev, newState]);

    const newNode: Node = {
      id: name,
      type: "stateNode",
      position: { x: 250, y: index * 150 },
      data: { ...newState, onDelete: () => removeState(name) },
    };
    setNodes((nds) => [...nds, newNode]);
  };

  const removeState = (name: string) => {
    setWorkflowStates((prev) => prev.filter((s) => s.name !== name));
    setNodes((nds) => nds.filter((n) => n.id !== name));
    setEdges((eds) => eds.filter((e) => e.source !== name && e.target !== name));
    setWorkflowTransitions((prev) =>
      prev.filter((t) => t.from_state !== name && t.to_state !== name),
    );
  };

  const handleSave = () => {
    // Sync node positions don't matter for output — just states + transitions
    const currentTransitions = edges.map((e) => ({
      from_state: e.source,
      to_state: e.target,
      label: (e.label as string) || `${e.source} → ${e.target}`,
      conditions: workflowTransitions.find(
        (t) => t.from_state === e.source && t.to_state === e.target,
      )?.conditions ?? [],
      actions: workflowTransitions.find(
        (t) => t.from_state === e.source && t.to_state === e.target,
      )?.actions ?? [],
    }));
    onSave(workflowStates, currentTransitions);
  };

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

      <div className="h-[500px] rounded-lg border bg-white dark:bg-gray-950">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
          className="bg-dots-pattern"
        >
          <Controls />
          <Background />
          <MiniMap />
        </ReactFlow>
      </div>

      <div className="text-muted-foreground text-xs">
        Drag states to position. Draw connections by dragging from a state&apos;s bottom handle to another&apos;s top handle.
        {workflowStates.length > 0 && (
          <span> {workflowStates.length} states, {edges.length} transitions.</span>
        )}
      </div>
    </div>
  );
}
