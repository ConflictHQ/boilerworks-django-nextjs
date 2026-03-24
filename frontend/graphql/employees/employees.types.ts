export type EmployeeAvatar = {
  publicPermanentUrl: string;
};

export type EmployeeProfile = {
  id: string;
  avatar: EmployeeAvatar | null;
  displayName: string;
  firstName: string;
  lastName: string;
};

export type EmployeeUser = {
  id: string;
  firstName: string;
  lastName: string;
  profile: EmployeeProfile | null;
  email: string;
  isActive: boolean;
};

export type Employee = {
  id: string;
  user: EmployeeUser;
};

export type EmployeeEdge = {
  cursor: string;
  node: Employee;
};

export type EmployeesQueryData = {
  employees: {
    edges: EmployeeEdge[];
    totalCount: number;
    pageInfo: {
      hasNextPage: boolean;
    };
  } | null;
};

export type EmployeesQueryVariables = {
  first?: number;
  offset?: number;
  search?: string;
  showDeactivated?: boolean;
  departments_Department_Name_Icontains?: string;
  departments_Position_Name_Icontains?: string;
};
