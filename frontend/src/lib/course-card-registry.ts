export type ManagedCourseCard = {
  key: string;
  title: string;
  description: string;
  duration: string;
  price: string;
  href: string;
  image: string;
  label: string;
};

export const MANAGED_COURSE_CARDS: ManagedCourseCard[] = [
  {
    key: "sql-excel",
    title: "SQL & Excel for Blockchain Data Analytics",
    description: "Six weeks of SQL, Excel, APIs and AI-assisted onchain research.",
    duration: "6 weeks",
    price: "$50",
    href: "/programs/cohort-9-sql-blockchain-data-analytics",
    image: "/SQL and Excel for Blockchain Analytics.png",
    label: "Registration open",
  },
  {
    key: "blockchain-data-engineering",
    title: "Blockchain Data Engineering",
    description: "Build production-minded blockchain data pipelines and infrastructure.",
    duration: "10 weeks",
    price: "$200",
    href: "/programs/blockchain-data-engineering",
    image: "/blockchain-data-engineering.png",
    label: "Join the waitlist",
  },
];
