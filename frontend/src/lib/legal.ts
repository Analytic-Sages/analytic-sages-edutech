export type LegalBlock =
  | { type: "p"; text: string }
  | { type: "h3"; text: string }
  | { type: "ul"; items: string[] };

export type LegalSection = {
  heading: string;
  blocks: LegalBlock[];
};

export type LegalDocumentContent = {
  title: string;
  slug: "/privacy" | "/terms";
  updated: string;
  description: string;
  intro: string[];
  sections: LegalSection[];
};

export const LEGAL_UPDATED = "19 August 2026";

export const privacyPolicy: LegalDocumentContent = {
  title: "Privacy Policy",
  slug: "/privacy",
  updated: LEGAL_UPDATED,
  description:
    "How Analytic Sages collects, uses, stores, and protects personal information on analyticsages.io.",
  intro: [
    'Analytic Sages ("Analytic Sages", "we", "our", or "us") is committed to protecting your privacy and handling your personal information responsibly.',
    "This Privacy Policy explains how we collect, use, store, and protect information when you visit analyticsages.io, create an account, enroll in our programs or courses, participate in our classrooms, interact with our content, or otherwise use our services.",
    "Analytic Sages operates from Nigeria and serves a global audience. We process personal information in line with the Nigeria Data Protection Act (NDPA), including lawful, transparent, purpose-limited, and secure processing, and we also describe how we handle information for users outside Nigeria.",
    "By using the Analytic Sages platform, you acknowledge that you have read and understood this Privacy Policy.",
  ],
  sections: [
    {
      heading: "1. Information We Collect",
      blocks: [
        {
          type: "p",
          text: "We collect information that you provide directly to us and information generated when you use our platform.",
        },
        { type: "h3", text: "Account information" },
        { type: "p", text: "When you create an account, we may collect:" },
        {
          type: "ul",
          items: [
            "Full name",
            "Email address",
            "Phone number, where required",
            "Password or authentication information",
            "Profile information you choose to provide",
            "Account preferences",
          ],
        },
        {
          type: "p",
          text: "If you use Google or another supported authentication provider, we may receive information associated with that account, such as your name, email address, and profile information permitted by that provider.",
        },
        { type: "h3", text: "Learning information" },
        {
          type: "p",
          text: "When you participate in our courses or programs, we may collect information such as:",
        },
        {
          type: "ul",
          items: [
            "Courses and cohorts you enroll in",
            "Course progress",
            "Lessons completed",
            "Assignment submissions",
            "Assessment results",
            "Attendance",
            "Classroom participation",
            "Certificates or completion records, if and when those features are available",
            "Learning activity and engagement",
          ],
        },
        {
          type: "p",
          text: "This information is used primarily to provide and improve your learning experience.",
        },
        { type: "h3", text: "Payment information" },
        {
          type: "p",
          text: "When you purchase a course or program, payments may be processed through third-party payment providers.",
        },
        { type: "p", text: "We may receive information such as:" },
        {
          type: "ul",
          items: [
            "Payment status",
            "Transaction reference",
            "Amount paid",
            "Currency",
            "Course or program purchased",
            "Payment date",
          ],
        },
        {
          type: "p",
          text: "We do not store your complete credit or debit card details or cryptocurrency wallet private keys on our platform. Payment information is processed by the relevant payment provider according to its own privacy policy and terms.",
        },
        { type: "h3", text: "Communications" },
        {
          type: "p",
          text: "If you contact us, we may collect information contained in your communication, including your name, email address, and the contents of your message.",
        },
      ],
    },
    {
      heading: "2. Information Collected Automatically",
      blocks: [
        {
          type: "p",
          text: "When you use our website, certain technical and usage information may be collected automatically. This may include:",
        },
        {
          type: "ul",
          items: [
            "IP address",
            "Browser type",
            "Device type",
            "Operating system",
            "Pages visited",
            "Approximate location derived from technical information",
            "Referring website",
            "Date and time of visits",
            "Platform interactions",
            "General usage and performance information",
          ],
        },
        {
          type: "p",
          text: "We may use this information to understand how people use our platform, improve performance, maintain security, and measure the effectiveness of our services. We aim to collect only information that is reasonably necessary for these purposes.",
        },
      ],
    },
    {
      heading: "3. How We Use Your Information",
      blocks: [
        { type: "p", text: "We may use personal information to:" },
        {
          type: "ul",
          items: [
            "Create and manage your account",
            "Provide access to courses and programs",
            "Process enrollments and payments",
            "Deliver live and self-paced learning",
            "Track course progress",
            "Record attendance",
            "Manage assignments and assessments",
            "Provide feedback and support",
            "Communicate with you about your account or enrollment",
            "Send important service notifications",
            "Improve our courses and platform",
            "Understand platform usage and learning engagement",
            "Maintain security and prevent fraud or abuse",
            "Manage instructors, staff, authors, and other platform users",
            "Publish approved research or educational content where you have provided the necessary information or permission",
            "Comply with applicable legal and regulatory requirements",
          ],
        },
        {
          type: "p",
          text: "We will not use your personal information for purposes that are incompatible with the purpose for which it was collected without an appropriate legal basis.",
        },
      ],
    },
    {
      heading: "4. Learning and Activity Data",
      blocks: [
        {
          type: "p",
          text: "Analytic Sages may collect learning activity to help students and instructors understand progress and engagement. For example, the platform may record:",
        },
        {
          type: "ul",
          items: [
            "When a lesson is started or completed",
            "Course progress",
            "Assignment submission status",
            "Attendance at live sessions",
            "Recent learning activity",
            "Course completion",
          ],
        },
        {
          type: "p",
          text: "Instructors may be provided with learning-related information about students enrolled in their assigned cohorts where necessary to support teaching and student success. Instructors and staff should only have access to information necessary for their role.",
        },
        {
          type: "p",
          text: "We do not intend for instructors to have unrestricted access to students' private account, payment, authentication, or other unrelated personal information.",
        },
      ],
    },
    {
      heading: "5. Platform Analytics",
      blocks: [
        {
          type: "p",
          text: "We may use aggregated or appropriately limited information to understand how our platform is being used. This may include:",
        },
        {
          type: "ul",
          items: [
            "Website visits",
            "Course views",
            "Course enrollments",
            "Course completion",
            "Learning engagement",
            "Platform activity",
            "General traffic patterns",
          ],
        },
        {
          type: "p",
          text: "Where possible, analytics are presented in aggregate and are not intended to expose unnecessary personal information.",
        },
      ],
    },
    {
      heading: "6. Cookies and Similar Technologies",
      blocks: [
        { type: "p", text: "We may use cookies and similar technologies to:" },
        {
          type: "ul",
          items: [
            "Keep you signed in",
            "Maintain essential platform functionality",
            "Remember preferences",
            "Improve website performance",
            "Understand how visitors use the website",
            "Support analytics and security",
          ],
        },
        {
          type: "p",
          text: "Website traffic measurement on analyticsages.io uses Plausible Analytics, which is designed not to use advertising cookies or collect personal information for ads. Sign-in, payments, classroom, and chat features may still use cookies or similar technologies that those services need in order to work.",
        },
        {
          type: "p",
          text: "Some cookies may be provided by third-party services integrated into our platform. You may control cookies through your browser settings. Some essential functionality may not work properly if certain cookies are disabled.",
        },
        {
          type: "p",
          text: "Where required by applicable law, we will provide appropriate cookie choices or consent mechanisms.",
        },
      ],
    },
    {
      heading: "7. Third-Party Services",
      blocks: [
        {
          type: "p",
          text: "Analytic Sages relies on selected third-party providers to operate and improve the platform. Depending on the services you use, these may include providers for:",
        },
        {
          type: "ul",
          items: [
            "Cloud hosting and infrastructure",
            "Authentication",
            "Video delivery",
            "Live classrooms",
            "Payment processing",
            "Email delivery",
            "Analytics",
            "Database and application infrastructure",
          ],
        },
        {
          type: "p",
          text: "Examples may include Google, Vercel, Render, RealtimeKit, Bunny Stream, Paystack, NOWPayments, YouTube, Plausible Analytics, and other service providers used by the platform.",
        },
        {
          type: "p",
          text: "These providers may process information according to their own terms and privacy policies. We seek to use reputable providers and only provide third parties with access to information reasonably necessary for them to perform their services.",
        },
      ],
    },
    {
      heading: "8. Payments",
      blocks: [
        {
          type: "p",
          text: "Payments for Analytic Sages courses and programs may be processed by third-party payment providers. Depending on the payment method you choose, this may include card or bank transfer processing, or cryptocurrency payment processing.",
        },
        { type: "p", text: "We do not request or store:" },
        {
          type: "ul",
          items: [
            "Your card PIN",
            "Your card security credentials beyond what is required by the payment processor",
            "Your cryptocurrency wallet private keys",
            "Your exchange account password",
          ],
        },
        {
          type: "p",
          text: "Payment providers may collect and process payment information directly.",
        },
      ],
    },
    {
      heading: "9. Video and Live Learning",
      blocks: [
        {
          type: "p",
          text: "Our platform may contain recorded videos and live learning sessions. Recorded content may be delivered through third-party video platforms. Live classes may be delivered through third-party realtime communication infrastructure.",
        },
        {
          type: "p",
          text: "Participation in a live session may generate technical information such as:",
        },
        {
          type: "ul",
          items: [
            "Joining and leaving times",
            "Session attendance",
            "Connection information",
            "Participation duration",
          ],
        },
        {
          type: "p",
          text: "Where applicable, additional information about recordings or session participation will be communicated to participants.",
        },
      ],
    },
    {
      heading: "10. Research Authors and Contributors",
      blocks: [
        {
          type: "p",
          text: "Analytic Sages may allow approved contributors to submit educational articles, research, tutorials, analyses, or other content. Authors may create contributor accounts and submit content for editorial review.",
        },
        {
          type: "p",
          text: "We may publish approved content together with information such as:",
        },
        {
          type: "ul",
          items: [
            "Author name",
            "Professional title or biography",
            "Profile image",
            "Affiliation",
            "Research interests",
          ],
        },
        {
          type: "p",
          text: "Authors should only submit personal information that they are comfortable having published publicly.",
        },
      ],
    },
    {
      heading: "11. How We Share Information",
      blocks: [
        { type: "p", text: "We do not sell your personal information." },
        { type: "p", text: "We may share limited information with:" },
        { type: "h3", text: "Service providers" },
        {
          type: "p",
          text: "Companies that help us operate our platform, including hosting, authentication, payment, email, video, analytics, and infrastructure providers.",
        },
        { type: "h3", text: "Instructors and authorized staff" },
        {
          type: "p",
          text: "Information necessary for instructors and authorized staff to perform their responsibilities.",
        },
        { type: "h3", text: "Legal and regulatory authorities" },
        {
          type: "p",
          text: "Where disclosure is required by applicable law, regulation, court order, or lawful governmental request.",
        },
        { type: "h3", text: "Business transactions" },
        {
          type: "p",
          text: "If Analytic Sages is involved in a merger, acquisition, restructuring, financing, sale of assets, or similar transaction, relevant information may be transferred as part of that transaction subject to applicable law.",
        },
      ],
    },
    {
      heading: "12. International Data Transfers",
      blocks: [
        {
          type: "p",
          text: "Because Analytic Sages serves a global audience and uses technology providers operating in different countries, your information may be processed or stored outside Nigeria or your country of residence.",
        },
        {
          type: "p",
          text: "Where personal information is transferred internationally, we seek to use appropriate safeguards and reputable service providers consistent with applicable data protection requirements.",
        },
      ],
    },
    {
      heading: "13. Data Retention",
      blocks: [
        {
          type: "p",
          text: "We retain personal information only for as long as reasonably necessary for the purposes described in this Privacy Policy, including:",
        },
        {
          type: "ul",
          items: [
            "Providing our services",
            "Maintaining your account",
            "Maintaining learning records",
            "Meeting legal and regulatory obligations",
            "Resolving disputes",
            "Preventing fraud and abuse",
            "Maintaining appropriate business records",
          ],
        },
        {
          type: "p",
          text: "When information is no longer required, we may delete, anonymize, or securely dispose of it, subject to applicable legal obligations.",
        },
      ],
    },
    {
      heading: "14. Your Privacy Rights",
      blocks: [
        {
          type: "p",
          text: "Depending on your location and applicable law, you may have rights relating to your personal information. These may include the right to:",
        },
        {
          type: "ul",
          items: [
            "Know how your information is being used",
            "Request access to personal information we hold about you",
            "Request correction of inaccurate information",
            "Request deletion of certain information",
            "Object to certain processing",
            "Restrict certain processing",
            "Withdraw consent where processing is based on consent",
            "Request portability of certain information",
            "Lodge a complaint with an applicable data protection authority",
          ],
        },
        {
          type: "p",
          text: "The Nigeria Data Protection Act recognizes several of these rights, including access, rectification, objection, portability, and the right to be forgotten. Some rights may be subject to legal limitations.",
        },
        {
          type: "p",
          text: "If you are in Nigeria, you may also lodge a complaint with the Nigeria Data Protection Commission (NDPC) where you believe your data protection rights have been infringed.",
        },
      ],
    },
    {
      heading: "15. Account and Data Requests",
      blocks: [
        { type: "p", text: "If you would like to:" },
        {
          type: "ul",
          items: [
            "Update your information",
            "Access your personal information",
            "Request deletion of your account",
            "Withdraw consent",
            "Ask a privacy-related question",
          ],
        },
        {
          type: "p",
          text: "please contact us using the details provided below. We may need to verify your identity before processing certain requests.",
        },
      ],
    },
    {
      heading: "16. Security",
      blocks: [
        {
          type: "p",
          text: "We take reasonable technical and organizational measures to protect personal information against unauthorized access, unauthorized disclosure, loss, misuse, alteration, and destruction.",
        },
        {
          type: "p",
          text: "However, no internet-based service can guarantee absolute security. You are responsible for maintaining the confidentiality of your account credentials and should notify us if you believe your account has been compromised.",
        },
      ],
    },
    {
      heading: "17. Children's Privacy",
      blocks: [
        {
          type: "p",
          text: "Analytic Sages is primarily designed for learners who are legally able to enter into agreements and use our educational services. We do not knowingly collect personal information from children in violation of applicable law.",
        },
        {
          type: "p",
          text: "Where a program is specifically designed for younger learners, we may implement additional consent and safeguarding requirements appropriate to that program.",
        },
      ],
    },
    {
      heading: "18. Third-Party Websites",
      blocks: [
        {
          type: "p",
          text: "Our website may contain links or embedded content from third-party websites and services. Examples may include YouTube, Dune, Google, and other educational or technology platforms.",
        },
        {
          type: "p",
          text: "We are not responsible for the privacy practices, security, or content of third-party websites. We encourage you to review their respective privacy policies before providing them with personal information.",
        },
      ],
    },
    {
      heading: "19. Changes to This Privacy Policy",
      blocks: [
        {
          type: "p",
          text: "We may update this Privacy Policy from time to time as our platform, services, technology, or legal obligations change.",
        },
        {
          type: "p",
          text: "When we make significant changes, we may provide notice through the website or other appropriate communication channels. The Last Updated date at the top of this page indicates when the policy was most recently revised.",
        },
      ],
    },
    {
      heading: "20. Contact Us",
      blocks: [
        {
          type: "p",
          text: "If you have questions about this Privacy Policy or how Analytic Sages handles personal information, contact Analytic Sages at analyticsages.io or by email using the address shown at the bottom of this page.",
        },
      ],
    },
  ],
};

export const termsOfUse: LegalDocumentContent = {
  title: "Terms of Use",
  slug: "/terms",
  updated: LEGAL_UPDATED,
  description:
    "Terms that govern your use of the Analytic Sages website, courses, classroom, and related services.",
  intro: [
    "Welcome to Analytic Sages.",
    'These Terms of Use ("Terms") govern your access to and use of the Analytic Sages website, learning platform, courses, programs, classroom services, community features, research publications, and related services.',
    "By accessing or using our platform, you agree to these Terms. If you do not agree with these Terms, please do not use the platform.",
  ],
  sections: [
    {
      heading: "1. About Analytic Sages",
      blocks: [
        {
          type: "p",
          text: "Analytic Sages provides technology-focused education and learning experiences, including instructor-led training, self-paced courses, educational resources, research, and community activities.",
        },
        {
          type: "p",
          text: "Our areas of education may include data, artificial intelligence, quantitative finance, blockchain, software engineering, and other emerging technologies.",
        },
      ],
    },
    {
      heading: "2. Accounts",
      blocks: [
        {
          type: "p",
          text: "Certain features require you to create an account. You agree to:",
        },
        {
          type: "ul",
          items: [
            "Provide accurate information",
            "Keep your account information current",
            "Protect your login credentials",
            "Not share your account with another person",
            "Notify us of unauthorized access",
          ],
        },
        {
          type: "p",
          text: "You are responsible for activity carried out through your account unless caused by circumstances outside your reasonable control.",
        },
      ],
    },
    {
      heading: "3. Courses and Programs",
      blocks: [
        { type: "p", text: "Analytic Sages may offer:" },
        {
          type: "ul",
          items: [
            "Free courses",
            "Paid self-paced courses",
            "Instructor-led cohorts",
            "Workshops",
            "Mentorship",
            "Other educational programs",
          ],
        },
        {
          type: "p",
          text: "Specific program pages may contain additional information about duration, schedules, fees, requirements, refund terms, and other conditions. Those terms form part of your agreement for that particular program.",
        },
      ],
    },
    {
      heading: "4. Educational Content",
      blocks: [
        {
          type: "p",
          text: "Our courses and materials are provided for educational purposes. Completing a course or program does not guarantee:",
        },
        {
          type: "ul",
          items: [
            "Employment",
            "Promotion",
            "Income",
            "Investment returns",
            "Business success",
            "Professional certification",
            "Any particular career outcome",
          ],
        },
        {
          type: "p",
          text: "Educational results depend on many factors, including individual effort, experience, and circumstances.",
        },
      ],
    },
    {
      heading: "5. Intellectual Property",
      blocks: [
        {
          type: "p",
          text: "Unless otherwise stated, Analytic Sages owns or has the necessary rights to the content we publish on the platform, including course materials, written content, videos produced by Analytic Sages, graphics, branding, website design, software, and educational resources.",
        },
        {
          type: "p",
          text: "You may use course materials for your personal educational purposes. You may not reproduce, redistribute, resell, publicly republish, or commercially exploit our proprietary course materials without permission.",
        },
      ],
    },
    {
      heading: "6. YouTube and Third-Party Content",
      blocks: [
        {
          type: "p",
          text: "Some educational content may be delivered through third-party platforms such as YouTube. Your use of third-party services is also subject to their own terms and policies.",
        },
      ],
    },
    {
      heading: "7. Assignments and Student Work",
      blocks: [
        {
          type: "p",
          text: "When you submit assignments, projects, or other work through the platform, you retain your rights in your original work unless otherwise agreed.",
        },
        {
          type: "p",
          text: "You grant Analytic Sages the limited rights necessary to store, process, review, and display the submission for the purpose of providing the educational service. We will not publicly publish identifiable student work as promotional material without appropriate permission.",
        },
      ],
    },
    {
      heading: "8. Research and Author Contributions",
      blocks: [
        {
          type: "p",
          text: "Authors and contributors may submit research, articles, tutorials, and other content. Submitting content does not guarantee publication. Analytic Sages may review, edit, reject, or request changes to submissions.",
        },
        { type: "p", text: "Authors are responsible for ensuring that submitted content:" },
        {
          type: "ul",
          items: [
            "Is substantially their own work",
            "Does not infringe third-party rights",
            "Does not contain unlawful material",
            "Properly attributes sources",
            "Does not intentionally misrepresent research or data",
          ],
        },
      ],
    },
    {
      heading: "9. Prohibited Activities",
      blocks: [
        { type: "p", text: "You must not use the platform to:" },
        {
          type: "ul",
          items: [
            "Break applicable laws",
            "Attack or compromise the platform",
            "Attempt unauthorized access",
            "Upload malware",
            "Impersonate another person",
            "Abuse other users",
            "Harass instructors, students, staff, or contributors",
            "Scrape or systematically copy protected platform content",
            "Circumvent access controls",
            "Share paid course access without authorization",
            "Use the platform for fraudulent activities",
          ],
        },
      ],
    },
    {
      heading: "10. Payments",
      blocks: [
        {
          type: "p",
          text: "Paid programs must be paid for through the payment methods made available by Analytic Sages.",
        },
        {
          type: "p",
          text: "Prices, currencies, taxes where applicable, payment schedules, and refund conditions may vary by program. Any specific refund or cancellation policy displayed during purchase will apply to that transaction.",
        },
      ],
    },
    {
      heading: "11. Live Classes",
      blocks: [
        {
          type: "p",
          text: "Instructor-led programs may use third-party live communication services. Students are expected to participate respectfully and comply with classroom rules.",
        },
        {
          type: "p",
          text: "We reserve the right to remove participants from a session or program where necessary because of serious misconduct, abuse, disruption, or security concerns.",
        },
      ],
    },
    {
      heading: "12. Platform Availability",
      blocks: [
        {
          type: "p",
          text: "We work to keep Analytic Sages available and reliable, but we do not guarantee uninterrupted access. The platform may occasionally be unavailable because of:",
        },
        {
          type: "ul",
          items: [
            "Maintenance",
            "Technical problems",
            "Third-party service outages",
            "Security incidents",
            "Events outside our reasonable control",
          ],
        },
      ],
    },
    {
      heading: "13. Account Suspension",
      blocks: [
        {
          type: "p",
          text: "We may suspend or terminate an account where reasonably necessary, including where a user:",
        },
        {
          type: "ul",
          items: [
            "Violates these Terms",
            "Attempts to compromise the platform",
            "Engages in fraud",
            "Abuses other users",
            "Shares unauthorized paid content",
            "Creates a security risk",
          ],
        },
        {
          type: "p",
          text: "Where appropriate, we may provide notice before taking action.",
        },
      ],
    },
    {
      heading: "14. Third-Party Services",
      blocks: [
        {
          type: "p",
          text: "The platform may integrate with third-party services including payment providers, authentication providers, video platforms, cloud infrastructure providers, analytics services, and other technology providers. We are not responsible for services that are independently operated by third parties.",
        },
      ],
    },
    {
      heading: "15. Disclaimer",
      blocks: [
        {
          type: "p",
          text: 'The platform and educational materials are provided on an "as available" basis. While we make reasonable efforts to provide accurate and useful educational material, we do not guarantee that all information will always be complete, current, error-free, or suitable for every purpose.',
        },
        {
          type: "p",
          text: "Blockchain, financial, technical, and other educational content should not be interpreted as personalized financial, legal, investment, or professional advice.",
        },
      ],
    },
    {
      heading: "16. Limitation of Liability",
      blocks: [
        {
          type: "p",
          text: "To the extent permitted by applicable law, Analytic Sages will not be responsible for indirect, incidental, consequential, or unforeseeable losses arising from use of the platform.",
        },
        {
          type: "p",
          text: "Nothing in these Terms excludes or limits liability that cannot legally be excluded or limited.",
        },
      ],
    },
    {
      heading: "17. Changes to These Terms",
      blocks: [
        {
          type: "p",
          text: "We may update these Terms as the platform and services evolve. When significant changes are made, we may provide appropriate notice.",
        },
        {
          type: "p",
          text: "Continued use of the platform after the updated Terms become effective constitutes acceptance of the updated Terms, subject to applicable law.",
        },
      ],
    },
    {
      heading: "18. Governing Law",
      blocks: [
        {
          type: "p",
          text: "These Terms are governed by the laws of the Federal Republic of Nigeria, subject to any mandatory rights or protections applicable to users in their jurisdiction.",
        },
      ],
    },
    {
      heading: "19. Contact",
      blocks: [
        {
          type: "p",
          text: "Questions about these Terms can be directed to Analytic Sages at analyticsages.io or by email using the address shown at the bottom of this page.",
        },
      ],
    },
  ],
};
