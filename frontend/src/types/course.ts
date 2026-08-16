export type Difficulty = "Beginner" | "Intermediate" | "Advanced";

export type Lesson = {
  id: string;
  title: string;
  duration: string;
  completed?: boolean;
  videoId?: string;
};

export type Module = {
  id: string;
  title: string;
  lessons: Lesson[];
  quiz?: { id: string; title: string };
};

export type Instructor = {
  name: string;
  title: string;
  avatar: string;
};

export type Course = {
  id: string;
  slug: string;
  title: string;
  description: string;
  longDescription: string;
  thumbnail: string;
  category: string;
  difficulty: Difficulty;
  duration: string;
  lessonsCount: number;
  price: number;
  currency: string;
  instructor: Instructor;
  rating: number;
  studentsCount: number;
  modules: Module[];
  skills: string[];
  requirements: string[];
  careerOutcomes?: string[];
  roleDescription?: string;
  enrolled?: boolean;
  progress?: number;
  /** When true, course is listed but not open for enrollment yet. */
  comingSoon?: boolean;
};

export type Certificate = {
  id: string;
  courseTitle: string;
  issuedAt: string;
  certificateId: string;
  recipientName?: string;
};

export type QuizQuestion = {
  id: string;
  question: string;
  options: string[];
  correctIndex: number;
};

export type Quiz = {
  id: string;
  title: string;
  passScore: number;
  questions: QuizQuestion[];
};
