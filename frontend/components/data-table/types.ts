export type FilterOption = {
  value: string;
  label: string;
};

export type FilterConfig = {
  id: string;
  label: string;
  type: "select" | "text";
  /** Required when type = "select" */
  options?: FilterOption[];
  /** Optional hint for type = "text" inputs */
  placeholder?: string;
};
