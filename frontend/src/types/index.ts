export interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'student' | 'teacher';
  is_active: boolean;
  created_at: string;
}

export interface Assignment {
  id: number;
  title: string;
  description: string;
  attachments: string | null;
  due_date: string;
  teacher_id: number;
  student_id: number | null;
  created_at: string;
  updated_at: string | null;
}

export interface Submission {
  id: number;
  content: string | null;
  files: string | null;
  status: 'pending' | 'approved' | 'rejected';
  feedback: string | null;
  assignment_id: number;
  student_id: number;
  submitted_at: string;
  updated_at: string | null;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}