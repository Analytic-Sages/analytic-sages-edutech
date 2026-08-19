"use client";

import Link from "next/link";
import { use, useState } from "react";
import {
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Code2,
  Download,
  FileText,
  Maximize2,
  Menu,
  MessageSquare,
  Play,
  Sparkles,
  Zap,
} from "lucide-react";
import { notFound } from "next/navigation";
import { CodeSandbox } from "@/components/course/code-sandbox";
import { LessonSidebar } from "@/components/course/lesson-sidebar";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { EmptyState } from "@/components/shared/empty-state";
import { getCourseBySlug } from "@/lib/mock-data";

type Props = {
  params: Promise<{ slug: string; lessonId: string }>;
};

type DiscussionComment = {
  id: string;
  author: string;
  avatar: string;
  role?: string;
  timeAgo: string;
  content: string;
  likes: number;
};

const initialComments: DiscussionComment[] = [
  {
    id: "c1",
    author: "Dr. Alex Rivera",
    avatar: "AR",
    role: "Lead Instructor",
    timeAgo: "2 hours ago",
    content:
      "Welcome to this lesson! Make sure to test your SQL query in the interactive sandbox tab below. Pay special attention to how gas prices spike during high volatility events.",
    likes: 12,
  },
  {
    id: "c2",
    author: "Sarah Chen",
    avatar: "SC",
    timeAgo: "1 hour ago",
    content:
      "Loved the breakdown of internal transactions versus standard ETH transfers! The sandbox example really helped clarify Etherscan trace outputs.",
    likes: 4,
  },
];

export function MockCoursePlayer({ params }: Props) {
  const { slug, lessonId } = use(params);
  const course = getCourseBySlug(slug);

  const [completed, setCompleted] = useState(false);
  const [speed, setSpeed] = useState("1x");
  const [focusMode, setFocusMode] = useState(false);
  const [personalNotes, setPersonalNotes] = useState("");
  const [notesSaved, setNotesSaved] = useState(false);
  const [comments, setComments] = useState<DiscussionComment[]>(initialComments);
  const [newComment, setNewComment] = useState("");

  if (!course) notFound();

  const allLessons = course.modules.flatMap((m) => m.lessons);
  const currentIndex = allLessons.findIndex((l) => l.id === lessonId);
  const resolvedIndex = currentIndex >= 0 ? currentIndex : 0;
  const currentLesson = allLessons[resolvedIndex];
  const prevLesson = resolvedIndex > 0 ? allLessons[resolvedIndex - 1] : undefined;
  const nextLesson = allLessons[resolvedIndex + 1];

  if (!currentLesson) {
    return (
      <div className="p-6 sm:p-8">
        <EmptyState
          icon={<BookOpen className="size-5" />}
          title="Curriculum coming soon"
          description="This course is unlocked, but lessons aren’t available in the player yet. Check the course page for details while we finish the content."
          action={{ label: "Back to course", href: `/courses/${slug}` }}
        />
      </div>
    );
  }

  const handleSaveNotes = () => {
    setNotesSaved(true);
    setTimeout(() => setNotesSaved(false), 2000);
  };

  const handleAddComment = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    setComments([
      {
        id: `c_${Date.now()}`,
        author: "You (Student)",
        avatar: "YO",
        timeAgo: "Just now",
        content: newComment.trim(),
        likes: 0,
      },
      ...comments,
    ]);
    setNewComment("");
  };

  return (
    <div className="-m-4 flex min-h-[calc(100vh-4rem)] flex-col lg:-m-8 lg:flex-row">
      {/* Mobile module drawer */}
      <div className="border-b p-4 lg:hidden">
        <Sheet>
          <SheetTrigger
            className="inline-flex h-7 items-center gap-2 rounded-[min(var(--radius-md),12px)] border border-border bg-background px-2.5 text-[0.8rem] font-medium hover:bg-muted lg:hidden"
          >
            <Menu className="size-4" />
            Course Content
          </SheetTrigger>
          <SheetContent side="left" className="w-80 overflow-y-auto p-4">
            <LessonSidebar
              courseSlug={slug}
              modules={course.modules}
              currentLessonId={currentLesson.id}
            />
          </SheetContent>
        </Sheet>
      </div>

      {/* Desktop sidebar */}
      {!focusMode && (
        <aside className="hidden w-80 shrink-0 overflow-y-auto border-r bg-brand-surface p-4 lg:block">
          <div className="mb-4">
            <Link
              href={`/courses/${slug}`}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              ← Back to course
            </Link>
            <h2 className="mt-2 font-heading font-semibold line-clamp-2">{course.title}</h2>
            <Progress value={course.progress ?? 0} className="mt-3 h-1.5" />
            <p className="mt-1 text-xs text-muted-foreground">{course.progress}% complete</p>
          </div>
          <LessonSidebar
            courseSlug={slug}
            modules={course.modules}
            currentLessonId={currentLesson.id}
          />
        </aside>
      )}

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col">
        {/* Custom Bunny Video Player UI */}
        <div className="relative aspect-video w-full overflow-hidden bg-slate-950 shadow-elevated">
          <div className="flex h-full flex-col items-center justify-center bg-gradient-to-br from-slate-950 via-brand-navy/30 to-slate-950 p-6 text-center">
            <div className="group relative cursor-pointer">
              <div className="mx-auto mb-4 flex size-20 items-center justify-center rounded-full bg-brand-orange text-white shadow-float transition-transform group-hover:scale-110">
                <Play className="ml-1 size-8 fill-current" />
              </div>
            </div>
            <h3 className="font-heading text-lg font-bold text-white sm:text-xl">
              {currentLesson.title}
            </h3>
            <p className="mt-1 text-xs text-slate-400 font-mono">
              Bunny Stream HD Player • {currentLesson.duration}
            </p>
          </div>

          {/* Video Control Bar */}
          <div className="absolute bottom-0 inset-x-0 flex items-center justify-between border-t border-slate-800/80 bg-slate-900/90 px-4 py-2.5 backdrop-blur-md text-xs text-slate-200">
            <div className="flex items-center gap-3">
              <button className="flex items-center gap-1 font-mono font-medium hover:text-brand-orange">
                <Play className="size-3.5 fill-current" /> Play
              </button>
              <span className="text-slate-600">|</span>
              <span className="font-mono text-slate-400">03:45 / {currentLesson.duration}</span>
            </div>

            <div className="flex items-center gap-3">
              {/* Playback Speed Pill */}
              <div className="flex items-center gap-1 rounded-md bg-slate-800 p-0.5 font-mono text-[0.7rem]">
                {["1x", "1.25x", "1.5x", "2x"].map((sp) => (
                  <button
                    key={sp}
                    onClick={() => setSpeed(sp)}
                    className={`rounded px-1.5 py-0.5 font-semibold ${
                      speed === sp ? "bg-brand-orange text-white" : "text-slate-400 hover:text-white"
                    }`}
                  >
                    {sp}
                  </button>
                ))}
              </div>

              {/* Theater/Focus Mode */}
              <button
                onClick={() => setFocusMode(!focusMode)}
                title="Toggle Focus Mode"
                className="hidden sm:flex items-center gap-1 rounded bg-slate-800 px-2 py-1 hover:bg-slate-700"
              >
                <Maximize2 className="size-3" />
                <span>{focusMode ? "Exit Focus" : "Focus Mode"}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="border-b bg-background p-4 sm:px-6 lg:px-8">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-[0.7rem] uppercase">
                  Lesson {resolvedIndex + 1} of {allLessons.length}
                </Badge>
                <span className="text-xs text-muted-foreground">{currentLesson.duration}</span>
              </div>
              <h1 className="mt-1 font-heading text-xl font-bold sm:text-2xl">{currentLesson.title}</h1>
            </div>

            <div className="flex flex-wrap gap-2.5">
              <Button
                variant={completed ? "secondary" : "default"}
                className={completed ? "bg-emerald-500/10 text-emerald-600 border border-emerald-500/30 dark:text-emerald-400" : "bg-brand-navy text-white hover:bg-brand-navy/90"}
                onClick={() => setCompleted(!completed)}
              >
                {completed ? "✓ Completed" : "Mark Complete"}
              </Button>
              {prevLesson && (
                <ButtonLink href={`/courses/${slug}/learn/${prevLesson.id}`} variant="outline">
                  <ChevronLeft className="size-4" />
                  Previous
                </ButtonLink>
              )}
              {nextLesson && (
                <ButtonLink
                  href={`/courses/${slug}/learn/${nextLesson.id}`}
                  className="bg-brand-orange text-white hover:bg-brand-orange/90"
                >
                  Next Lesson
                  <ChevronRight className="size-4" />
                </ButtonLink>
              )}
            </div>
          </div>
        </div>

        {/* Tabbed Interactive Workspace */}
        <div className="flex-1 p-4 sm:p-6 lg:p-8">
          <Tabs defaultValue="sandbox" className="w-full">
            <TabsList className="mb-6 flex w-full flex-wrap justify-start border-b bg-transparent p-0">
              <TabsTrigger value="sandbox" className="gap-2 font-bold data-[state=active]:bg-brand-navy data-[state=active]:text-white">
                <Code2 className="size-4" />
                Interactive Code Sandbox
              </TabsTrigger>
              <TabsTrigger value="overview" className="gap-2 font-bold data-[state=active]:bg-brand-navy data-[state=active]:text-white">
                <BookOpen className="size-4" />
                Overview & Personal Notes
              </TabsTrigger>
              <TabsTrigger value="qa" className="gap-2 font-bold data-[state=active]:bg-brand-navy data-[state=active]:text-white">
                <MessageSquare className="size-4" />
                Q&A Discussion ({comments.length})
              </TabsTrigger>
              <TabsTrigger value="resources" className="gap-2 font-bold data-[state=active]:bg-brand-navy data-[state=active]:text-white">
                <Download className="size-4" />
                Resources
              </TabsTrigger>
            </TabsList>

            {/* Code Sandbox Tab */}
            <TabsContent value="sandbox" className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-heading text-lg font-bold">Onchain Analytics Lab</h3>
                  <p className="text-xs text-muted-foreground">
                    Test queries and live python pipelines directly within your browser.
                  </p>
                </div>
                <Badge variant="outline" className="gap-1 text-emerald-600 dark:text-emerald-400">
                  <Sparkles className="size-3" /> Hands-on Practice
                </Badge>
              </div>
              <CodeSandbox />
            </TabsContent>

            {/* Overview & Personal Notes Tab */}
            <TabsContent value="overview" className="grid gap-6 lg:grid-cols-2">
              <Card className="shadow-card">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base font-heading">
                    <FileText className="size-4 text-brand-orange" />
                    Lesson Objectives & Summary
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm text-muted-foreground leading-relaxed">
                  <p>
                    In this lesson, you&apos;ll master how to query, parse, and analyze blockchain transactions using Etherscan ABI data and Dune SQL tables.
                  </p>
                  <ul className="list-disc space-y-1.5 pl-5">
                    <li>Differentiating between consensus traces and internal transactions.</li>
                    <li>Calculating precise USD volume from raw WEI values.</li>
                    <li>Filtering gas spike anomalies during DEX volatility events.</li>
                  </ul>
                </CardContent>
              </Card>

              {/* Personal Notes Card */}
              <Card className="shadow-card">
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base font-heading">
                    <Zap className="size-4 text-brand-navy" />
                    My Timestamped Notes
                  </CardTitle>
                  {notesSaved && (
                    <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400">
                      ✓ Saved!
                    </span>
                  )}
                </CardHeader>
                <CardContent className="space-y-3">
                  <Textarea
                    placeholder="Write key takeaways or timestamp notes here (e.g. 02:45 - gas price formula)..."
                    className="min-h-[120px] text-xs font-mono"
                    value={personalNotes}
                    onChange={(e) => setPersonalNotes(e.target.value)}
                  />
                  <div className="flex justify-end">
                    <Button size="sm" onClick={handleSaveNotes} className="bg-brand-navy text-white hover:bg-brand-navy/90">
                      Save Notes
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Q&A Discussion Tab */}
            <TabsContent value="qa" className="space-y-6">
              <Card className="shadow-card p-4">
                <form onSubmit={handleAddComment} className="space-y-3">
                  <h4 className="font-heading text-sm font-bold">Ask a question or share feedback</h4>
                  <Textarea
                    placeholder="Have a question about this lesson's query or code?"
                    className="min-h-[80px] text-xs"
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                  />
                  <div className="flex justify-end">
                    <Button type="submit" size="sm" className="bg-brand-orange text-white hover:bg-brand-orange/90">
                      Post Comment
                    </Button>
                  </div>
                </form>
              </Card>

              <div className="space-y-4">
                {comments.map((comment) => (
                  <Card key={comment.id} className="p-4 shadow-card">
                    <div className="flex items-start gap-3">
                      <Avatar className="size-8 border">
                        <AvatarFallback className="bg-brand-navy text-xs text-white">
                          {comment.avatar}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm">{comment.author}</span>
                          {comment.role && (
                            <Badge variant="secondary" className="text-[0.65rem] bg-brand-orange/10 text-brand-orange font-semibold">
                              {comment.role}
                            </Badge>
                          )}
                          <span className="text-xs text-muted-foreground">{comment.timeAgo}</span>
                        </div>
                        <p className="mt-2 text-xs leading-relaxed text-foreground">{comment.content}</p>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </TabsContent>

            {/* Resources Tab */}
            <TabsContent value="resources">
              <Card className="shadow-card">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base font-heading">
                    <Download className="size-4 text-brand-orange" />
                    Downloadable Lesson Assets
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {[
                    "Etherscan_Transaction_Parser.sql",
                    "Blockchain_Data_Engineering_Slides.pdf",
                    "DEX_Liquidity_Sample_Dataset.csv",
                  ].map((file) => (
                    <div
                      key={file}
                      className="flex items-center justify-between rounded-xl border p-3 text-xs hover:bg-muted transition-colors"
                    >
                      <span className="font-mono font-medium">{file}</span>
                      <Button size="sm" variant="outline" className="gap-1.5 text-xs">
                        <Download className="size-3.5 text-brand-navy" /> Download
                      </Button>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
